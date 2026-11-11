# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 第 4 步：上领子（上领缘直线折线 · A 在 P₁ 右上方）

    python pattern/step4.py
      → out/step4_上领子.svg / .png       平铺线稿 + 领子
      → out/step4_领口放大.svg / .png     V 附近局部放大（4×）
      → out/step4.json

用户 2026-11-10 22:15–22:19 口径：
  ① P₁A 为领高，暂取 3cm = 30mm（geo.COLLAR_H，可调）；
  ② B 在「直线」HP₂ 上，**不是线段** H→P₂；
  ③ 领子带子：起点边 P₂B，经过 P₁A，终点边 P₂′B′；
  ④ 左右镜像同步（承第 3 步），故 P₁′A′ 与 P₂′B′ 一并存在。

**2026-11-11 11:42**：用户给三张实物参考图（已归档 `ref/`），否决抽象几何选项，
  「领子完全看参考图处理方法」——领子为**等宽、边缘以直线段为主**的竖起带。
  ref/ 只作拓扑依据，**不从照片量取任何数值**。

**2026-11-11 11:48 修正（用户「能工智人修正」）**：
  · 「P1P2 为圆心角 60 度的弧」：第 3 步新领口改为 60° 解析圆弧，
    端点 P₁/P₂ 不动、弦长不变 ⇒ R = 弦长 = 76.5732mm，圆心由弦中垂线解析确定，
    取弧中点 y 较小的一支＝凹向下摆；左片圆心 = 右片关于 x=0 镜像、两段不共圆。
  · 「A 依然右上角」：A = P₁ + 30·mirror(w) = (−44.819281, 799.549284) 不动。
  · 「上领缘采用直线」：B→A→A′→B′ 回到**三段直线折线**（撤销 01:13 三段圆弧），
    四个端点 A/B/A′/B′、四条 30mm 宽度边全部不动。
  · 领子下缘＝第 3 步 60° 弧（红线复用，不重复描）。

解析推导（不量图）：
  w = −U_LAP（沿门襟边直线指向 V，向上偏左 9.944294°）—— 由「B 在直线 HP₂ 上」唯一确定；
  mirror(w) = (−w.x, w.y)（向上偏右 9.944294°）＝「P₁ 右上方」；
  B  = P₂ + 30w          = V + 20·u_lap = (3.453812, 750.300478)
  A  = P₁ + 30·mirror(w) = (−44.819281, 799.549284)   ← P₁ 右上方
  A′ = mirror_x(A) = (44.819281, 799.549284)；B′ = mirror_x(B) = (−3.453812, 750.300478)
  A—A′ = 89.6386mm < 下缘中段 P₁—P₁′ = 100mm；A/A′ 竖起在顶边之上 29.5493mm。
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet
from step1 import make_png

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

INK, GRAY, RED, BLUE = "#1a1a1a", "#6f6f6f", "#c0392b", "#1f5fa8"
CP = geo.collar_points()
PAIR = geo.segment_p1p2_pair()
RIGHT, LEFT = PAIR["right"], PAIR["left"]


