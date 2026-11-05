# -*- coding: utf-8 -*-
"""DXF ↔ SVG/场景 JSON 互转（供 studio 的 CAD 协同窗口使用，依赖 ezdxf）。

用法：
    python dxf_io.py import  in.dxf  out.svg
    python dxf_io.py export  scene.json out.dxf

约定：
  · 输入 DXF 按 $INSUNITS 折算到 mm；无单位时按 mm；
  · 输出 SVG 用 mm、y 向下，图层写成 <g id="图层名">；
  · 场景 JSON 来自 SvgView.scene_json()，坐标是 SVG 用户单位（y 向下），
    导出时翻回 CAD（y 向上，原点左下）。
"""
import json
import html
import math
import os
import sys

try:
    import ezdxf
    from ezdxf import path as ezpath
    from ezdxf.enums import TextEntityAlignment
except Exception as _e:
    print("需要 ezdxf（py=%s, %s: %s）" % (sys.executable, type(_e).__name__, _e),
          file=sys.stderr)
    sys.exit(2)

_UNIT_MM = {0: 1.0, 1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0}


def _aci_hex(aci):
    if aci in (0, 256):
        return "#1a1a1a"
    if aci == 7:
        return "#1a1a1a"
    try:
        r, g, b = ezdxf.colors.aci2rgb(aci)
        return "#%02x%02x%02x" % (r, g, b)
    except Exception:
        return "#1a1a1a"


def _layer_color(doc, name):
    try:
        return _aci_hex(doc.layers.get(name).dxf.color)
    except Exception:
        return "#1a1a1a"


def _ent_color(e, doc, layer):
    try:
        tc = getattr(e.dxf, "true_color", None)
        if tc:
            return "#%06x" % int(tc)
    except Exception:
        pass
    try:
        c = getattr(e.dxf, "color", 256)
        if c in (0, 256):
            return _layer_color(doc, layer)
        return _aci_hex(c)
    except Exception:
        return _layer_color(doc, layer)


def _lineweight(e):
    try:
        lw = getattr(e.dxf, "lineweight", -1)
        if lw and lw > 0:
            return max(0.35, lw / 100.0)
    except Exception:
        pass
    return 0.5


def _flatten(e, dist_mm, scale):
    t = e.dxftype()
    if t == "LINE":
        s, d = e.dxf.start, e.dxf.end
        return [[(s.x * scale, s.y * scale), (d.x * scale, d.y * scale)]], False
    if t in ("LWPOLYLINE", "POLYLINE", "SPLINE", "ARC", "CIRCLE", "ELLIPSE"):
        p = ezpath.make_path(e)
        pts = [(v.x * scale, v.y * scale)
               for v in p.flattening(max(0.05, dist_mm / max(scale, 1e-9)))]
        closed = bool(getattr(e, "closed", False) or getattr(e, "is_closed", False)
                      or t in ("CIRCLE", "ELLIPSE"))
        return [pts], closed
    return [], False


