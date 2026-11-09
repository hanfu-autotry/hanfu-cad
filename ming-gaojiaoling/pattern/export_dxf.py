# -*- coding: utf-8 -*-
"""pieces.json → DXF（mm，CAD 可直接打开）。需要 ezdxf。"""
import json
import math
import os
import sys

try:
    import ezdxf
except ImportError:
    print("需要 ezdxf")
    sys.exit(2)

CUT, GRAIN, NOTCH, TEXT = "CUT_轮廓", "GRAIN_布纹", "NOTCH_刀口", "TEXT_文字"


def sample(cmds, n=48):
    pts, cur = [], (0.0, 0.0)
    for c in cmds:
        k = c[0]
        if k == "M":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "L":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "C":
            p1, p2, p3 = c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt ** 3 * cur[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * cur[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = tuple(p3)
        elif k == "Q":
            c1, p2 = c[1], c[2]
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt * mt * cur[0] + 2 * mt * t * c1[0] + t * t * p2[0],
                            mt * mt * cur[1] + 2 * mt * t * c1[1] + t * t * p2[1]))
            cur = tuple(p2)
    return pts


def main(src, dst):
    d = json.load(open(src, encoding="utf-8"))
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4          # mm
    doc.layers.add(CUT, color=7)
    doc.layers.add(GRAIN, color=3)
    doc.layers.add(NOTCH, color=1)
    doc.layers.add(TEXT, color=5)
    msp = doc.modelspace()

    for p in d["pieces"]:
        ox, oy = p["ox"], p["oy"]
        pts = [(x + ox, oy - y) for x, y in sample(p["cmds"])]
        if pts and math.dist(pts[0], pts[-1]) > 1e-6:
            pts.append(pts[0])
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": CUT})
        x0, y0, x1, y1 = p["box"]
        msp.add_text("%s ×%d" % (p["name"], p["qty"]),
                     dxfattribs={"layer": TEXT, "height": 40}).set_placement((x0 + 10, y0 + 20))
        # 布纹
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        gx, gy = p["grain"]
        n = math.hypot(gx, gy) or 1.0
        ln = min(max(x1 - x0, 120.0), max(y1 - y0, 120.0)) * 0.5
        msp.add_line((cx - gx / n * ln / 2, cy + gy / n * ln / 2),
                     (cx + gx / n * ln / 2, cy - gy / n * ln / 2), dxfattribs={"layer": GRAIN})
        for nx, ny in p["notches"]:
            px, py = nx + ox, oy - ny
            msp.add_line((px - 10, py - 10), (px + 10, py + 10), dxfattribs={"layer": NOTCH})
            msp.add_line((px - 10, py + 10), (px + 10, py - 10), dxfattribs={"layer": NOTCH})

    doc.saveas(dst)
    print("DXF → %s" % dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