def selftest():
    r = []

    def ck(name, ok, extra=""):
        r.append((name, bool(ok), extra))

    cp = CP
    h = cp["h"]
    A, B, Ap, Bp = cp["A"], cp["B"], cp["Ap"], cp["Bp"]
    P1, P2, P1p, P2p = cp["P1"], cp["P2"], cp["P1p"], cp["P2p"]
    V = geo.V
    L = V[1]
    w, wA = cp["dir"], cp["dir_A"]

    ck("领子＝上领缘直线折线（A 在 P₁ 右上方），不是三段圆弧、不是同心弧",
       cp["mode"].startswith("上领缘直线折线") and cp["concentric"] is False)
    ck("领高 h = 30mm（暂取 3cm，可调）", abs(h - 30.0) < 1e-9)
    ck("|P₁A| = 30mm（领高）",
       abs(math.dist(P1, A) - 30.0) < 1e-9, "%.4f mm" % math.dist(P1, A))
    ck("四条宽度边等长 = 30mm（等高领子）",
       all(abs(math.dist(a, b) - h) < 1e-9 for a, b in cp["width_edges"]))
    ck("w = −U_LAP（由「B 在直线 HP₂ 上」唯一确定）",
       abs(geo._cross(w, (-geo.U_LAP[0], -geo.U_LAP[1]))) < 1e-9)
    ck("P₁A 方向 = mirror_x(w)（向上偏右 9.944294°）",
       wA == list(geo.mirror_x(w)))
    ck("★ A 依然在 P₁ 右上方（用户 11:48「A 依然右上角」）",
       A[0] > P1[0] + 1e-9 and A[1] > P1[1] + 1e-9,
       "A=(%.6f, %.6f) vs P₁=(%.0f, %.0f)" % (A[0], A[1], P1[0], P1[1]))
    ck("★ A′ 在 P₁′ 左上方（向中缝收拢，左右镜像同步）",
       Ap[0] < P1p[0] - 1e-9 and Ap[1] > P1p[1] + 1e-9)
    ck("★ 竖起：A / A′ 在顶边 y=770 之上",
       A[1] > L + 1e-9 and Ap[1] > L + 1e-9,
       "Δy=%.4f mm" % (A[1] - L))
    ck("上窄下宽：A—A′ = 89.6386mm < 下缘中段 P₁—P₁′ = 100mm",
       abs(A[1] - Ap[1]) < 1e-9 and cp["AA"] < math.dist(P1, P1p) - 1e-9,
       "A—A′=%.4f / P₁—P₁′=%.0f mm" % (cp["AA"], math.dist(P1, P1p)))
    ck("A = P₁ + h·mirror(w)（解析端点，未动）",
       abs(A[0] - (P1[0] + h * wA[0])) < 1e-9 and
       abs(A[1] - (P1[1] + h * wA[1])) < 1e-9)
    ck("B = P₂ + h·w = V + 20·u_lap（仍在直线 HP₂ 上）",
       abs(B[0] - (V[0] + 20 * geo.U_LAP[0])) < 1e-9 and
       abs(B[1] - (V[1] + 20 * geo.U_LAP[1])) < 1e-9,
       "B=(%.6f, %.6f)" % (B[0], B[1]))
    ck("A′/B′ = A/B 关于前中缝 x=0 镜像",
       Ap == list(geo.mirror_x(A)) and Bp == list(geo.mirror_x(B)))
    ck("B 在直线 HP₂ 上",
       abs(geo._cross((B[0] - V[0], B[1] - V[1]), geo.U_LAP)) < 1e-9)
    hp = (geo.H[0] - P2[0], geo.H[1] - P2[1])
    s = ((B[0] - P2[0]) * hp[0] + (B[1] - P2[1]) * hp[1]) / (hp[0] ** 2 + hp[1] ** 2)
    ck("B 严格在线段 H→P₂ 之外（「直线不是线段」）", s < -1e-9, "s=%.4f" % s)
    ck("B′ 在左片门襟边直线 H′P₂′ 上",
       abs(geo._cross((Bp[0] - V[0], Bp[1] - V[1]),
                      (-geo.U_LAP[0], geo.U_LAP[1]))) < 1e-9)
    ck("宽度边方向：P₂B∥w、P₁A∥mirror(w)、P₁′A′∥w、P₂′B′∥mirror(w)",
       all(abs(geo._cross((b[0] - a[0], b[1] - a[1]), d)) < 1e-9
           for (a, b), d in zip(cp["width_edges"], cp["width_edge_dirs"])))
    ck("领子下缘折点 = P₂→P₁→P₁′→P₂′", cp["lower"] == [P2, P1, P1p, P2p])
    ck("上缘 4 端点 = B→A→A′→B′（11:48 端点全不动）",
       cp["upper"] == [B, A, Ap, Bp])
    ck("★ 上领缘采用直线：upper_path 恰为 4 个端点、无中间采样点（不是圆弧）",
       len(cp["upper_path"]) == 4 and cp["upper_path"] == cp["upper"],
       "%d 点" % len(cp["upper_path"]))
    ck("上缘三段都是直线段（B→A、A→A′、A′→B′，无弧中点）",
       all(len(seg) == 2 for seg in
           [[cp["upper_path"][i], cp["upper_path"][i + 1]] for i in range(3)]))
    ck("第 3 步新领口仍是圆弧采样折线（未回退成直线）",
       len(RIGHT["samples"]) > 2 and len(LEFT["samples"]) > 2,
       "%d 点/段" % len(RIGHT["samples"]))
    ck("★ 第 3 步 P₁P₂ 圆心角 = 60°（用户 11:48 令）",
       abs(abs(RIGHT["sweep_deg"]) - geo.ARC_SWEEP_DEG) < 1e-9 and
       abs(abs(LEFT["sweep_deg"]) - geo.ARC_SWEEP_DEG) < 1e-9,
       "%.6f°" % RIGHT["sweep_deg"])
    ck("★ 60° 弧 R = 弦长 = 76.5732mm（不再是 VP₁=50、圆心不再是 V）",
       abs(geo.ARC_R - RIGHT["chord"]) < 1e-9 and
       abs(RIGHT["radius"] - geo.ARC_R) < 1e-9,
       "R=%.6f mm" % geo.ARC_R)
    ck("60° 弧圆心由弦中垂线解析确定、左片圆心 = 右片镜像（不共圆）",
       abs(RIGHT["center"][0] + LEFT["center"][0]) < 1e-9 and
       abs(RIGHT["center"][1] - LEFT["center"][1]) < 1e-9,
       "C=(%.6f, %.6f)" % (RIGHT["center"][0], RIGHT["center"][1]))
    ck("60° 弧凹向下摆（弧中点低于弦中点）",
       RIGHT["apex"][1] < RIGHT["midpoint"][1],
       "弧中点 y=%.4f" % RIGHT["apex"][1])
    ck("领子下缘 = 第 3 步两条 60° 圆弧 + 顶边中段直线（红线复用，不重复描）",
       len(cp["lower_path"]) > 2 and cp["lower_path"][0] == P2 and
       cp["lower_path"][-1] == P2p)
    ck("四个端点与四条 30mm 宽度边全不动（11:48 只换线型 / 弧的圆心角）",
       cp["upper"] == [B, A, Ap, Bp] and
       all(abs(math.dist(a, b) - h) < 1e-9 for a, b in cp["width_edges"]))
    return r


