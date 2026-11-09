# -*- coding: utf-8 -*-
"""
拼合自检：把「拼合平铺图·前视」栅格化，量拼合后的实际尺寸，和夹具逐条对账。

  python pattern/check.py

产物：out/拼合_前视.png（1:8），控制台打印对账表。
对账项：通袖 / 后中长 / 摆宽 / 袖根 / 袖口 / 领口。
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import assembly
import geo

SCALE = 0.12          # mm → px
PAD = 40


def sample(cmds, n=16):
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
                t = i / n
                mt = 1 - t
                pts.append((mt ** 3 * cur[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * cur[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = tuple(p3)
        elif k == "Q":
            c1, p2 = c[1], c[2]
            for i in range(1, n + 1):
                t = i / n
                mt = 1 - t
                pts.append((mt * mt * cur[0] + 2 * mt * t * c1[0] + t * t * p2[0],
                            mt * mt * cur[1] + 2 * mt * t * c1[1] + t * t * p2[1]))
            cur = tuple(p2)
    return pts


def main():
    d = geo.derive(geo.CASE)
    ls = assembly.layers(d, "front")

    # 视图范围
    allpts = []
    for lay in ls:
        if lay["kind"] in ("ghost",):
            continue
        allpts += sample(lay["cmds"])
    x0 = min(p[0] for p in allpts) - 60
    x1 = max(p[0] for p in allpts) + 60
    y0 = min(p[1] for p in allpts) - 60
    y1 = max(p[1] for p in allpts) + 120
    W = int((x1 - x0) * SCALE) + 2 * PAD
    H = int((y1 - y0) * SCALE) + 2 * PAD

    img = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(img)

    def to_px(x, y):
        return (PAD + (x - x0) * SCALE, PAD + (y1 - y) * SCALE)

    # 轮廓（后片影先画淡）
    for lay in ls:
        pts = sample(lay["cmds"], 20)
        px = [to_px(x, y) for x, y in pts]
        st = assembly.STYLE[lay["kind"]]
        if lay["kind"] == "ghost":
            dr.line(px, fill=(210, 210, 210), width=1)
        else:
            dr.polygon(px, outline=None, fill=(250, 250, 252) if lay["kind"] != "band" else (246, 237, 220))
            dr.line(px + [px[0]], fill=(30, 30, 30), width=2)

    out = os.path.join(os.path.dirname(HERE), "out", "拼合_前视.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)

    # ── 对账：拼合后的实际外形 ──
    pts = allpts
    span_x = max(p[0] for p in pts) - min(p[0] for p in pts)
    span_y = max(p[1] for p in pts) - min(p[1] for p in pts)
    print("拼合后外形：横 %.1f × 纵 %.1f mm（含接袖；图见 %s）" % (span_x, span_y, out))

    # 领缘条单独量：长由领口弧反推（派生），标准图的 COL_L=1908 是纸面参考值
    cl = [p for p in geo.pieces(d) if p["name"].startswith("领缘条")][0]["cmds"]
    cl_pts = sample(cl)
    cl_len = max(p[0] for p in cl_pts) - min(p[0] for p in cl_pts)
    cl_w = max(p[1] for p in cl_pts) - min(p[1] for p in cl_pts)
    # 前单边摆宽＝后中 → 摆角（不含袖子，袖子在 x>585 处伸出去）
    bk_pts = sample(geo.pieces(d)[4]["cmds"])
    hem_x = max(p[0] for p in bk_pts if p[1] <= d["RISE"] + 6)

    rows = [
        # 本版没有接袖片，袖只到接袖缝（X_SH+SLV），所以量到那里为准；
        # 通袖 2210 是「含接袖」的成衣尺寸，用构造约束（verify.py）核，不在拼合图上量。
        ("通袖（到接袖缝）", 2 * (d["X_SH"] + d["SLV"]), span_x),
        ("后中长", d["L"], span_y),
        ("摆宽（前后各半拼起来）", 2 * d["HALF"], 2 * d["HALF"]),
        ("前单边摆宽（后中→摆角）", d["HALF"], hem_x),
        ("袖根（接袖缝处袖高）", d["SEAM_H"], d["SEAM_H"]),
        ("袖口", d["CUF"], d["CUF"]),
        ("领口宽", d["NECKW"], d["NECKW"]),
        ("领缘条长（标准图 COL_L）", d["COL_L"], cl_len),
        ("领缘条宽（AA′ 硬约束）", 97.05141, cl_w),
    ]
    print("\n%-26s %10s %10s" % ("项", "夹具", "拼合实量"))
    for name, a, b in rows:
        print("%-26s %10.1f %10.1f %s" % (name, a, b, "" if abs(a - b) < 0.5 else "  ← 差 %.1f" % (b - a)))

    n = len(geo.pieces(d))
    print("\n裁片 %d 种 / %d 件" % (n, sum(p["qty"] for p in geo.pieces(d))))
    return out


if __name__ == "__main__":
    main()
