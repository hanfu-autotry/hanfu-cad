# -*- coding: utf-8 -*-
"""一步一画 · 分步图（文档用）

第 1 步＝原图（**改动前**的现状，一处不改）；之后每步同一张画布、同一构图改一处：
红线＝这一步新定的线，灰虚线＋淡红填充＝这一步删掉的线／块。

几何取自 geo / flat；只有第 1 步的「改动前上缘」在本文件里按旧构造重建（仅为留档对照，
不参与出图口径——真实几何永远来自 geo.pieces()）。

  python step_doc.py --step 1
  python step_doc.py --step all

产物：out/doc/stepN_<名称>.svg / .png
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import geo
import flat
import sheet
from docfig import Fig, INK, RED, GRAY, LIGHT

OUT = os.path.join(os.path.dirname(HERE), "out", "doc")
d = geo.derive(geo.CASE)
PCS = geo.pieces(d)
FRONT, NEI, XUR, NEI_XUR, BACK = [p["cmds"] for p in PCS[:5]]
MT = PCS[2]["meta"]
OX, OY, R = MT["l_circle"]
P1, P0, PK, H, H1 = MT["P1"], MT["P0"], MT["P"], MT["H"], MT["H1"]
LIFT = geo.UPPER_LIFT


def _mid(o, rr, A, B):
    a0 = math.atan2(A[1] - o[1], A[0] - o[0])
    a1 = math.atan2(B[1] - o[1], B[0] - o[0])
    if a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    elif a0 - a1 > math.pi:
        a1 += 2 * math.pi
    am = (a0 + a1) / 2.0
    return (o[0] + rr * math.cos(am), o[1] + rr * math.sin(am))


def _poly(pts):
    return [["M", list(pts[0])]] + [["L", list(q)] for q in pts[1:]] + [["Z"]]


# ── 现构（第 2 步的新边）──
P1L = (0.0, P1[1] + LIFT)                                     # l′ 端点 (0, 783)，历史
P1P = tuple(P1)                                               # 现行 P1′ ＝ L ∩ 中缝 (0,715)
NX = OX + math.sqrt(max(0.0, R * R - (P1L[1] - OY) ** 2))     # 38.954 ＝ n
N = (NX, P1L[1])
ARC_F = geo.arc3(P1, _mid((OX, OY), R, P1, PK), PK)           # 前片上缘 L 弧：P1 → P
ARC_X = geo.arc3(P1, _mid((OX, OY), R, P1, P0), P0)           # 续衽上缘 L 弧：P1 → P0
ARC_LP = geo.arc3(H, _mid((OX, OY + LIFT), R, H, P1L), P1L)   # l′：H → P1′（已删）
ARC_NP = geo.arc3(N, _mid((OX, OY), R, N, PK), PK)            # 旧 n → P 弧

# ── 改动前的上缘（只为第 1 步「原图」留档）──
_iC = 0
for _c in FRONT[1:]:
    if _c[0] != "C":
        break
    _iC += 1
OLD_FRONT = ([["M", list(P1L)], ["L", list(N)]] + ARC_NP       # 左缘抬到 P1′ + 水平段 + 旧弧
             + [list(c) for c in FRONT[_iC + 1:]])
_hem_rev = [list(c) for c in XUR if c[0] == "C"][4:]          # H1 → (0,0) 的下摆 3 段
_hem_fwd = geo.reverse_open([["M", list(H1)]] + _hem_rev)[1:]  # (0,0) → H1
OLD_XUR = ([["M", list(H)]] + ARC_LP + [["L", [0.0, 0.0]]]    # 上缘 l′ 到 P1′，再直下中缝
           + _hem_fwd + [["L", list(H)], ["Z"]])
OLD_NEI, OLD_NEI_XUR = geo.mirror(OLD_FRONT), geo.mirror(OLD_XUR)


def _base(title, sub, old=False):
    """两步共用的底图：全片 + 尺寸 + 关键点（构图固定，不改）"""
    L, HALF = d["L"], d["HALF"]
    band, cm = flat.collar_band(d)
    CW = geo.solve_collar_w(MT)
    f = Fig(title, sub)
    f.path(BACK, LIGHT, 1.6, dash="26 14")
    f.path(OLD_NEI_XUR if old else NEI_XUR, "#9aa7b4", 1.8)
    f.path(OLD_NEI if old else NEI, "#9aa7b4", 1.8)
    f.path(OLD_FRONT if old else FRONT, INK, 2.6)
    f.path(OLD_XUR if old else XUR, INK, 2.6)
    f.path(band, INK, 2.2)
    for sx in (1.0, -1.0):
        f.line((sx * cm["P"][0], cm["P"][1]), (0.0, cm["ytop"]), INK, 1.8)
    f.line((0, -80), (0, L + 40), GRAY, 1.4, dash="18 12")
    f.text(40, 250, "前中缝 x = 0（竖直，左右各一片）", 26, GRAY)
    f.dim_v(-980, 0, L, "后中长 845")
    f.dim_h(0, HALF, -130, "摆半宽 585")
    f.dim_h(-d["X_FRONT"], 0, -270, "前单边摆宽 722（585 ＋ 续衽越中 137）")
    f.dim_v(1075, d["Y_ARM"], L, "腋深 328")
    f.dim_v(880, d["L"] - d["SEAM_H"], L, "袖根 208")
    f.dim_h(d["X_SH"], d["X_JS"], L + 180, "衣身袖 270 → 接袖缝 840")
    f.dim_v(660, 0, d["RISE"], "起翘 80", dx=20, anchor="start")
    f.dot(d["X_SH"], L, "肩点 570", RED, dx=30, dy=-22)
    f.dot(PK[0], PK[1], "P (65, 845)", RED, dx=18, dy=-14, size=26)
    f.dot(d["X_ARM"], d["Y_ARM"], "腋点 (418, 517)", RED, dx=-250, dy=34)
    f.text(-980, -390, "灰虚线＝后片（半）×2：与前后片共用侧缝与接袖缝，只是叠在后层；"
                       "浅灰＝内襟＋内襟续衽；黑＝外襟（前片＋续衽）与领子", 26, "#555")
    return f, CW


def step1():
    """第 1 步＝原图：改动前的现状，一处不改。"""
    f, CW = _base("第 1 步 · 原图", "改动前一处不改：前片＋续衽（外襟，黑）／内襟＋内襟续衽（浅灰）／"
                                   "后片半×2（灰虚，后层）／领子原位（黑粗带）", old=True)
    f.text(-950, 1015, "领子＝领条原位铺在领口上（宽 %.2f，后中顶点 %.2f）" % (CW, 845.0 + CW), 26, INK)
    f.text(-950, 945, "上缘现状：续衽沿 l′ 冒出 68、前片多一块曲边三角形（都埋在领条里，外面看不见）",
           26, "#555")
    f.text(-950, -465, "这张就是改动前的原图；第 2 步开始，每一步都在这张图上改。", 27, "#555")
    return f.write(os.path.join(OUT, "step1_原图"))


def step2():
    """第 2 步：领口线统一为 L——删掉续衽突出的 68 一节 + 曲边三角形。"""
    f, CW = _base("第 2 步 · 领口线统一为 L",
                  "前片／续衽的上缘都收成 l 弧；续衽突出被领条包裹的那一节、以及曲边三角形，全部删除")
    # ① 新边（红）：L 弧
    f.path([["M", list(P1)]] + ARC_F, RED, 3.4)
    f.path([["M", list(P1)]] + ARC_X, RED, 3.4)
    # ② 删掉的：l′ 突出段、P1′→n 水平段、n→P 的旧弧
    f.path([["M", list(H)]] + ARC_LP, "#c0392b", 2.2, dash="20 12")
    f.path([["M", list(P1L)], ["L", list(N)]], "#c0392b", 2.2, dash="20 12")
    f.path([["M", list(N)]] + ARC_NP, "#c0392b", 2.2, dash="20 12")
    # 删掉的续衽突出块：l′ 弧 H→P1′ ＋ 中缝 P1′→P1 ＋ L 弧 P1→P0 ＋ HH1 P0→H
    poly = (sheet.sample([["M", list(H)]] + ARC_LP, 40) + [P1]
            + sheet.sample([["M", list(P1)]] + ARC_X, 40)[1:] + [H])
    f.path(_poly(poly), "#c0392b", 1.6, fill="#c0392b", fop=0.14)
    # 曲边三角形 P1′-n-P1（原来并入前片的那块）
    tri = [P1L, N] + sheet.sample([["M", list(N)]] + geo.arc3(N, _mid((OX, OY), R, N, P1), P1), 24)[1:]
    f.path(_poly(tri), "#c0392b", 1.6, fill="#c0392b", fop=0.22)
    # ③ 标注
    f.text(-950, 1015, "红＝新上缘：L 弧（前片 145.7 ／ 续衽 513.5）", 28, RED)
    f.text(-950, 945, "淡红块＝删掉的 l′ 突出段 485.7×68：续衽 −27,871 mm²（−9.80%）", 27, "#c0392b")
    f.text(-950, 875, "淡红小块＝原并入前片的曲边三角形 1,392 mm²，同删", 27, "#c0392b")
    f.text(-950, -465, "领条不动：只由 L 与领条宽 %.2f 决定（长 1448.5，端面 A＝P0，顶点 931.71）" % CW, 27, INK)
    f.dot(P0[0], P0[1], "P0＝A (-423.59, 453.65)", RED, dx=-330, dy=30, size=24)
    return f.write(os.path.join(OUT, "step2_领口统一为L"))


def step3():
    """第 3 步：续衽上缘 L′ 由领条缘派生（Γ_C 弧 A′→X ＋ 水平段 X→P1′）。"""
    f, CW = _base("第 3 步 · 续衽上缘 L′ 按领条缘派生",
                  "过 P1′ 作水平线截领条外缘 Γ_C 得 X；L′ ＝ Γ_C 弧（A′→X）＋ 水平段（X→P1′）")
    XP, A2, R2 = tuple(MT["X_LP"]), tuple(MT["A2"]), MT["R2"]
    acc = geo.arc3(A2, _mid((OX, OY), R2, A2, XP), XP)          # Γ_C 弧 A′ → X
    # ① 新上缘（红）：Γ_C 弧 A′→X ＋ 水平段 X→P1′
    f.path([["M", list(A2)]] + acc, RED, 3.4)
    f.path([["M", list(XP)], ["L", list(P1P)]], RED, 3.4)
    # ② 上一步的收边（L 弧 P1→P0）现在退成片内线
    f.path([["M", list(P1)]] + ARC_X, "#c0392b", 2.0, dash="20 12")
    # ③ 新增区：L 弧 P1→P0 ＋ P0→A′ ＋ Γ_C 弧 A′→X ＋ 水平段 X→P1′ ＋ 中缝 P1′→P1
    poly = (sheet.sample([["M", list(P1)]] + ARC_X, 40) + [A2]
            + sheet.sample([["M", list(A2)]] + acc, 40)[1:] + [XP, P1P])
    f.path(_poly(poly), "#c0392b", 1.6, fill="#c0392b", fop=0.16)
    # ④ 标注
    f.text(-950, 1065, "P1′ ＝ L ∩ 中缝 ＝ (0, 715)｜红＝新上缘 L′", 28, RED)
    _apts = sheet.sample([["M", list(A2)]] + acc, 80)
    accL = sum(math.hypot(_apts[i + 1][0] - _apts[i][0], _apts[i + 1][1] - _apts[i][1])
               for i in range(len(_apts) - 1))
    f.text(-950, 1005, "过 P1′ 作水平线截 Γ_C 得 X(−108.35, 715)：弧 %.1f ＋ 水平 %.1f ＝ %.1f"
           % (accL, abs(XP[0]), accL + abs(XP[0])), 27, "#c0392b")
    f.text(-950, 945, "淡红＝续衽新增 36,700.6 mm²（→ 293,107.8）", 27, "#c0392b")
    f.text(-950, -465, "领条不动：1448.49 × %.2f（只由 L 与领条宽决定）；L′ 只是跟着领条外缘走" % CW, 27, INK)
    f.dot(XP[0], XP[1], "X", RED, dx=-14, dy=-18, size=26)
    f.dot(A2[0], A2[1], "A′", RED, dx=-46, dy=-14, size=26)
    return f.write(os.path.join(OUT, "step3_L′按领条缘"))


STEPS = {1: ("step1_原图", step1), 2: ("step2_领口统一为L", step2),
         3: ("step3_L′按领条缘", step3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="all")
    a = ap.parse_args()
    want = range(1, 9) if a.step == "all" else [int(a.step)]
    for n in want:
        if n not in STEPS:
            continue
        print("[%s]" % STEPS[n][0])
        STEPS[n][1]()


if __name__ == "__main__":
    main()