def _tx(x, y, s, size=22, color=INK, anchor="start", weight=None):
    w = ' font-weight="600"' if weight else ""
    # SVG 文本里的裸 < / > / & 会让整个 SVG 变成非法 XML → 浏览器拒渲染（白图）。
    # 统一转义（历史踩坑：01:03 白图）。
    t = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return ('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" '
            'fill="%s" text-anchor="%s"%s>%s</text>' % (x, y, size, color, anchor, w, t))


def _seg(TX, a, b, w=2.2, dash=None, color=INK):
    ds = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="%.1f" '
            'fill="none" stroke-linecap="round"%s/>'
            % (TX(a)[0], TX(a)[1], TX(b)[0], TX(b)[1], color, w, ds))


def _poly(TX, pts, w, color, close=False):
    d = "M %.1f %.1f" % TX(pts[0])
    for q in pts[1:]:
        d += " L %.1f %.1f" % TX(q)
    if close:
        d += " Z"
    return '<path d="%s" stroke="%s" stroke-width="%.1f" fill="none" stroke-linejoin="round"/>' % (d, color, w)


def _dot(TX, p, lab, dx, dy, color, rad=7):
    x, y = TX(p)
    return ['<circle cx="%.1f" cy="%.1f" r="%d" fill="#ffffff" stroke="%s" stroke-width="2.2"/>'
            % (x, y, rad, color),
            _tx(x + dx, y + dy, lab, 23, color, weight=1)]


