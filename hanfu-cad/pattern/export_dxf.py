# -*- coding: utf-8 -*-
"""裁片几何（pieces.json）→ DXF（mm，CAD 可直接打开）"""
import json, os, math, sys

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    print("需要 ezdxf：pip install ezdxf")
    sys.exit(2)

CUT, GRAIN, NOTCH, TEXT, DIM = "CUT_轮廓", "GRAIN_布纹", "NOTCH_刀口", "TEXT_文字", "DIM_标注"


def sample(cmds, n=40):
    """M/L/C/Q/Z → 折线点列（服饰坐标，y 向上）"""
    pts, cur = [], None
    for c in cmds:
        k = c[0]
        if k == "M":
            cur = c[1]; pts.append(cur)
        elif k == "L":
            cur = c[1]; pts.append(cur)
        elif k == "C":
            p0 = cur; p1, p2, p3 = c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0],
                            mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]))
            cur = p3
        elif k == "Q":
            p0 = cur; c1, p3 = c[1], c[2]
            for i in range(1, n + 1):
                t = i / n
                pts.append(((1-t)**2*p0[0] + 2*(1-t)*t*c1[0] + t*t*p3[0],
                            (1-t)**2*p0[1] + 2*(1-t)*t*c1[1] + t*t*p3[1]))
            cur = p3
        elif k == "Z":
            pass
    return pts


def svg_to_cad(p, X, Y):
    """SVG 平移坐标 → CAD 坐标（y 翻回向上，原点左下）"""
    ox, oy = p["ox"], p["oy"]
    return X - ox, oy - Y


def build(src_json, out_dxf):
    d = json.load(open(src_json, encoding="utf-8"))
    W, H = d["canvas"]
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4          # 毫米
    doc.header["$MEASUREMENT"] = 1       # 公制
    for name, col in ((CUT, 7), (GRAIN, 8), (NOTCH, 1), (TEXT, 3), (DIM, 4)):
        doc.layers.add(name, color=col)
    # 中文必须走 TrueType，默认 txt.shx 无汉字字形 → 打开是 "??"
    doc.styles.add("CN", font="simsun.ttc")
    msp = doc.modelspace()

    for p in d["pieces"]:
        pts = sample(p["cmds"])
        # SVG 坐标 → CAD：先平移，再把 y 翻到 "H - y"
        cad = [(x + p["ox"], H + y - p["oy"]) for (x, y) in pts]
        msp.add_lwpolyline(cad, close=True, dxfattribs={"layer": CUT})

        # 布纹线
        bx0, by0, bx1, by1 = p["box"]
        if p.get("grain_at"):
            gx_, gy_ = p["grain_at"]
            gX, gY = gx_ + p["ox"], H + gy_ - p["oy"]
        else:
            gX, gY = (bx0 + bx1) / 2, H - (by0 + by1) / 2
        gdx, gdy = p["grain"]
        nn = math.hypot(gdx, gdy) or 1
        gdx, gdy = gdx / nn, gdy / nn
        L = 320.0
        a = (gX - gdx * L / 2, gY - gdy * L / 2)
        b = (gX + gdx * L / 2, gY + gdy * L / 2)
        msp.add_line(a, b, dxfattribs={"layer": GRAIN})
        nx, ny = -gdy, gdx
        for sgn in (+1, -1):
            msp.add_line(b, (b[0] - gdx * 30 + sgn * nx * 12, b[1] - gdy * 30 + sgn * ny * 12),
                         dxfattribs={"layer": GRAIN})

        # 刀口
        for nx, ny in p["notches"]:
            X, Y = nx + p["ox"], H - (-ny + p["oy"])
            msp.add_line((X - 10, Y - 10), (X + 10, Y + 10), dxfattribs={"layer": NOTCH})
            msp.add_line((X - 10, Y + 10), (X + 10, Y - 10), dxfattribs={"layer": NOTCH})

        # 片名
        msp.add_text("%s ×%d" % (p["name"], p["qty"]),
                     height=35,
                     dxfattribs={"layer": TEXT, "style": "CN"}).set_placement(
            (bx0, H - by0 + 14), align=TextEntityAlignment.LEFT)

    # 100mm 校验标尺
    x0, y0 = 40, -60
    msp.add_line((x0, y0), (x0 + 1000, y0), dxfattribs={"layer": DIM})
    for k in range(11):
        hh = 26 if k % 5 == 0 else 14
        msp.add_line((x0 + k * 100, y0), (x0 + k * 100, y0 + hh), dxfattribs={"layer": DIM})
    msp.add_text("100mm 校验标尺 · 单位 mm · 净版（未含缝份）· 对穿交半臂 右衽",
                 height=35, dxfattribs={"layer": TEXT, "style": "CN"}).set_placement((x0, y0 - 70))

    doc.saveas(out_dxf)
    return len(d["pieces"]), (W, H)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "对穿交_右衽_裁片图.pieces.json"
    out = sys.argv[2] if len(sys.argv) > 2 else src.replace(".pieces.json", ".dxf")
    n, size = build(src, out)
    print("DXF 已写出：%s（%d 个裁片，画布 %.0f×%.0f mm）" % (out, n, size[0], size[1]))