def import_dxf(src, dst):
    doc = ezdxf.readfile(src)
    scale = _UNIT_MM.get(int(getattr(doc, "units", 4) or 4), 1.0)
    msp = doc.modelspace()
    layers = {}
    order = []
    nent = 0

    def put(layer, elem):
        if layer not in layers:
            layers[layer] = []
            order.append(layer)
        layers[layer].append(elem)

    def walk(entities):
        nonlocal nent
        for e in entities:
            t = e.dxftype()
            if t == "INSERT":
                try:
                    walk(e.virtual_entities())
                except Exception:
                    pass
                continue
            layer = e.dxf.get("layer", "0") or "0"
            if t in ("TEXT", "MTEXT"):
                try:
                    ins = e.dxf.insert
                    x, y = ins.x * scale, ins.y * scale
                    h = float(getattr(e.dxf, "height", 2.5) or 2.5) * scale
                    rot = float(getattr(e.dxf, "rotation", 0) or 0)
                    txt = e.dxf.text if t == "TEXT" else (e.plain_text() or "")
                    if not txt:
                        continue
                    col = _ent_color(e, doc, layer)
                    put(layer, '<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" '
                               'stroke="none" text-anchor="start"%s>%s</text>'
                        % (x, y, h, col,
                           (' transform="rotate(%.2f %.2f %.2f)"' % (-rot, x, y)) if rot else "",
                           html.escape(txt)))
                    nent += 1
                except Exception:
                    pass
                continue
            polys, closed = _flatten(e, 0.5, scale)
            if not polys:
                continue
            col = _ent_color(e, doc, layer)
            sw = _lineweight(e)
            for pts in polys:
                if len(pts) < 2:
                    continue
                d = "M " + " L ".join("%.2f %.2f" % p for p in pts)
                if closed and pts[0] != pts[-1]:
                    d += " Z"
                put(layer, '<path d="%s" fill="none" stroke="%s" stroke-width="%.2f"/>'
                    % (d, col, sw))
                nent += 1

    walk(msp)
    if not order:
        raise RuntimeError("DXF 里没有可导入的实体")

    xs, ys = [], []
    for name in order:
        for el in layers[name]:
            for a, b in _numbers(el):
                xs.append(a)
                ys.append(b)
    if not xs:
        raise RuntimeError("无法计算 DXF 范围")
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = max(5.0, 0.02 * max(maxx - minx, maxy - miny))
    W, H = maxx - minx + 2 * pad, maxy - miny + 2 * pad

    def conv(s):
        # 数字变换：x 平移，y 翻到 SVG 向下
        return s

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" '
           'viewBox="0 0 %g %g">' % (W, H, W, H),
           '<rect x="0" y="0" width="%g" height="%g" fill="#ffffff"/>' % (W, H)]
    for name in order:
        col = _layer_color(doc, name)
        out.append('<g id="%s" fill="none" stroke="%s" stroke-width="0.5">'
                   % (html.escape(str(name), quote=True), col))
        for el in layers[name]:
            out.append(_map_y(el, minx, maxy, pad))
        out.append("</g>")
    out.append("</svg>")
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(json.dumps(dict(ok=True, svg=dst, entities=nent, layers=len(order),
                          bbox=[minx, miny, maxx, maxy], unit_scale=scale), ensure_ascii=False))


def _numbers(el):
    """从我们生成的简单 SVG 元素里取数字对，用来算范围。"""
    import re
    if el.startswith("<path"):
        d = re.search(r'd="([^"]*)"', el)
        if not d:
            return []
        toks = re.findall(r"-?\d+\.?\d*", d.group(1))
        vals = [float(x) for x in toks]
        return list(zip(vals[0::2], vals[1::2]))
    if el.startswith("<text"):
        x = float(re.search(r' x="([^"]*)"', el).group(1))
        y = float(re.search(r' y="([^"]*)"', el).group(1))
        return [(x, y)]
    return []


def _map_y(el, minx, maxy, pad):
    """把元素里的坐标从 DXF mm 改为 SVG mm（x 平移、y 翻转）。"""
    import re

    def point(m):
        x, y = float(m.group(1)), float(m.group(2))
        return "%.2f %.2f" % (x - minx + pad, maxy - y + pad)

    if el.startswith("<path"):
        m = re.search(r'd="([^"]*)"', el)
        d = m.group(1)
        out = []
        parts = re.findall(r"[MLZ]|-?\d+\.?\d*", d)
        i = 0
        while i < len(parts):
            t = parts[i]
            if t in ("M", "L"):
                x, y = float(parts[i + 1]), float(parts[i + 2])
                out.append("%s %.2f %.2f" % (t, x - minx + pad, maxy - y + pad))
                i += 3
            elif t == "Z":
                out.append("Z")
                i += 1
            else:
                i += 1
        return el.replace(d, " ".join(out))
    if el.startswith("<text"):
        x = float(re.search(r' x="([^"]*)"', el).group(1))
        y = float(re.search(r' y="([^"]*)"', el).group(1))
        nx, ny = x - minx + pad, maxy - y + pad
        el = re.sub(r' x="[^"]*"', ' x="%.2f"' % nx, el, count=1)
        el = re.sub(r' y="[^"]*"', ' y="%.2f"' % ny, el, count=1)
        el = re.sub(r"rotate\(([-\d.]+) [-\d.]+ [-\d.]+\)",
                    "rotate(\\1 %.2f %.2f)" % (nx, ny), el)
        return el
    return el


