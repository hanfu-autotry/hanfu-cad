# -*- coding: utf-8 -*-
"""叠图 · 古制（V1 ／ V1B）× 厂商基准默认直领对襟 —— **带 100mm 网格，只做目测**

  · 对齐方式：**下摆齐（y = 0）、前中重合（x = 0）**，mm，同一比例，不加缩放；
  · 网格：**100mm 一格，500mm 一格加重**，原点 x=0 前中 ／ y=0 下摆；坐标数字每 200mm 一个；
  · 蓝＝默认口径 直领对襟（`../hanfu-zhidui/pattern/flat.py` 的几何，直接取它的变量，不另算）；
  · 红＝古制（`build.py` 的 V1 ／ `build_v1b.py` 的 V1B，常数照搬）；
  · 只画外轮廓 ＋ 领条／开领那几根线；浅色填充只为分辨领条区，不是面积统计。

    python pattern/overlay_zhidui.py                        # V1（无网格，老图）
    python pattern/overlay_zhidui.py --variant v1b --grid    # V1B ＋ 网格
    python pattern/overlay_zhidui.py --variant v1b --grid --cell 50

**这张图不参与出图口径**，是看稿；要数值看两个项目各自的 README（hanfu-shenyi / hanfu-zhidui）。
"""
import argparse
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # hanfu/
ZD = os.path.join(ROOT, "hanfu-zhidui", "pattern")

sys.path.insert(0, ZD)
import flat as Z                                       # noqa: E402  直领对襟的平铺几何
sys.path.insert(0, HERE)
os.environ.setdefault("HANFU_OUT", os.path.join(tempfile.gettempdir(), "_ov_probe.svg"))
import build as B1                                     # noqa: E402  V1 的常数
import build_v1b as B2                                 # noqa: E402  V1B 的常数
from docfig import Fig, INK, GRAY                      # noqa: E402

BLUE = "#1f5fa8"
RED = "#b0392b"
G_MINOR = "#d5cec0"
G_MAJOR = "#b5ab9a"
G_ZERO = "#8b8173"

OUT = os.path.join(os.path.dirname(HERE), "out", "doc")


def segs(f, pairs, color, width, dash=""):
    for a, b in pairs:
        f.line(a, b, color, width, dash)


def poly(f, pts, color, width, fill="none", fop=1.0):
    f.path([["M", list(pts[0])]] + [["L", list(q)] for q in pts[1:]] + [["Z"]],
           color, width, "", fill, fop)


def grid(f, x0, x1, y0, y1, cell):
    """100mm 网格：每 cell 一格，5×cell 加重，x=0 / y=0 再加重。"""
    for x in range(int(x0), int(x1) + 1, cell):
        heavy = (x % (5 * cell) == 0)
        col = G_ZERO if x == 0 else (G_MAJOR if heavy else G_MINOR)
        f.line((x, y0), (x, y1), col, 3.6 if x == 0 else (2.8 if heavy else 2.1))
    for y in range(int(y0), int(y1) + 1, cell):
        heavy = (y % (5 * cell) == 0)
        col = G_ZERO if y == 0 else (G_MAJOR if heavy else G_MINOR)
        f.line((x0, y), (x1, y), col, 3.6 if y == 0 else (2.8 if heavy else 2.1))
    # 坐标数字：x 在网格下沿，y 在网格左沿
    for x in range(int(x0), int(x1) + 1, 2 * cell):
        if x:
            f.text(x, y0 - cell * 0.45, "%d" % x, 22, GRAY, "middle")
    for y in range(int(y0), int(y1) + 1, 2 * cell):
        if y:
            f.text(x0 - cell * 0.3, y - cell * 0.12, "%d" % y, 22, GRAY, "end")


