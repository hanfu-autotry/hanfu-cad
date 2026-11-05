# -*- coding: utf-8 -*-
"""极简 SVG 预览 / 手工编辑：把脚本产出的 SVG 直接画到 tkinter Canvas。

为什么不用「转 PNG 再贴图」：那既慢又糊，缩放看不清线条，也没法选中单个组件。
这里直接解析 SVG（只用 M/L/C/Q/Z 与 g/path/line/circle/rect/text），画成 Canvas 元素。

坐标：SVG 用户单位 = mm，SVG 的 y 轴向下；画布也按 y 向下映射（不翻转）。
编辑能力（壳里的"排料层"，不碰几何）：
  · 拖动组件（裁片轮廓 + 邻近标注一起走）；空白处拖动＝平移画布
  · 新建组件（矩形占位片）
  · Ctrl+C / Ctrl+V 复制粘贴组件
  · 重置布局
"""
import copy as _copy
import html
import math
import re
import tkinter as tk
import xml.etree.ElementTree as ET

HT = "{http://www.w3.org/2000/svg}"
EDIT_LAYER = "手工"


def _color(v, default="#111111"):
    if not v or v in ("none",):
        return default if v != "none" else None
    v = v.strip()
    if v.startswith("#"):
        return v
    named = {"white": "#ffffff", "black": "#000000", "red": "#d33", "blue": "#36c",
             "green": "#196", "gray": "#888888", "grey": "#888888", "orange": "#e08020"}
    return named.get(v.lower(), default)


def _dash(st):
    raw = (st.get("dash") or "").strip()
    if not raw:
        return None
    try:
        vals = [float(v) for v in raw.replace(",", " ").split()]
    except ValueError:
        return None
    return tuple(max(1, int(v)) for v in vals) or None


def _poly_points(polys):
    return [p for poly in polys for p in poly]


def _bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _item_anchor(kind, data):
    """组件归属用的锚点（SVG 坐标）。"""
    try:
        if kind == "path":
            pts = _poly_points(data)
            if not pts:
                return None
            x0, y0, x1, y1 = _bbox(pts)
            return (x0 + x1) / 2.0, (y0 + y1) / 2.0
        if kind == "line":
            return (data[0][0] + data[1][0]) / 2.0, (data[0][1] + data[1][1]) / 2.0
        if kind == "rect":
            x, y, w, h = data
            return x + w / 2.0, y + h / 2.0
        if kind == "ellipse":
            return data[0], data[1]
        if kind == "text":
            return data[0], data[1]
    except Exception:
        pass
    return None


class SvgDoc:
    """解析后的显示列表。"""

    def __init__(self, svg_text):
        root = ET.fromstring(svg_text)
        vb = root.get("viewBox")
        if vb:
            self.vb = [float(v) for v in vb.split()]
        else:
            self.vb = [0, 0, float(root.get("width", "0").replace("mm", "") or 0),
                       float(root.get("height", "0").replace("mm", "") or 0)]
        self.items = []          # (layer, kind, data, style, id)
        self.layer_names = []
        self._parse(root, "未命名", {"stroke": "#111111", "fill": "none", "sw": 1.0,
                                     "fs": 12.0, "dash": None, "opacity": 1.0})
        for it in self.items:
            if it[0] not in self.layer_names:
                self.layer_names.append(it[0])

    # ---------- 解析 ----------
    _STYLE_MAP = (("stroke", "stroke"), ("fill", "fill"), ("stroke-width", "sw"),
                  ("font-size", "fs"), ("opacity", "opacity"))

    @classmethod
    def _style(cls, el, style):
        st = dict(style)
        for k, target in cls._STYLE_MAP:
            if el.get(k) is not None:
                st[target] = el.get(k)
        if el.get("stroke-dasharray"):
            st["dash"] = el.get("stroke-dasharray")
        return st

    def _parse(self, el, layer, style):
        for ch in el:
            tag = ch.tag.replace(HT, "")
            if tag == "g":
                lid = ch.get("id") or layer or "未命名组"
                self._parse(ch, lid, self._style(ch, style))
            elif tag == "path":
                d = ch.get("d") or ""
                if d.strip():
                    st = self._style(ch, style)
                    st["_d"] = d
                    for k in ("marker-end", "marker-start"):
                        if ch.get(k):
                            st["_" + k.replace("-", "_")] = ch.get(k)
                    self.items.append((layer, "path", _path_to_polys(d), st, ch.get("id")))
            elif tag == "line":
                self.items.append((layer, "line",
                                   [(float(ch.get("x1")), float(ch.get("y1"))),
                                    (float(ch.get("x2")), float(ch.get("y2")))],
                                   self._style(ch, style), ch.get("id")))
            elif tag in ("circle", "ellipse"):
                self.items.append((layer, "ellipse",
                                   (float(ch.get("cx", 0)), float(ch.get("cy", 0)),
                                    float(ch.get("r", 0))),
                                   self._style(ch, style), ch.get("id")))
            elif tag == "rect":
                try:
                    x, y = float(ch.get("x", 0)), float(ch.get("y", 0))
                    w, h = float(ch.get("width", 0)), float(ch.get("height", 0))
                except ValueError:
                    continue
                self.items.append((layer, "rect", (x, y, w, h),
                                   self._style(ch, style), ch.get("id")))
            elif tag == "text":
                try:
                    x, y = float(ch.get("x", 0)), float(ch.get("y", 0))
                except ValueError:
                    continue
                st = self._style(ch, style)
                for k in ("font-family", "text-anchor", "font-weight"):
                    if ch.get(k) is not None:
                        st[k] = ch.get(k)
                m = re.search(r"rotate\(\s*(-?[\d.]+)", ch.get("transform") or "")
                st["_rot"] = float(m.group(1)) if m else 0.0
                self.items.append((layer, "text", (x, y, ch.text or ""), st, ch.get("id")))

    def components(self):
        """组件名集合：来自 path 的 id（"<片名>_ot" 形式）。"""
        names = []
        for it in self.items:
            i = it[4]
            if i and i.endswith("_ot"):
                n = i[:-3]
                if n not in names:
                    names.append(n)
        return names