def _hex_color(st):
    c = (st or {}).get("stroke") or (st or {}).get("fill") or "#1a1a1a"
    if isinstance(c, str) and c.startswith("#") and len(c) == 7:
        try:
            return int(c[1:], 16)
        except ValueError:
            pass
    return 0x1A1A1A


def _valid_layer(name):
    bad = set('<>/\\":;?*|=,')
    s = "".join("_" if ch in bad else ch for ch in str(name or "0"))
    return s or "0"


def export_dxf(src_json, dst):
    d = json.load(open(src_json, encoding="utf-8"))
    items = d.get("items") or []
    vb = d.get("viewBox") or [0, 0, 100, 100]
    x0, y0, W, H = [float(v) for v in vb]
    tr = d.get("transforms") or {}
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.styles.add("CN", font="simsun.ttc")
    layers = {}
    for it in items:
        layers.setdefault(_valid_layer(it.get("layer")), 0x1A1A1A)
    for name in layers:
        if name not in doc.layers:
            doc.layers.add(name, color=7)
    msp = doc.modelspace()

    def conv(p, comp):
        dx, dy = tr.get(comp, [0, 0])[:2]
        return (float(p[0]) + dx - x0, (y0 + H) - (float(p[1]) + dy))

    n = 0
    for it in items:
        kind = it.get("kind")
        data = it.get("data")
        st = it.get("style") or {}
        layer = _valid_layer(it.get("layer"))
        comp = it.get("comp")
        attribs = {"layer": layer}
        try:
            attribs["true_color"] = _hex_color(st)
        except Exception:
            pass
        try:
            if kind == "path":
                for poly in data or []:
                    if len(poly) < 2:
                        continue
                    pts = [conv(p, comp) for p in poly]
                    close = len(pts) >= 3 and pts[0] == pts[-1]
                    if close:
                        pts = pts[:-1]
                    msp.add_lwpolyline(pts, close=close, dxfattribs=attribs)
                    n += 1
            elif kind == "line":
                a, b = conv(data[0], comp), conv(data[1], comp)
                msp.add_line(a, b, dxfattribs=attribs)
                n += 1
            elif kind == "rect":
                x, y, w, h = data
                pts = [conv(p, comp) for p in
                       ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
                msp.add_lwpolyline(pts, close=True, dxfattribs=attribs)
                n += 1
            elif kind == "ellipse":
                cx, cy, r = data
                msp.add_circle(conv((cx, cy), comp), float(r), dxfattribs=attribs)
                n += 1
            elif kind == "text":
                x, y, text = data
                ox, oy = conv((x, y), comp)
                hgt = float(st.get("fs") or 12.0)
                rot = -float(st.get("_rot") or 0.0)
                e = msp.add_text(text or "", height=hgt,
                                 dxfattribs={"layer": layer, "style": "CN",
                                             "true_color": _hex_color(st)})
                e.set_placement((ox, oy), align=TextEntityAlignment.LEFT)
                if rot:
                    e.dxf.rotation = rot
                n += 1
        except Exception as e:
            print("skip %s: %s" % (kind, e), file=sys.stderr)
    if not n:
        raise RuntimeError("场景里没有可导出的实体")
    doc.saveas(dst)
    print(json.dumps(dict(ok=True, dxf=dst, entities=n, layers=len(layers)), ensure_ascii=False))


def main():
    if len(sys.argv) < 4:
        print("用法：python dxf_io.py import|export <src> <dst>", file=sys.stderr)
        return 2
    mode, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "import":
        import_dxf(src, dst)
    elif mode == "export":
        export_dxf(src, dst)
    else:
        print("未知模式", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
