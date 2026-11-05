# -*- coding: utf-8 -*-
"""手工排料 → CAD DXF（裁片轮廓 / 布纹 / 刀口 / 片名，可选缝份）

用法（由 hanfu-studio 调用，需 ezdxf；缝份需 shapely）：
    python layout_dxf.py 手工排料.pieces.json 手工排料.dxf

输入 JSON 的裁片与各项目 pattern/export_dxf.py 同一口径：
  · cmds 为裁片局部坐标（y 向上），ox/oy 为放到画布上的平移；
  · 画布为 SVG 坐标（y 向下），输出时翻回 CAD（y 向上）。
手工移动/新建/复制已经在上游折进 ox/oy/box，这里不再改摆放。
"""
import json
import math
import os
import sys

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except Exception as _e:
    print("需要 ezdxf（py=%s, %s: %s）" % (sys.executable, type(_e).__name__, _e),
          file=sys.stderr)
    sys.exit(2)

CUT, GRAIN, NOTCH, TEXT, DIM, NET = (
    "CUT_裁剪", "GRAIN_布纹", "NOTCH_刀口", "TEXT_文字", "DIM_标注", "NET_净样")


def sample(cmds, n=40):
    pts, cur = [], None
    for c in cmds:
        k = c[0]
        if k == "M":
            cur = tuple(c[1])
            pts.append(cur)
        elif k == "L":
            cur = tuple(c[1])
            pts.append(cur)
        elif k == "C":
            p0 = cur
            p1, p2, p3 = c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n
                mt = 1 - t
                pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
                            + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
                            + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = tuple(p3)
        elif k == "Q":
            p0 = cur
            c1, p3 = c[1], c[2]
            for i in range(1, n + 1):
                t = i / n
                pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c1[0] + t * t * p3[0],
                            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c1[1] + t * t * p3[1]))
            cur = tuple(p3)
    return pts


def offset_closed(cad, amount):
    """闭合多边形向外偏移（缝份）。失败时返回原样并打印警告。"""
    if amount <= 0:
        return cad
    try:
        from shapely.geometry import Polygon
    except ImportError:
        print("!! 缝份需要 shapely：请用带 shapely 的解释器，或把缝份改为净版", file=sys.stderr)
        sys.exit(3)
    poly = Polygon(cad)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return cad
    buf = poly.buffer(amount, join_style=2, mitre_limit=5.0)
    if buf.is_empty:
        return cad
    if buf.geom_type == "MultiPolygon":
        buf = max(buf.geoms, key=lambda g: g.area)
    return list(buf.exterior.coords)


def main():
    if len(sys.argv) < 3:
        print("用法：python layout_dxf.py <pieces.json> <out.dxf>", file=sys.stderr)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    d = json.load(open(src, encoding="utf-8"))
    pieces = d.get("pieces") or []
    if not pieces:
        print("没有裁片", file=sys.stderr)
        return 2
    W, H = d.get("canvas") or (0, 0)
    if not W or not H:
        W = max(p["box"][2] for p in pieces) + 200
        H = max(p["box"][3] for p in pieces) + 200
    seam = float(d.get("seam_allowance") or 0)
    title = d.get("title") or "手工排料"

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    for name, col in ((CUT, 7), (GRAIN, 8), (NOTCH, 1), (TEXT, 3), (DIM, 4), (NET, 6)):
        doc.layers.add(name, color=col)
    doc.styles.add("CN", font="simsun.ttc")
    msp = doc.modelspace()
    y_min = None

    for p in pieces:
        pts = sample(p["cmds"])
        if not pts:
            continue
        ox, oy = float(p.get("ox", 0)), float(p.get("oy", 0))
        cad = [(x + ox, H + y - oy) for (x, y) in pts]
        cut = offset_closed(cad, seam)
        msp.add_lwpolyline(cut, close=True, dxfattribs={"layer": CUT})
        if seam > 0:
            msp.add_lwpolyline(cad, close=True, dxfattribs={"layer": NET})
        y_min = min(min(y for _, y in cut), y_min) if y_min is not None else min(y for _, y in cut)

        box = p.get("box")
        if not box:
            xs = [x + ox for x, _ in pts]
            ys = [oy - y for _, y in pts]
            box = [min(xs), min(ys), max(xs), max(ys)]
        bx0, by0, bx1, by1 = [float(v) for v in box]

        # 布纹线
        if p.get("grain_at"):
            gx, gy = float(p["grain_at"][0]) + ox, H + float(p["grain_at"][1]) - oy
        else:
            gx, gy = (bx0 + bx1) / 2.0, H - (by0 + by1) / 2.0
        gdx, gdy = p.get("grain") or [0, 1]
        nn = math.hypot(gdx, gdy) or 1.0
        gdx, gdy = gdx / nn, gdy / nn
        # 布纹线长度按裁片在布纹方向上的实际跨度限制，避免窄条上的线跑出片外
        extent = abs((bx1 - bx0) * gdx) + abs((by1 - by0) * gdy)
        length = max(12.0, min(320.0, 0.8 * extent))
        a = (gx - gdx * length / 2, gy - gdy * length / 2)
        b = (gx + gdx * length / 2, gy + gdy * length / 2)
        msp.add_line(a, b, dxfattribs={"layer": GRAIN})
        nx, ny = -gdy, gdx
        for sgn in (+1, -1):
            msp.add_line(b, (b[0] - gdx * 30 + sgn * nx * 12, b[1] - gdy * 30 + sgn * ny * 12),
                         dxfattribs={"layer": GRAIN})

        # 刀口
        for nx_, ny_ in (p.get("notches") or []):
            X, Y = nx_ + ox, H + ny_ - oy
            msp.add_line((X - 10, Y - 10), (X + 10, Y + 10), dxfattribs={"layer": NOTCH})
            msp.add_line((X - 10, Y + 10), (X + 10, Y - 10), dxfattribs={"layer": NOTCH})

        # 片名（放在片上方）
        label = "%s ×%d" % (p.get("name", "裁片"), int(p.get("qty", 1)))
        msp.add_text(label, height=35, dxfattribs={"layer": TEXT, "style": "CN"}
                     ).set_placement((bx0, H - by0 + 16), align=TextEntityAlignment.LEFT)

    if y_min is None:
        print("没有有效轮廓", file=sys.stderr)
        return 2
    y0 = y_min - 120
    msp.add_line((40, y0), (1040, y0), dxfattribs={"layer": DIM})
    for k in range(11):
        hh = 26 if k % 5 == 0 else 14
        msp.add_line((40 + k * 100, y0), (40 + k * 100, y0 + hh), dxfattribs={"layer": DIM})
    mode = ("含缝份 %.0fmm（净样另见 %s 层）" % (seam, NET)) if seam > 0 else "净版（未含缝份）"
    msp.add_text("%s ｜ %s ｜ 单位 mm ｜ 手工排料" % (title, mode),
                 height=35, dxfattribs={"layer": TEXT, "style": "CN"}
                 ).set_placement((40, y0 - 70))
    msp.add_text("100mm 校验标尺", height=28, dxfattribs={"layer": TEXT, "style": "CN"}
                 ).set_placement((40, y0 + 44))

    doc.saveas(dst)
    print(json.dumps(dict(ok=True, pieces=len(pieces), seam=seam, out=dst), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