def geom_v1():
    HL, S = B1.HALF_L, B1.HALF_S
    CUT, CW = B1.SLIT_HALF, B1.COLLAR_W
    NX, NY = B1.N_X, B1.N_Y
    NTH, NH = B1.NTH, B1.NECK_H
    edge = [[(-S, HL), (-CUT, HL)],
            [(-(CUT + NX * CW), HL), (CUT + NX * CW, HL)],
            [(CUT, HL), (S, HL)]]
    body = [[(-S, 0), (S, 0)], [(-S, 0), (-S, HL)], [(S, 0), (S, HL)]]
    slit = [[(-CUT, HL), (0.0, 0.0)], [(CUT, HL), (0.0, 0.0)]]
    inner = [[(-(CUT + NX * CW), HL + NY * CW), (-NX * CW, NY * CW)],
             [(CUT + NX * CW, HL + NY * CW), (NX * CW, NY * CW)]]
    trap = [(-CUT, HL), (-NTH, HL + NH), (NTH, HL + NH), (CUT, HL)]
    return dict(HL=HL, S=S, CUT=CUT, CW=CW, NTH=NTH, edges=body + edge,
                slit=slit, inner=inner, trap=trap,
                seam=[[(0.0, 0.0), (0.0, HL)]], out_h=None,
                name="V1 原始直领交襟")