def _path_to_polys(d, n=22):
    """M/L/C/Q/Z → 折线集合（每个子路径一条）；保持 SVG 的 y 向下。"""
    toks = re.findall(r"[MLCQZmlcqz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    polys, cur, pt, i = [], [], None, 0
    cmd = None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t.upper()
            i += 1
            if cmd == "Z":
                if cur:
                    if cur[0] != cur[-1]:
                        cur.append(cur[0])
                    polys.append(cur)
                    cur = []
                pt = None
                continue
        if cmd is None:
            i += 1
            continue
        if cmd in ("M", "L"):
            x, y = float(toks[i]), float(toks[i + 1])
            i += 2
            if cmd == "M":
                if cur:
                    polys.append(cur)
                cur = [(x, y)]
            else:
                cur.append((x, y))
            pt = (x, y)
        elif cmd == "C":
            p1 = (float(toks[i]), float(toks[i + 1]))
            p2 = (float(toks[i + 2]), float(toks[i + 3]))
            p3 = (float(toks[i + 4]), float(toks[i + 5]))
            i += 6
            if pt:
                cur.extend(_bez(pt, p1, p2, p3, n))
            pt = p3
        elif cmd == "Q":
            c1 = (float(toks[i]), float(toks[i + 1]))
            p2 = (float(toks[i + 2]), float(toks[i + 3]))
            i += 4
            if pt:
                cur.extend(_quad(pt, c1, p2, n))
            pt = p2
        else:
            i += 1
    if cur:
        polys.append(cur)
    return polys


def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                    mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]))
    return out


def _quad(p0, c1, p2, n):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt * mt * p0[0] + 2 * mt * t * c1[0] + t * t * p2[0],
                    mt * mt * p0[1] + 2 * mt * t * c1[1] + t * t * p2[1]))
    return out


def _sample_cmds(cmds, n=24):
    """裁片 cmds（局部坐标，y 向上）→ 折线点列。"""
    pts, cur = [], None
    for c in cmds or []:
        k = c[0]
        if k in ("M", "L"):
            cur = tuple(c[1])
            pts.append(cur)
        elif k == "C" and cur:
            p0, p1, p2, p3 = cur, c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n
                mt = 1 - t
                pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
                            + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
                            + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = tuple(p3)
        elif k == "Q" and cur:
            p0, c1, p3 = cur, c[1], c[2]
            for i in range(1, n + 1):
                t = i / n
                pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c1[0] + t * t * p3[0],
                            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c1[1] + t * t * p3[1]))
            cur = tuple(p3)
    return pts