def _head(W, H, title, lines):
    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         _tx(56, 62, title, 38, INK, weight=1)]
    for i, ln in enumerate(lines):
        s.append(_tx(56, 102 + 32 * i, ln, 21, GRAY))
    return s


def make_flat_step4():
    """平铺线稿 + 领子。外轮廓沿用第 3 步骨架（不加 Z）。"""
    W, H = 2200, 1500
    OX, OY = W / 2.0, 1120.0

    def TX(q):
        return (OX + q[0], OY - q[1])

    half = sheet.sample(geo.back_piece()["cmds"], 32)
    whole = half + list(reversed([(-x, y) for x, y in half]))
    L = max(y for _, y in whole)
    HW = max(x for x, _ in whole)
    V, Hh = geo.V, geo.H
    Hm = (-Hh[0], 0.0)
    R1, R2 = RIGHT["P1"], RIGHT["P2"]
    L1, L2 = LEFT["P1"], LEFT["P2"]
    flat_dashed = [[V, L1], [R1, V]]
    solid_d, top_dash = sheet.split_polyline(whole, flat_dashed, TX)
    cp = CP

    s = _head(W, H, "试验竖领浅交襟 · 第 4 步 · 上领子（上领缘直线折线 · A 在 P₁ 右上方）", [
        "外轮廓＝后片半 ×2 镜像合成整片　｜　红线＝第 3 步新领口圆弧（圆心角 60°、R=弦长=76.5732mm）　｜　蓝线＝上领缘直线折线",
        "领子：起点边 P₂B → 经过 P₁A / P₁′A′ → 终点边 P₂′B′；四条宽度边各 30mm；A 在 P₁ 右上方、竖起 29.55mm",
        "11:48 修正：P₁P₂ 改圆心角 60° 弧、A 依然右上角、上领缘采用直线（撤销三段圆弧）；白底、不填色、不做背视",
    ])
    # 1 外轮廓（不加 Z：split_polyline 用 M 断开后，Z 会闭合到最近 M 凭空生线）
    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" '
             'stroke-linejoin="round"/>' % (solid_d, INK))
    for a, b in top_dash:
        s.append(_seg(TX, a, b, 2.6, "14 10"))
    # 2 后中缝
    s.append(_seg(TX, (0, 0), (0, L), 1.6, "26 14", GRAY))
    # 3 前片门襟边（P₂→H 实线，V→P₂ 旧边虚线）
    s.append(_seg(TX, R2, Hh, 3.0))
    s.append(_seg(TX, L2, Hm, 3.0))
    s.append(_seg(TX, V, R2, 3.0, "14 10"))
    s.append(_seg(TX, V, L2, 3.0, "14 10"))
    # 4 领子：上领缘直线折线 + 四条宽度边；下缘＝红新领口圆弧，直接复用、不重复描
    s.append(_poly(TX, cp["upper_path"], 3.2, BLUE))
    for a, b in cp["width_edges"]:
        s.append(_seg(TX, a, b, 2.6, color=BLUE))
    # 5 新领口：左右镜像同步的两条 60° 圆弧（解析采样折线，红色实线）
    s.append(_poly(TX, RIGHT["samples"], 4.2, RED))
    s.append(_poly(TX, LEFT["samples"], 4.2, RED))

    # 6 点标注：领口 8 个点位在 1:1 主图只占约 110mm，标签必互相遮挡 →
    #    全部交给「领口局部放大（4×）」，主图只留 V / S / S′ / H / H′。
    for p, lab, dx, dy, col in [
        (V, "V", 16, -46, INK),
        ((-geo.X_SHLD, L), "S", -64, 34, INK),
        ((geo.X_SHLD, L), "S′", 18, 34, INK),
        (Hh, "H", 18, 22, INK), (Hm, "H′", -74, 22, INK),
    ]:
        s += _dot(TX, p, lab, dx, dy, col)

    # 7 图上说明
    s.append(_tx(OX + Hh[0] + 34, OY - L * 0.46, "前片门襟边（模板原边）", 21, INK))
    s.append(_tx(OX - 26, OY - L * 0.34, "后中缝", 20, GRAY, "end"))
    s.append(_tx(56, 300, "后片整片外轮廓（后片半 ×2 镜像）", 21, GRAY))
    s.append(_tx(OX + 190, 250, "领子上缘＝直线折线 B→A→A′→B′（11:48 令）；红线＝圆心角 60° 的新领口弧", 21, BLUE))
    s.append(_seg(TX, (-HW, -70), (HW, -70), 1.0, color=GRAY))
    s.append(_seg(TX, (-HW, -60), (-HW, -80), 1.0, color=GRAY))
    s.append(_seg(TX, (HW, -60), (HW, -80), 1.0, color=GRAY))
    s.append(_tx(OX, OY + 116,
                 "领高＝30mm（暂取 3cm，可调）；A 在 P₁ 右上方；上领缘＝直线折线；P₁P₂＝圆心角 60° 弧（R=弦长=76.5732mm）",
                 23, BLUE, "middle"))
    s.append(_tx(OX, OY + 152,
                 "领子：起点边 P₂B → 经过 P₁A / P₁′A′ → 终点边 P₂′B′；四条宽度边各 30mm、端点全不动；领口点位见放大图",
                 21, GRAY, "middle"))
    s.append(_tx(OX, OY + 188,
                 "平铺宽 %.0f　衣长 %.0f　｜　参考图见 ref/（只作拓扑依据，不量数）；前片 / 后片 cmds 未改"
                 % (HW * 2, L), 21, GRAY, "middle"))

    # 8 100mm 标尺
    bx, by = 56, H - 56
    s.append('<g id="SCALE" stroke="%s" stroke-width="2.2" fill="none">' % INK)
    for k in range(11):
        hh = 28 if k % 5 == 0 else 15
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx + k * 100, by, bx + k * 100, by - hh))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx, by, bx + 1000, by))
    s.append('</g>')
    s.append(_tx(bx, by + 30, "100mm 校验标尺（1:1 打印后实测，误差应 ≤0.5mm）", 20, INK))
    s.append('</svg>')

    svg = os.path.join(OUT, "step4_上领子.svg")
    open(svg, "w", encoding="utf-8").write("\n".join(s))
    png = os.path.join(OUT, "step4_上领子.png")
    return svg, png, make_png(svg, png)


