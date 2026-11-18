# -*- coding: utf-8 -*-
"""直领对襟 · 平铺预览（**只做正面线稿**，白底纯黑线，不填色、不做背视）

    python pattern/flat.py
      → out/平铺预览.svg

口径（用户 2026-11-18 定，纯几何）：

    外轮廓   ＝ 后片（半 ×2 合成整片）
    前襟边   ＝ 弦 c：Q→P，P ＝ 领口点 (±NECK_W/2, L)，Q ＝ 前中缝∩下摆 ＝ (0, 0)
    领条     ＝ 与襟缘 c **平行、宽 LB ＝ COLLAR_W ＝ 3cm** 的区域（法向等距 30）；颈口处合理转折为
                 「前片两三角 ＋ 后片梯形」。五块，共边＝折痕（不是接缝）：
                   前襟带（右/左）＝ {Q, P, P+LB·n̂, Q+LB·n̂}      与 c 平行、宽 LB
                   前片三角（右/左）＝ {P, P+LB·n̂, M}             转角处的折角
                   后片梯形        ＝ {P, M, M′, P′}              底 NECK_W、高 LB
                 M ＝ 过 P+LB·n̂ 且平行 c 的直线 ∩ 直线 y = L+LB；M′ ＝ 镜像
                 ⇒ 后领带高 ＝ LB，顶边 ＝ NECK_W − 2·(LB/ tan∠)（本案 105.5）＝ 梯形
                 两前襟带的内缘在 y ＝ LB/(2·u_x) ≈ 154 处相交 ⇒ 下摆附近交叠成「又」
    后中缝   ＝ x=0 虚线（下摆→肩线）
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet

INK, GRAY = "#1a1a1a", "#6f6f6f"

W, H = 2200, 1400
OX, OY = W / 2.0, 1090.0            # 前中 / 下摆基线

def txt(x, y, s, size=22, color=INK, anchor="start", weight=None):
    w = ' font-weight="600"' if weight else ""
    return ('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" '
            'fill="%s" text-anchor="%s"%s>%s</text>' % (x, y, size, color, anchor, w, s))


def poly(pts, close=True):
    d = "M %.1f %.1f" % (OX + pts[0][0], OY - pts[0][1])
    for p in pts[1:]:
        d += " L %.1f %.1f" % (OX + p[0], OY - p[1])
    return d + (" Z" if close else "")


def seg(a, b, w=2.2, dash=None, color=INK):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="%.1f" '
            'fill="none" stroke-linecap="round"%s/>'
            % (OX + a[0], OY - a[1], OX + b[0], OY - b[1], color, w, d))


def add(p, n, w):
    return (p[0] + n[0] * w, p[1] + n[1] * w)


# ── 几何（全部来自 geo）────────────────────────────────────────────
PRM = geo.params()
P = {p["name"]: p for p in geo.step2_pieces(PRM)}
back_half = sheet.sample(P["后片"]["cmds"], 32)
back_whole = back_half + list(reversed([(-x, y) for x, y in back_half]))

L = max(y for _, y in back_whole)          # 肩线
HW = max(x for x, _ in back_whole)         # 半宽
CUT = geo.slit_half(PRM)                   # 80 领口点横坐标
LB = PRM["COLLAR_W"]                       # 30 领条宽（与襟缘平行的等距宽）

HEM = (0.0, 0.0)                           # Q ＝ 前中缝∩下摆
PR = (CUT, L)                              # P ＝ 领口点（右）
PL = (-CUT, L)                             # P′

_n = math.hypot(CUT, L)
uR = (CUT / _n, L / _n)                    # 襟缘方向（Q→P）
nR = (-L / _n, CUT / _n)                   # 左法向 ＝ 指向颈口一侧
nL = (-nR[0], nR[1])

QB = add(HEM, nR, LB)                      # 右襟带下摆外角
PB = add(PR, nR, LB)                       # 右襟带 P 处内角
YB = L + LB                                # 后领带上缘 y
MB = (geo.trap_top_half(PRM), YB)                     # 右转角点 M（＝geo 的 miter 解）
ML = (-MB[0], YB)                                    # M′

strip_R = [HEM, PR, PB, QB]                # 前襟带（右）：与襟缘平行、宽 LB
strip_L = [HEM, PL, (-PB[0], PB[1]), (-QB[0], QB[1])]
tri_R = [PR, PB, MB]                       # 前片三角（右）：转角折角
tri_L = [PL, (-PB[0], PB[1]), ML]
trap = [PR, MB, ML, PL]                    # 后片梯形：底 160 → 顶 2|M.x|，高 LB

X_CROSS = LB / (2.0 * uR[0])               # 两带内缘交点 y

s = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
     'viewBox="0 0 %d %d">' % (W, H, W, H),
     '<rect width="100%" height="100%" fill="#ffffff"/>',
     txt(56, 62, "直领对襟 · 平铺（正面线稿）", 38, INK, weight=1),
     txt(56, 102, "外轮廓＝后片（半 ×2 合成整片）｜前襟边＝弦 Q(0,0)→P(±%.0f, %.0f)｜"
                  "领条＝与襟缘平行、宽 %.0f 的区域（领条宽 3cm），颈口转折为 前片两三角＋后片梯形"
                  % (CUT, L, LB), 21, GRAY)]

# 1 外轮廓（后片整片）
s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" '
         'stroke-linejoin="round"/>' % (poly(back_whole), INK))

# 2 领条五块（同一片料；共边＝折痕）
for pc in (strip_R, strip_L):
    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="3.2" '
             'stroke-linejoin="round"/>' % (poly(pc), INK))
for pc in (tri_R, tri_L):
    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.4" '
             'stroke-linejoin="round"/>' % (poly(pc), INK))
s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" '
         'stroke-linejoin="round"/>' % (poly(trap), INK))

# 3 后中缝（虚线，只到下摆→肩线）
s.append(seg((0, 0), (0, L), 1.6, "26 14"))

# 4 布纹（两侧各一道，细虚线）
for sx in (-1, 1):
    x = sx * (CUT + 250)
    s.append(seg((x, L * 0.20), (x, L * 0.70), 1.4, "18 10", GRAY))

# 5 标注（都在衣外）
s.append(txt(OX - CUT - 210, OY - L - LB + 8, "领条宽 %.0f（与襟缘平行等距）" % LB, 19, INK, "end"))
s.append(txt(OX + MB[0] + 26, OY - YB - 12, "后片梯形：%.0f → %.1f（高 %.0f）"
             % (CUT * 2, 2 * abs(MB[0]), LB), 19, INK))
s.append(txt(OX + CUT + 170, OY - L * 0.55, "前襟边：Q→P（P 领口点 x=%.0f）" % CUT, 19, INK))
s.append(txt(OX + CUT + 26, OY - YB - 56, "前片三角 ×2（转角折角）", 19, INK))
s.append(txt(OX - CUT - 200, OY - L * 0.42, "后中缝", 19, GRAY, "end"))
s.append(txt(OX + 26, OY - X_CROSS - 16, "两带内缘交于 y=%.0f ⇒ 下摆附近交叠" % X_CROSS, 19, INK))

s.append(txt(OX, OY + 52, "领条＝与襟缘平行、宽 %.0f 的五块（前襟带×2 ＋ 前片三角×2 ＋ 后片梯形）；"
             "裁片＝同宽的 %.1f × %.0f 直条"
             % (LB, 2 * geo.neck_cut_len(PRM) + CUT * 2, LB), 23, INK, "middle"))
s.append(txt(OX, OY + 88, "平铺宽 %.0f（2 × %.0f）　高（到下摆）%.0f"
             % (HW * 2, HW, L), 21, GRAY, "middle"))

# 平铺宽尺寸线
s.append(seg((-HW, -96), (HW, -96), 1.0, color=GRAY))
s.append(seg((-HW, -86), (-HW, -106), 1.0, color=GRAY))
s.append(seg((HW, -86), (HW, -106), 1.0, color=GRAY))

# 100mm 标尺
bx, by = 56, H - 44
s.append('<g id="SCALE" stroke="%s" stroke-width="2.2" fill="none">' % INK)
for k in range(11):
    hh = 28 if k % 5 == 0 else 15
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx + k * 100, by, bx + k * 100, by - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx, by, bx + 1000, by))
s.append('</g>')
s.append(txt(bx, by + 30, "100mm 校验标尺（1:1 打印后实测，误差应 ≤0.5mm）", 20, INK))
s.append('</svg>')

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)
fn = os.path.join(OUT, "平铺预览.svg")
open(fn, "w", encoding="utf-8").write("\n".join(s))
print(fn)
print("平铺 %.0f × %.0f ｜ 襟缘 Q(0,0)→P(±%.0f,%.0f) ｜ 领宽 %.0f ｜ 带外角 (%.2f,%.2f) ｜ "
      "转角 M=(%.2f,%.2f) ｜ 后领带顶宽 %.2f ｜ 内缘交点 y=%.2f"
      % (HW * 2, L, CUT, L, LB, QB[0], QB[1], MB[0], MB[1], 2 * abs(MB[0]), X_CROSS))