class SvgView(tk.Frame):
    """矢量预览 + 手工排料。API：
    set_svg(text) / fit() / zoom(f) / select(name) / on_pick(cb)
    components() / layer_names() / add_component() / copy_selected() / paste()
    reset_edits() / has_edits() / export_svg()
    """

    BG = "#f7f7f5"

    def __init__(self, master, **kw):
        super().__init__(master, bg=self.BG, **kw)
        self.canvas = tk.Canvas(self, bg=self.BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.doc = None
        self.scale = 1.0
        self.ox = self.oy = 0.0
        self._hit = {}            # canvas item -> 组件名（None = 静态标注）
        self._scene = []          # 渲染项：dict(layer,kind,data,style,id,comp)
        self._external_scene = False  # CAD 协同：按图层当组件，不做裁片归组
        self._comp_items = {}     # 组件名 -> 场景下标
        self._comp_canvas = {}    # 组件名 -> canvas item id
        self._components = []
        self._dx = {}             # 组件名 -> (dx, dy)，单位 mm
        self._added = {}          # 手工组件：name -> {"items": [...], "piece": {...}, "w":.., "h":..}
        self._piece_src = {}      # 片名 -> pieces.json 里的真实裁片定义
        self._clip = None
        self._sel = None
        self._pick_cb = None
        self._scale_cb = None
        self._hidden = set()
        self._drag = None
        self._fitted = False
        self.canvas.bind("<Configure>", self._configure)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Button-4>", lambda e: self._wheel_dir(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self._wheel_dir(e, -1))

    # ---------- 对外 ----------
    def set_svg(self, svg_text):
        try:
            self.doc = SvgDoc(svg_text)
        except Exception:
            self.doc = None
        self._external_scene = False
        self._sel = None
        self._fitted = False
        self._rebuild_scene()
        self.after_idle(self.fit)

    def load_external_svg(self, svg_text):
        """CAD 协同：把外部 SVG 按图层当组件加载（不做裁片归组）。"""
        try:
            self.doc = SvgDoc(svg_text)
        except Exception:
            self.doc = None
            return False
        self._external_scene = True
        self._added = {}
        self._dx = {}
        self._hidden = set()
        self._clip = None
        self._sel = None
        self._piece_src = {}
        self._fitted = False
        self._rebuild_scene()
        self.after_idle(self.fit)
        return True

    def _configure(self, _e=None):
        if self.doc and not self._fitted:
            self.fit()
        else:
            self._redraw()

    def fit(self):
        if not self.doc:
            return
        x0, y0, w, h = self.doc.vb
        cw = max(self.canvas.winfo_width(), 10)
        ch = max(self.canvas.winfo_height(), 10)
        if cw < 60 or ch < 60:
            self._fitted = False
            return
        self._fitted = True
        self.scale = min(cw / max(w, 1), ch / max(h, 1)) * 0.94
        if self._scale_cb:
            try:
                self._scale_cb()
            except Exception:
                pass
        self.ox = (cw - w * self.scale) / 2 - x0 * self.scale
        self.oy = (ch - h * self.scale) / 2 - y0 * self.scale
        self._redraw()

    def zoom(self, f):
        if not self.doc:
            return
        cw = max(self.canvas.winfo_width(), 10)
        ch = max(self.canvas.winfo_height(), 10)
        cx, cy = cw / 2, ch / 2
        wx = (cx - self.ox) / self.scale
        wy = (cy - self.oy) / self.scale
        self.scale *= f
        self.ox = cx - wx * self.scale
        self.oy = cy - wy * self.scale
        self._redraw()

    def set_layer(self, layer, visible):
        if visible:
            self._hidden.discard(layer)
        else:
            self._hidden.add(layer)
        self._redraw()

    def layer_state(self):
        return dict((l, l not in self._hidden) for l in self.layer_names())

    def layer_names(self):
        if self._external_scene:
            names = list(self._components)
        else:
            names = list(self.doc.layer_names) if self.doc else []
        if any(it["layer"] == EDIT_LAYER for it in self._scene):
            names.append(EDIT_LAYER)
        return names

    def components(self):
        return list(self._components)

    def set_piece_source(self, pieces):
        """子程序产出的真实裁片（pieces.json），供排料 DXF 与复制粘贴使用。"""
        self._piece_src = dict((p.get("name"), p) for p in (pieces or []) if p.get("name"))

    def piece_of(self, name):
        """组件对应的真实裁片定义（原片或手工/库组件）。"""
        p = self._piece_src.get(name)
        if p is None:
            p = (self._added.get(name) or {}).get("piece")
        return _copy.deepcopy(p) if p else None

    def library_refs(self):
        out = []
        for name, spec in self._added.items():
            ref = spec.get("ref")
            if ref:
                d = _copy.deepcopy(ref)
                d["component"] = name
                d["kind"] = spec.get("kind") or "piece"
                out.append(d)
        return out

    def detach_component(self, name):
        spec = self._added.get(name)
        if not spec or not spec.get("ref"):
            return False
        spec.pop("ref", None)
        return True

    def _piece_display_items(self, piece, name, kind="piece"):
        """用裁片几何生成预览项（轮廓 + 片名 + 布纹 + 刀口），供跨项目插入。"""
        pts = _sample_cmds(piece.get("cmds") or [])
        if not pts:
            return []
        ox, oy = float(piece.get("ox", 0)), float(piece.get("oy", 0))
        xy = [(x + ox, oy - y) for (x, y) in pts]
        box = piece.get("box")
        if not box:
            xs = [p[0] for p in xy]
            ys = [p[1] for p in xy]
            box = [min(xs), min(ys), max(xs), max(ys)]
        bx0, by0, bx1, by1 = [float(v) for v in box]
        outline_style = {"stroke": "#1a1a1a", "fill": "none", "sw": 2.0, "_d": ""}
        if kind == "block":
            outline_style["dash"] = "18 8"
        out = [dict(kind="path", data=[xy], style=outline_style, id=name + "_ot"),
               dict(kind="text", data=(bx0, by0 - 26.0, name),
                    style={"fill": "#1a1a1a", "fs": 30.0, "text-anchor": "start",
                           "_rot": 0.0}, id=None)]
        gdx, gdy = piece.get("grain") or (0, 1)
        nn = math.hypot(gdx, gdy) or 1.0
        gdx, gdy = gdx / nn, -gdy / nn          # 裁片 y 向上 → SVG y 向下
        cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
        ext = abs((bx1 - bx0) * gdx) + abs((by1 - by0) * gdy)
        length = max(24.0, min(320.0, 0.8 * ext))
        out.append(dict(kind="line",
                        data=[(cx - gdx * length / 2, cy - gdy * length / 2),
                              (cx + gdx * length / 2, cy + gdy * length / 2)],
                        style={"stroke": "#1a1a1a", "sw": 1.4}, id=None))
        for nx, ny in (piece.get("notches") or []):
            X, Y = nx + ox, oy - ny
            out.append(dict(kind="line", data=[(X - 10, Y - 10), (X + 10, Y + 10)],
                            style={"stroke": "#c0392b", "sw": 2.4}, id=None))
            out.append(dict(kind="line", data=[(X - 10, Y + 10), (X + 10, Y - 10)],
                            style={"stroke": "#c0392b", "sw": 2.4}, id=None))
        return out

    def insert_piece(self, piece, label=None, ref=None, kind="piece"):
        """把库组件插入当前排料（默认引用实例，piece 同时留快照）。"""
        base = (label or piece.get("name") or "库组件").strip()
        name = self._unique_name(base + "（库）")
        p = _copy.deepcopy(piece)
        p["name"] = name
        p["qty"] = 1
        items = self._piece_display_items(p, name, kind)
        self._added[name] = dict(items=items, piece=p, kind=kind,
                                 ref=_copy.deepcopy(ref) if ref else None)
        box = p.get("box")
        if not box:
            xy = _sample_cmds(p.get("cmds") or [])
            ox, oy = float(p.get("ox", 0)), float(p.get("oy", 0))
            xs = [x + ox for (x, _) in xy]
            ys = [oy - y for (_, y) in xy]
            box = [min(xs), min(ys), max(xs), max(ys)]
        cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
        vx, vy = self._view_center()
        self._dx[name] = (vx - cx, vy - cy)
        self._rebuild_scene()
        self._sel = name
        self._redraw()
        return name

    def layout_state(self):
        """可保存的排料状态（不含几何；几何仍在子程序里）。"""
        return dict(
            transforms=dict((k, [float(v[0]), float(v[1])]) for k, v in self._dx.items()
                            if abs(v[0]) > 1e-6 or abs(v[1]) > 1e-6),
            added=_copy.deepcopy(self._added),
            hidden=sorted(self._hidden),
        )

    def apply_layout(self, state):
        self._dx = {}
        self._added = {}
        self._clip = None
        self._sel = None
        for k, v in (state.get("transforms") or {}).items():
            try:
                self._dx[k] = (float(v[0]), float(v[1]))
            except (TypeError, ValueError, IndexError):
                pass
        self._added = _copy.deepcopy(state.get("added") or {})
        self._hidden = set(state.get("hidden") or [])
        self._rebuild_scene()
        self._redraw()

    def select(self, name):
        self._sel = name if name in self._components else None
        self._redraw()

    def selected(self):
        return self._sel

    def remove_selected(self):
        """CAD 协同：删除手工副本；原始图层则隐藏（不破坏源图）。"""
        if not self._sel:
            return None
        name = self._sel
        if name in self._added:
            self._added.pop(name, None)
            self._dx.pop(name, None)
            self._sel = None
            self._rebuild_scene()
            self._redraw()
            return "deleted"
        if self._external_scene and name in self._components:
            self._hidden.add(name)
            self._redraw()
            return "hidden"
        return None

    def scene_json(self, include_hidden=False):
        """当前场景 → CAD 导出 JSON（保留图层/样式/位移）。"""
        if not self.doc:
            return dict(units="mm", viewBox=[0, 0, 100, 100],
                        transforms={}, items=[])
        items = []
        for it in self._scene:
            if not include_hidden and it["layer"] in self._hidden:
                continue
            comp = it.get("comp")
            style = dict((k, v) for k, v in (it.get("style") or {}).items()
                         if not str(k).startswith("_d") and not str(k).startswith("_marker"))
            items.append(dict(layer=comp or it.get("layer") or "未命名",
                              comp=comp, kind=it.get("kind"), id=it.get("id"),
                              data=_copy.deepcopy(it.get("data")), style=style))
        transforms = {}
        for k, v in self._dx.items():
            if abs(v[0]) > 1e-9 or abs(v[1]) > 1e-9:
                transforms[k] = [float(v[0]), float(v[1])]
        return dict(units="mm", viewBox=list(self.doc.vb),
                    transforms=transforms, items=items)

    def on_pick(self, cb):
        self._pick_cb = cb

    def on_scale(self, cb):
        self._scale_cb = cb

    def has_edits(self):
        return bool(self._added) or any(abs(d[0]) > 1e-6 or abs(d[1]) > 1e-6
                                        for d in self._dx.values())

    def reset_edits(self):
        self._dx = {}
        self._added = {}
        self._clip = None
        self._sel = None
        self._rebuild_scene()
        self._redraw()

    # ---------- 场景 ----------
    def _rebuild_scene(self):
        self._scene = []
        self._comp_items = {}
        self._comp_canvas = {}
        self._components = []
        if self.doc:
            if self._external_scene:
                vx, vy, vw, vh = self.doc.vb
                for layer, kind, data, st, pid in self.doc.items:
                    if (kind == "rect" and (st.get("fill") or "").lower() in
                            ("#ffffff", "#fff", "white")):
                        x, y, ww, hh = data
                        if abs(x - vx) < 1 and abs(y - vy) < 1 and \
                                abs(ww - vw) < 1 and abs(hh - vh) < 1:
                            continue          # 跳过整页白底
                    comp = layer or "未命名"
                    self._scene.append(dict(layer=layer, kind=kind, data=data,
                                            style=st, id=pid, comp=comp))
                    if comp not in self._components:
                        self._components.append(comp)
            else:
                boxes = {}
                order = []
                for layer, kind, data, st, pid in self.doc.items:
                    if pid and pid.endswith("_ot"):
                        name = pid[:-3]
                        pts = _poly_points(data) if kind == "path" else []
                        if pts:
                            boxes[name] = _bbox(pts)
                            order.append(name)
                for layer, kind, data, st, pid in self.doc.items:
                    comp = None
                    if pid and pid.endswith("_ot"):
                        comp = pid[:-3]
                    elif layer not in ("BLOCK", "SCALE"):
                        comp = self._nearest_comp(kind, data, layer, boxes)
                    self._scene.append(dict(layer=layer, kind=kind, data=data,
                                            style=st, id=pid, comp=comp))
                self._components = order
        for name, spec in self._added.items():
            for raw in spec["items"]:
                self._scene.append(dict(layer=EDIT_LAYER, kind=raw["kind"],
                                        data=_copy.deepcopy(raw["data"]),
                                        style=_copy.deepcopy(raw["style"]),
                                        id=raw.get("id"), comp=name))
            if name not in self._components:
                self._components.append(name)
        for idx, it in enumerate(self._scene):
            if it["comp"]:
                self._comp_items.setdefault(it["comp"], []).append(idx)
        self._dx = dict((k, v) for k, v in self._dx.items() if k in self._components)
        for name in self._components:
            self._dx.setdefault(name, (0.0, 0.0))

    @staticmethod
    def _nearest_comp(kind, data, layer, boxes):
        """把缝线/刀口/尺寸/文字归到最近的裁片框（留 90mm 余量）。"""
        if not boxes:
            return None
        a = _item_anchor(kind, data)
        if a is None:
            return None
        best = None
        for name, (x0, y0, x1, y1) in boxes.items():
            m = max(90.0, 0.08 * max(x1 - x0, y1 - y0))
            ex0, ey0, ex1, ey1 = x0 - m, y0 - m, x1 + m, y1 + m
            if ex0 <= a[0] <= ex1 and ey0 <= a[1] <= ey1:
                area = (ex1 - ex0) * (ey1 - ey0)
                if best is None or area < best[0]:
                    best = (area, name)
        return best[1] if best else None

    def _T(self, x, y, comp=None):
        dx, dy = self._dx.get(comp, (0.0, 0.0)) if comp else (0.0, 0.0)
        return (self.ox + (x + dx) * self.scale, self.oy + (y + dy) * self.scale)

    def _arrowhead(self, poly, at_end, comp, stroke, sw):
        """SVG marker-start/end 的简化箭头：只画两条翼线，够看清方向即可。"""
        tip = poly[-1] if at_end else poly[0]
        prev = poly[-2] if at_end else poly[1]
        dx, dy = tip[0] - prev[0], tip[1] - prev[1]
        n = math.hypot(dx, dy)
        if n < 1e-6:
            return []
        ux, uy = dx / n, dy / n
        size = max(5.0, min(14.0, 20.0 * self.scale))
        half = size * 0.45
        bx, by = tip[0] - ux * size, tip[1] - uy * size
        a = (bx - uy * half, by + ux * half)
        b = (bx + uy * half, by - ux * half)
        pa = self._T(tip[0], tip[1], comp)
        qa = self._T(a[0], a[1], comp)
        qb = self._T(b[0], b[1], comp)
        col = stroke or "#111111"
        width = max(0.8, sw * 0.9)
        return [self.canvas.create_line(pa[0], pa[1], qa[0], qa[1], fill=col, width=width),
                self.canvas.create_line(pa[0], pa[1], qb[0], qb[1], fill=col, width=width)]

    # ---------- 画 ----------
    def _redraw(self):
        c = self.canvas
        c.delete("all")
        self._hit = {}
        self._comp_canvas = {}
        if not self.doc:
            return
        for idx, it in enumerate(self._scene):
            layer, kind, data, st, pid, comp = (it["layer"], it["kind"], it["data"],
                                                it["style"], it["id"], it["comp"])
            if layer in self._hidden:
                continue
            sel = bool(self._sel) and comp == self._sel
            stroke = _color(st.get("stroke"), "#111111")
            fill = _color(st.get("fill"), None) if st.get("fill") != "none" else None
            sw = max(0.6, float(st.get("sw") or 1.0) * self.scale)
            if sel:
                stroke = "#d33"
                sw += 1.6
            dash = _dash(st)
            dash = tuple(max(1, int(v * self.scale)) for v in dash) if dash else None
            made = []
            if kind == "path":
                for poly in data:
                    if len(poly) < 2:
                        continue
                    flat = []
                    for p in poly:
                        flat.extend(self._T(p[0], p[1], comp))
                    made.append(c.create_line(flat, fill=stroke or "#111111", width=sw,
                                              capstyle="round", joinstyle="round",
                                              dash=dash if dash else ()))
                    if st.get("_marker_end"):
                        made.extend(self._arrowhead(poly, True, comp, stroke, sw))
                    if st.get("_marker_start"):
                        made.extend(self._arrowhead(poly, False, comp, stroke, sw))
            elif kind == "line":
                a = self._T(data[0][0], data[0][1], comp)
                b = self._T(data[1][0], data[1][1], comp)
                made.append(c.create_line(a[0], a[1], b[0], b[1], fill=stroke or "#111111",
                                          width=sw, dash=dash if dash else ()))
            elif kind == "rect":
                x, y, ww, hh = data
                p1 = self._T(x, y, comp)
                p2 = self._T(x + ww, y + hh, comp)
                made.append(c.create_rectangle(p1[0], p1[1], p2[0], p2[1],
                                               outline=stroke or "",
                                               width=sw, fill=fill or ""))
            elif kind == "ellipse":
                cx, cy, r = data
                p1 = self._T(cx - r, cy - r, comp)
                p2 = self._T(cx + r, cy + r, comp)
                made.append(c.create_oval(p1[0], p1[1], p2[0], p2[1],
                                          outline=stroke or "", width=sw, fill=fill or ""))
            elif kind == "text":
                x, y, txt = data
                px, py = self._T(x, y, comp)
                fs = max(6.0, float(st.get("fs") or 12.0) * self.scale)
                anchor = {"start": "w", "middle": "center", "end": "e"}.get(
                    st.get("text-anchor"), "w")
                rot = -float(st.get("_rot") or 0.0)
                kw = dict(text=txt, anchor=anchor, fill=_color(st.get("fill"), "#111111"),
                          font=("Microsoft YaHei UI", int(max(6, fs))), angle=rot)
                made.append(c.create_text(px, py, **kw))
            for cid in made:
                self._hit[cid] = comp
                if comp:
                    self._comp_canvas.setdefault(comp, []).append(cid)

    # ---------- 选择 / 拖动 ----------
    def _comp_at(self, x, y):
        for cid in reversed(self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2)):
            comp = self._hit.get(cid)
            if comp:
                return comp
        return None

    def _press(self, e):
        try:
            self.canvas.focus_set()
        except Exception:
            pass
        comp = self._comp_at(e.x, e.y)
        if comp:
            if comp != self._sel:
                self._sel = comp
                self._redraw()
                if self._pick_cb:
                    self._pick_cb(comp)
            self._drag = ("move", comp, e.x, e.y, e.x, e.y, self._dx.get(comp, (0.0, 0.0)))
        else:
            self._sel = None
            self._redraw()
            self._drag = ("pan", e.x, e.y)

    def _motion(self, e):
        if not self._drag:
            return
        if self._drag[0] == "pan":
            dx, dy = e.x - self._drag[1], e.y - self._drag[2]
            if dx or dy:
                self.canvas.move("all", dx, dy)
                self.ox += dx
                self.oy += dy
                self._drag = ("pan", e.x, e.y)
        else:
            _, comp, sx, sy, lx, ly, orig = self._drag
            dx, dy = e.x - lx, e.y - ly
            if dx or dy:
                for cid in self._comp_canvas.get(comp, []):
                    self.canvas.move(cid, dx, dy)
                self._drag = ("move", comp, sx, sy, e.x, e.y, orig)

    def _release(self, _e):
        if self._drag and self._drag[0] == "move":
            _, comp, sx, sy, lx, ly, orig = self._drag
            if abs(lx - sx) > 0.5 or abs(ly - sy) > 0.5:
                self._dx[comp] = (orig[0] + (lx - sx) / self.scale,
                                  orig[1] + (ly - sy) / self.scale)
                self._redraw()
        self._drag = None

    def _wheel(self, e):
        self.zoom(1.15 if e.delta > 0 else 1 / 1.15)

    def _wheel_dir(self, e, d):
        self.zoom(1.15 if d > 0 else 1 / 1.15)

    # ---------- 新建 / 复制 / 粘贴 ----------
    def _unique_name(self, base):
        name = base
        n = 2
        while name in self._components:
            name = "%s %d" % (base, n)
            n += 1
        return name

    def _view_center(self):
        cw = max(self.canvas.winfo_width(), 10)
        ch = max(self.canvas.winfo_height(), 10)
        return (cw / 2 - self.ox) / self.scale, (ch / 2 - self.oy) / self.scale

    def add_component(self, w=420.0, h=300.0, label=None):
        name = self._unique_name(label or "新组件")
        cx, cy = self._view_center()
        x0, y0 = cx - w / 2.0, cy - h / 2.0
        x1, y1 = x0 + w, y0 + h
        raw = [
            dict(kind="path",
                 data=[[(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]],
                 style={"stroke": "#1a1a1a", "fill": "none", "sw": 2.0, "_d": ""},
                 id=name + "_ot"),
            dict(kind="text", data=(x0, y0 - 26.0, name),
                 style={"fill": "#1a1a1a", "fs": 30.0, "text-anchor": "start", "_rot": 0.0},
                 id=None),
        ]
        piece = dict(name=name, qty=1, ox=x0, oy=y1,
                     box=[x0, y0, x1, y1],
                     cmds=[["M", [0, 0]], ["L", [w, 0]], ["L", [w, h]],
                           ["L", [0, h]], ["Z"]],
                     grain=[0, 1], grain_at=None, notches=[])
        self._added[name] = dict(items=raw, piece=piece, w=w, h=h)
        self._rebuild_scene()
        self._sel = name
        self._redraw()
        return name

    def copy_selected(self):
        if not self._sel:
            return None
        items = []
        for idx in self._comp_items.get(self._sel, []):
            it = self._scene[idx]
            items.append(dict(kind=it["kind"], data=_copy.deepcopy(it["data"]),
                              style=_copy.deepcopy(it["style"]), id=it["id"]))
        if not items:
            return None
        self._clip = dict(name=self._sel, items=items,
                          dx=self._dx.get(self._sel, (0.0, 0.0)))
        return self._sel

    def paste(self):
        if not self._clip:
            return None
        src = self._clip["name"]
        name = self._unique_name(src + " 副本")
        items = []
        for raw in self._clip["items"]:
            data = _copy.deepcopy(raw["data"])
            sid = raw.get("id")
            if sid == src + "_ot":
                sid = name + "_ot"
            if raw["kind"] == "text":
                x, y, txt = data
                data = (x, y, txt.replace(src, name))
            items.append(dict(kind=raw["kind"], data=data,
                              style=_copy.deepcopy(raw["style"]), id=sid))
        piece = _copy.deepcopy(self._piece_src.get(src))
        if piece is None:
            piece = _copy.deepcopy((self._added.get(src) or {}).get("piece"))
        if piece:
            piece["name"] = name
            piece["qty"] = 1
        self._added[name] = dict(items=items, piece=piece)
        dx, dy = self._clip.get("dx", (0.0, 0.0))
        self._dx[name] = (dx + 40.0, dy + 40.0)
        self._rebuild_scene()
        self._sel = name
        self._redraw()
        return name

    # ---------- 导出当前布局 ----------
    def export_svg(self, include_hidden=False):
        """把当前画布（含手工移动/新增/复制）序列化为 SVG，单位 mm。"""
        if not self.doc:
            return ""
        x0, y0, w, h = self.doc.vb
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" '
               'viewBox="%g %g %g %g">' % (w, h, x0, y0, w, h),
               '<rect x="%g" y="%g" width="%g" height="%g" fill="#ffffff"/>' % (x0, y0, w, h)]
        groups = {}
        for it in self._scene:
            if not include_hidden and it["layer"] in self._hidden:
                continue
            groups.setdefault(it["comp"], []).append(it)
        static = groups.pop(None, [])
        out.append("<g>")
        out.extend(self._svg_items(static))
        out.append("</g>")
        for comp, items in groups.items():
            dx, dy = self._dx.get(comp, (0.0, 0.0))
            gid = (' id="%s"' % html.escape(str(comp), quote=True)) if comp else ""
            out.append('<g%s transform="translate(%g %g)">' % (gid, dx, dy))
            out.extend(self._svg_items(items))
            out.append("</g>")
        out.append("</svg>")
        return "\n".join(out)

    @staticmethod
    def _svg_items(items):
        out = []
        for it in items:
            kind, data, st = it["kind"], it["data"], it["style"]
            stroke = st.get("stroke")
            fill = st.get("fill")
            common = []
            if stroke:
                common.append('stroke="%s"' % stroke)
            if fill:
                common.append('fill="%s"' % fill)
            if st.get("sw"):
                common.append('stroke-width="%s"' % st["sw"])
            if st.get("dash"):
                common.append('stroke-dasharray="%s"' % st["dash"])
            if st.get("opacity"):
                common.append('opacity="%s"' % st["opacity"])
            a = " ".join(common)
            if kind == "path":
                d = st.get("_d") or ""
                if not d:
                    segs = []
                    for poly in data:
                        if not poly:
                            continue
                        segs.append("M " + " L ".join("%g %g" % p for p in poly) + " Z")
                    d = " ".join(segs)
                out.append('<path d="%s" %s/>' % (d, a))
            elif kind == "line":
                (x1, y1), (x2, y2) = data
                out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (x1, y1, x2, y2, a))
            elif kind == "rect":
                x, y, ww, hh = data
                out.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (x, y, ww, hh, a))
            elif kind == "ellipse":
                cx, cy, r = data
                out.append('<circle cx="%g" cy="%g" r="%g" %s/>' % (cx, cy, r, a))
            elif kind == "text":
                x, y, txt = data
                fs = st.get("fs") or 12
                anchor = st.get("text-anchor")
                rot = float(st.get("_rot") or 0.0)
                extra = ''
                if anchor:
                    extra += ' text-anchor="%s"' % anchor
                if abs(rot) > 1e-6:
                    extra += ' transform="rotate(%g %g %g)"' % (rot, x, y)
                out.append('<text x="%g" y="%g" font-size="%s" fill="%s"%s>%s</text>'
                           % (x, y, fs, st.get("fill") or "#111111", extra,
                              html.escape(txt)))
        return out