def geom_v1b():
    S, HL = B2.HALF_S, B2.L_BODY
    XS, YA = B2.X_SPLIT, B2.Y_ARM
    CUT, CW = B2.SLIT_HALF, B2.COLLAR_W
    NX, NY = B2.N_X, B2.N_Y
    NTH, NH = B2.NTH, B2.NECK_H
    # 折后平铺：袖在肩上（上沿 y = 衣身长），袖底下缘 y = 衣身长 − 接袖长
    outline = [(-S, YA), (-S, HL), (S, HL), (S, YA),
               (XS, YA), (XS, 0), (-XS, 0), (-XS, YA)]
    edges = [[outline[i], outline[(i + 1) % len(outline)]] for i in range(len(outline))]
    slit = [[(-CUT, HL), (0.0, 0.0)], [(CUT, HL), (0.0, 0.0)]]
    inner = [[(-(CUT + NX * CW), HL + NY * CW), (-NX * CW, NY * CW)],
             [(CUT + NX * CW, HL + NY * CW), (NX * CW, NY * CW)]]
    trap = [(-CUT, HL), (-NTH, HL + NH), (NTH, HL + NH), (CUT, HL)]
    seam = [[(0.0, 0.0), (0.0, HL)],
            [(-XS, 0.0), (-XS, HL)], [(XS, 0.0), (XS, HL)]]   # 侧缝＋接袖缝
    return dict(HL=HL, S=S, CUT=CUT, CW=CW, NTH=NTH, edges=edges,
                slit=slit, inner=inner, trap=trap, seam=seam, out_h=B2.JS,
                name="V1B 双长（衣身长 %.0f ／ 接袖长 %.1f）" % (HL, B2.JS))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["v1", "v1b"], default="v1")
    ap.add_argument("--grid", action="store_true", help="画 100mm 网格")
    ap.add_argument("--cell", type=int, default=100, help="网格边长（mm），默认 100")
    a = ap.parse_args()

    g = geom_v1() if a.variant == "v1" else geom_v1b()
    S, HL, CUT, CW = g["S"], g["HL"], g["CUT"], g["CW"]

    f = Fig("叠图 · %s × 默认直领对襟（平铺，同比例%s）" % (g["name"], "，100mm 网格" if a.grid else ""),
            "对齐：下摆齐 y=0、前中重合 x=0；蓝＝直领对襟（%.0f 宽 × 高 %.0f），红＝%s（%.0f × %.0f）"
            % (Z.HW * 2, Z.L, g["name"].split("（")[0], S * 2, HL))

    if a.grid:
        xmax = max(S, Z.HW) + 100
        ymax = max(HL + B2.NECK_H if a.variant == "v1b" else HL + B1.NECK_H, Z.L + Z.LB) + 100
        x0, x1 = -xmax, xmax
        y0, y1 = -200, ymax
        x0 -= x0 % a.cell; x1 -= x1 % a.cell
        y0 -= y0 % a.cell; y1 -= y1 % a.cell
        grid(f, x0, x1, y0, y1, a.cell)

    # 直领对襟：外轮廓 + 领条五块 + 后中缝
    poly(f, Z.back_whole, BLUE, 2.2)
    for pc in (Z.strip_R, Z.strip_L):
        poly(f, pc, BLUE, 2.2, BLUE, 0.10)
    for pc in (Z.tri_R, Z.tri_L):
        poly(f, pc, BLUE, 1.8, BLUE, 0.10)
    poly(f, Z.trap, BLUE, 2.0, BLUE, 0.10)
    f.line((0.0, 0.0), (0.0, Z.L), BLUE, 1.4, "26 14")

    # 古制：外轮廓 + 剪开 + 领条内缘 + 顶梯形 + 中缝（V1B 另含侧缝/接袖缝）
    segs(f, g["edges"], RED, 2.6)
    poly(f, g["trap"], RED, 2.2, RED, 0.14)
    segs(f, g["slit"], RED, 2.2)
    segs(f, g["inner"], RED, 1.6, "18 12")
    segs(f, g["seam"], RED, 1.4, "26 14")

    # 肩线对照
    f.line((-S - 40, HL), (S + 40, HL), RED, 1.0, "10 10")
    f.line((-Z.HW - 40, Z.L), (Z.HW + 40, Z.L), BLUE, 1.0, "10 10")
    f.text(S + 60, HL, "红 肩线 %.0f" % HL, 24, RED)
    f.text(Z.HW + 60, Z.L, "蓝 肩线 %.0f" % Z.L, 24, BLUE)

    # 领口点 / 原点
    f.dot(CUT, HL, "P (%.0f, %.0f)" % (CUT, HL), RED, 14, -16, 24)
    f.dot(CUT, Z.L, "P (%.0f, %.0f)" % (CUT, Z.L), BLUE, 14, -16, 24)
    f.line((CUT + 150, HL), (CUT + 150, Z.L), GRAY, 1.2, "14 10")
    f.text(CUT + 168, (HL + Z.L) / 2.0 + 8, "肩线差 %.0f" % (Z.L - HL), 22, GRAY)
    f.dot(0.0, 0.0, "Q (0, 0) 共用原点", INK, 18, 44, 22)

    # V1B 的台阶与袖段
    if g["out_h"]:
        f.text(-S + 30, g["out_h"] + 90, "袖段 y %.0f…%.0f（袖口高 %.0f）"
               % (HL - g["out_h"], HL, g["out_h"]), 24, RED)
        f.text(-S + 30, (HL - g["out_h"]) / 2.0, "侧缝段 y 0…%.0f" % (HL - g["out_h"]), 24, GRAY)

    # 图例
    ytop = max(HL, Z.L) + (200 if a.grid else 210)
    f.text(-S, ytop, "■ 蓝｜厂商基准 默认直领对襟：%d × %.0f，领口 P(±%.0f, %.0f)，领条宽 %.0f"
           % (round(Z.HW * 2), Z.L, CUT, Z.L, Z.LB), 26, BLUE)
    f.text(-S, ytop - 48, "■ 红｜%s：%d × %.0f，领口 P(±%.0f, %.0f)，领条宽 %.0f"
           % (g["name"], round(S * 2), HL, CUT, HL, CW), 26, RED)
    f.text(-S, ytop - 96, "同一口径（领口宽 %.0f、领条宽 %.0f）落在不同衣长上：肩线差 %.0f mm；"
                          "顶梯形 %.0f → %.1f（红）／ %.0f → %.1f（蓝）"
           % (2 * CUT, CW, Z.L - HL, 2 * CUT, 2 * g["NTH"], 2 * CUT, 2 * abs(Z.MB[0])), 24, INK)
    f.text(-S, -300, "网格 %dmm（每 5 格加重）；只做目测：不加尺寸链、不做面积统计" % a.cell, 22, GRAY)

    stem = os.path.join(OUT, "叠图_%s_vs_直领对襟" % ("V1" if a.variant == "v1" else "V1B"))
    svg, png = f.write(stem, scale=1.0 if a.grid else 0.8)
    print(svg)
    print("%s %.0f×%.0f  P(%.0f,%.0f) ｜ 对襟 %.0f×%.0f  P(%.0f,%.0f) ｜ 肩线差 %.0f ｜ 网格 %d"
          % (g["name"], S * 2, HL, CUT, HL, Z.HW * 2, Z.L, Z.CUT, Z.L, Z.L - HL,
             a.cell if a.grid else 0))
    print(png)


if __name__ == "__main__":
    main()