def make_zoom_step4():
    """V 附近 4× 局部放大：把上领缘直线折线、60° 弧下缘、上窄下宽的竖起领子看清楚。
    上领缘最高点是 A/A′ 的 y=799.55（无 827 弧顶），故视窗回到 y1=850、H=820。"""
    k = 4.0
    x0, y1 = -140.0, 850.0
    W, H = 1400, 820

    def TX(q):
        return (70 + (q[0] - x0) * k, 70 + (y1 - q[1]) * k)

    cp = CP
    L = geo.V[1]
    V = geo.V
    s = _head(W, H, "第 4 步 · 领口局部放大（4×）· 上领缘直线折线", [
        "蓝＝领子上缘直线折线 B→A→A′→B′ + 四条 30mm 宽度边；红＝第 3 步新领口 60° 圆弧（下缘，不重复描）",
        "红弧：圆心角 60° ⇒ R=弦长=76.5732mm、圆心 (%.3f, %.3f)、凹向下摆；左片圆心镜像、两段在中缝 y≈722.80 相交"
        % (RIGHT["center"][0], RIGHT["center"][1]),
        "11:48 修正：P₁P₂ 改 60° 弧、A 依然右上角、上领缘采用直线；A/A′ 竖起在顶边之上 29.55mm",
    ])
    # 顶边（中间两段旧边虚线）
    s.append(_seg(TX, (-140, L), (140, L), 2.2))
    s.append(_seg(TX, (cp["P1"][0], L), V, 2.2, "14 10"))
    s.append(_seg(TX, V, (cp["P1p"][0], L), 2.2, "14 10"))
    # 后中缝
    s.append(_seg(TX, (0, 700), (0, 830), 1.6, "26 14", GRAY))
    # 门襟边（局部范围内）
    xend = geo.LAP_DX * (L - 690) / L
    s.append(_seg(TX, V, cp["P2"], 2.6, "14 10"))
    s.append(_seg(TX, cp["P2"], (xend, 690), 2.6))
    s.append(_seg(TX, V, cp["P2p"], 2.6, "14 10"))
    s.append(_seg(TX, cp["P2p"], (-xend, 690), 2.6))
    # 领子：上领缘直线折线 + 四条宽度边
    s.append(_poly(TX, cp["upper_path"], 3.4, BLUE))
    for a, b in cp["width_edges"]:
        s.append(_seg(TX, a, b, 3.0, color=BLUE))
    # 新领口：两条 60° 圆弧（红色实线）
    s.append(_poly(TX, RIGHT["samples"], 4.2, RED))
    s.append(_poly(TX, LEFT["samples"], 4.2, RED))

    # 8 个点位：A/A′ 在顶边之上，dy 保持 30 不压线；其余沿用旧偏移
    for p, lab, dx, dy, col in [
        (V, "V", 16, -30, INK),
        (cp["P1"], "P₁", -116, 42, RED), (cp["P1p"], "P₁′", 26, 42, RED),
        (cp["P2"], "P₂", 28, 40, RED), (cp["P2p"], "P₂′", -116, 40, RED),
        (cp["A"], "A", -104, 30, BLUE), (cp["Ap"], "A′", 26, 30, BLUE),
        (cp["B"], "B", 46, -22, BLUE), (cp["Bp"], "B′", -122, -22, BLUE),
    ]:
        s += _dot(TX, p, lab, dx, dy, col, rad=8)

    s.append(_tx(70, 752, "P₁A = P₂B = P₁′A′ = P₂′B′ = 30mm（领高，暂取 3cm）；蓝带＝等高、一条连续、竖起", 23, BLUE))
    s.append(_tx(70, 788,
                 "A = P₁ + 30·mirror(w)（P₁ 右上方）；B = V + 20·u 仍在直线 HP₂ 上（非线段）；上领缘＝直线折线",
                 20, GRAY))
    s.append('</svg>')
    svg = os.path.join(OUT, "step4_领口放大.svg")
    open(svg, "w", encoding="utf-8").write("\n".join(s))
    png = os.path.join(OUT, "step4_领口放大.png")
    return svg, png, make_png(svg, png)


