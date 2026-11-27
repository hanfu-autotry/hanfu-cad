# -*- coding: utf-8 -*-
"""叠图 · 原始直领交襟衣 V1 × 厂商基准默认直领对襟（**只做目测观看**）

两块平铺轮廓同比例叠在一起，看差在哪：
  · 对齐方式：**下摆齐（y = 0）、前中重合（x = 0）**，mm，同一比例，不加缩放；
  · 蓝＝默认口径 直领对襟（`../hanfu-zhidui/pattern/flat.py` 的几何，直接取它的变量，不另算）；
  · 红＝古制 V1 原始直领交襟（`build.py` 的平铺那一段，常数照搬）；
  · 两块只画外轮廓 ＋ 领条／开领那几根线；浅色填充只为分辨领条区，不是面积统计。

    python pattern/overlay_zhidui.py   →  out/doc/叠图_V1_vs_直领对襟.svg / .png

**这张图不参与出图口径**，是看稿；要数值看 `构造分步图说.md` 与两个项目各自的 README。
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # hanfu/
ZD = os.path.join(ROOT, "hanfu-zhidui", "pattern")

sys.path.insert(0, ZD)
import flat as Z                                       # noqa: E402  直领对襟的平铺几何
sys.path.insert(0, HERE)
os.environ.setdefault("HANFU_OUT", os.path.join(tempfile.gettempdir(), "_ov_v1.svg"))
import build as B                                      # noqa: E402  V1 的常数
from docfig import Fig, INK, GRAY                     # noqa: E402

BLUE = "#1f5fa8"
RED = "#b0392b"

OUT = os.path.join(os.path.dirname(HERE), "out", "doc")

# ── V1 平铺（服装坐标：x = 0 前中，y = 0 下摆，y 向上）──────────────
HL, S = B.HALF_L, B.HALF_S
CUT, CW = B.SLIT_HALF, B.COLLAR_W
NX, NY = B.N_X, B.N_Y
NTH, NH = B.NTH, B.NECK_H

V1_EDGE = [  # 顶边三段（领条压过的地方断开）
    [(-S, HL), (-CUT, HL)],
    [(-(CUT + NX * CW), HL), (CUT + NX * CW, HL)],
    [(CUT, HL), (S, HL)],
]
V1_BODY = [[(-S, 0), (S, 0)], [(-S, 0), (-S, HL)], [(S, 0), (S, HL)]]
V1_SLIT = [[(-CUT, HL), (0.0, 0.0)], [(CUT, HL), (0.0, 0.0)]]
V1_INNER = [[(-(CUT + NX * CW), HL + NY * CW), (-NX * CW, NY * CW)],
            [(CUT + NX * CW, HL + NY * CW), (NX * CW, NY * CW)]]
V1_TRAP = [(-CUT, HL), (-NTH, HL + NH), (NTH, HL + NH), (CUT, HL)]


def segs(f, pairs, color, width, dash=""):
    for a, b in pairs:
        f.line(a, b, color, width, dash)


def poly(f, pts, color, width, fill="none", fop=1.0):
    f.path([["M", list(pts[0])]] + [["L", list(q)] for q in pts[1:]] + [["Z"]],
           color, width, "", fill, fop)


def main():
    f = Fig("叠图 · V1 原始直领交襟 × 默认直领对襟（平铺，同比例）",
            "对齐：下摆齐 y=0、前中重合 x=0；蓝＝直领对襟（%.0f 宽 × 高 %.0f），红＝V1（%.0f × %.0f）"
            % (Z.HW * 2, Z.L, S * 2, HL))

    # 直领对襟：外轮廓 + 领条五块 + 后中缝
    poly(f, Z.back_whole, BLUE, 2.2)
    for pc in (Z.strip_R, Z.strip_L):
        poly(f, pc, BLUE, 2.2, BLUE, 0.10)
    for pc in (Z.tri_R, Z.tri_L):
        poly(f, pc, BLUE, 1.8, BLUE, 0.10)
    poly(f, Z.trap, BLUE, 2.0, BLUE, 0.10)
    f.line((0.0, 0.0), (0.0, Z.L), BLUE, 1.4, "26 14")

    # V1：外轮廓 + 顶边 + 剪开 + 领条内缘 + 顶梯形 + 后中缝
    segs(f, V1_BODY + V1_EDGE, RED, 2.6)
    poly(f, V1_TRAP, RED, 2.2, RED, 0.14)
    segs(f, V1_SLIT, RED, 2.2)
    segs(f, V1_INNER, RED, 1.6, "18 12")
    f.line((0.0, 0.0), (0.0, HL), RED, 1.4, "26 14")

    # 肩线对照（两条水平延长虚线）
    f.line((-S - 40, HL), (S + 40, HL), RED, 1.0, "10 10")
    f.line((-Z.HW - 40, Z.L), (Z.HW + 40, Z.L), BLUE, 1.0, "10 10")
    f.text(S + 60, HL, "V1 肩线 %.0f" % HL, 24, RED)
    f.text(Z.HW + 60, Z.L, "直领对襟 肩线 %.0f" % Z.L, 24, BLUE)

    # 领口点：同一 x、两个高度 ⇒ 高差一眼看出
    f.dot(CUT, HL, "P (%.0f, %.0f)" % (CUT, HL), RED, 14, -14, 24)
    f.dot(CUT, Z.L, "P (%.0f, %.0f)" % (CUT, Z.L), BLUE, 14, -14, 24)
    f.line((CUT + 120, HL), (CUT + 120, Z.L), GRAY, 1.2, "14 10")
    f.text(CUT + 138, (HL + Z.L) / 2.0 + 8, "肩线差 %.0f" % (Z.L - HL), 22, GRAY)
    f.dot(0.0, 0.0, "Q (0, 0) 共用原点", INK, 18, 40, 22)

    # 图例（衣外上方）
    y = Z.L + 210
    f.text(-S, y, "■ 蓝线｜厂商基准 默认直领对襟：%d × %.0f，领口 P(±%.0f, %.0f)，领条宽 %.0f"
           % (round(Z.HW * 2), Z.L, CUT, Z.L, Z.LB), 26, BLUE)
    f.text(-S, y - 46, "■ 红线｜古制 V1 原始直领交襟：%d × %.0f，领口 P(±%.0f, %.0f)，领条宽 %.0f"
           % (round(S * 2), HL, CUT, HL, CW), 26, RED)
    f.text(-S, y - 92, "同一口径（领口宽 %.0f、领条宽 %.0f）落在不同衣长上：肩线高差 %.0f mm；"
                       "顶梯形 %.0f → %.1f（V1）／ %.0f → %.1f（对襟）"
           % (2 * CUT, CW, Z.L - HL, 2 * CUT, 2 * NTH, 2 * CUT, 2 * abs(Z.MB[0])), 24, INK)
    f.text(-S, -170, "只做目测：不加尺寸链、不做面积统计；数值见两个项目各自的 README 与 构造分步图说.md", 22, GRAY)

    stem = os.path.join(OUT, "叠图_V1_vs_直领对襟")
    svg, png = f.write(stem)
    print(svg)
    print("V1 %.0f×%.0f  P(%.0f,%.0f) ｜ 对襟 %.0f×%.0f  P(%.0f,%.0f) ｜ 肩线差 %.0f"
          % (S * 2, HL, CUT, HL, Z.HW * 2, Z.L, Z.CUT, Z.L, Z.L - HL))
    print(png)


if __name__ == "__main__":
    main()