def main():
    print("=== 第 4 步自检（上领缘直线折线 · A 在 P₁ 右上方 · P₁P₂ 60° 弧） ===")
    fails = []
    for name, ok, extra in selftest():
        print("  %s %s %s" % ("PASS" if ok else "FAIL", name, extra))
        if not ok:
            fails.append(name)
    if fails:
        print("!! 自检未过：", fails)
        return 1

    cp = CP
    seam_y = RIGHT["center"][1] - math.sqrt(geo.ARC_R ** 2 - RIGHT["center"][0] ** 2)
    data = {
        "step": 4,
        "action": "上领子（用户 2026-11-11 11:48 修正：P1P2 为圆心角 60° 的弧，A 依然右上角，上领缘采用直线）",
        "collar_height_mm": cp["h"],
        "collar_height_note": "P₁A 为领高＝宽度边长，暂取 3cm = 30mm（geo.COLLAR_H 可调）",
        "upper_edge": {
            "user_command": "11:48：上领缘采用直线（撤销 01:13 的三段圆弧）",
            "mode": "B→A→A′→B′ 三段直线折线；不是圆弧、不是同心弧、不是平移弧",
            "endpoints_unchanged": True,
            "straight_path": [list(q) for q in cp["upper_path"]],
            "why": "用户判 01:13 三段圆弧上缘「前领凹凸性错误」，并给三张实物参考图（ref/）后定「上领缘采用直线」",
            "reference": "ref/ 三张实物照只作拓扑依据（等宽、边缘以直线段为主的竖起带），不量取任何数值",
        },
        "neckline_arc_60": {
            "user_command": "11:48：P1P2 为圆心角 60 度的弧",
            "sweep_deg": RIGHT["sweep_deg"],
            "radius_mm": geo.ARC_R,
            "radius_source": "c = 2R·sin(60°/2) = R ⇒ R = 弦长 = 76.5732mm（不再是 VP₁=50、圆心不再是 V）",
            "center": [round(v, 6) for v in RIGHT["center"]],
            "center_left": [round(v, 6) for v in LEFT["center"]],
            "center_reason": "圆心在弦中垂线上、距弦中点 R·cos30°；取弧中点 y 较小的一支＝凹向下摆",
            "right_polar_deg": [RIGHT["start_deg"], RIGHT["end_deg"]],
            "left_polar_deg": [LEFT["start_deg"], LEFT["end_deg"]],
            "chord_mm": RIGHT["chord"],
            "arc_length_mm": RIGHT["arc_length"],
            "sagitta_mm": RIGHT["sagitta"],
            "apex": [round(v, 6) for v in RIGHT["apex"]],
            "seam_cross_y_mm": round(seam_y, 6),
            "concavity": "凹向下摆（沿用第 3 步 23:23 口径）；两段圆心互为镜像、不共圆、在中缝相交",
        },
        "band": {
            "start_edge": "P₂B", "via_edges": ["P₁A", "P₁′A′"], "end_edge": "P₂′B′",
            "lower": "P₂→P₁→P₁′→P₂′（第 3 步两条圆心角 60° 的新领口圆弧 + 顶边中段直线）",
            "upper": "B→A→A′→B′（直线折线，一条连续、等高、竖起）",
        },
        "points": {k: [round(v, 6) for v in cp[k]]
                   for k in ("A", "B", "Ap", "Bp", "P1", "P2", "P1p", "P2p")},
        "B_on_line": "直线 HP₂（不是线段 H→P₂）：B = V + 20·u，落在 P₂ 之上",
        "rise_above_top_mm": round(cp["rise_above_top"], 6),
        "AA_mm": round(cp["AA"], 6),
        "mirror_sync": True,
        "geometry_changed": False,
        "note": "11:48 只改两处线型/弧参数（第 3 步圆心角 60°、上领缘直线折线）；四个端点、四条 30mm 宽度边、P₁/P₂ 位置全不动；前片/后片 cmds 与模板逐项相同；未推断第 5 步。",
    }
    json.dump(data, open(os.path.join(OUT, "step4.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    svg, png, res = make_flat_step4()
    print("\n=== 产物 ===")
    print("  ", svg, "|", png, "|", res)
    zsvg, zpng, zres = make_zoom_step4()
    print("  ", zsvg, "|", zpng, "|", zres)
    print("  ", os.path.join(OUT, "step4.json"))
    print("\nA = %s  A′ = %s  B = %s  B′ = %s"
          % (cp["A"], cp["Ap"], cp["B"], cp["Bp"]))
    print("上领缘＝直线折线 B→A→A′→B′（%d 点，无弧中点）" % len(cp["upper_path"]))
    print("竖起：A / A′ 在顶边 y=%.0f 之上 %.4f mm；A—A′ = %.4f mm（下缘中段 %.0f mm，上窄下宽）"
          % (geo.V[1], cp["rise_above_top"], cp["AA"], math.dist(cp["P1"], cp["P1p"])))
    print("第 3 步 P₁P₂＝圆心角 %.0f° 弧：R=弦长=%.4f，圆心=(%.4f, %.4f)，弧长 %.4f / 矢高 %.4f mm"
          % (geo.ARC_SWEEP_DEG, geo.ARC_R, RIGHT["center"][0], RIGHT["center"][1],
             RIGHT["arc_length"], RIGHT["sagitta"]))
    print("两段弧在中缝 x=0 相交于 y=%.4f（左右镜像的几何必然，非 bug）" % seam_y)
    return 0


if __name__ == "__main__":
    sys.exit(main())
