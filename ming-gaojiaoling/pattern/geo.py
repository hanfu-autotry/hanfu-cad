# -*- coding: utf-8 -*-
"""
明制高交领 · 横卧领 · 版型几何
================================

依据（按优先级）：
  1. 用户手绘标准图（本案夹具，数值见 CASE 注释）—— 裁片口径以它为准
  2. kit/sources/04-直交一体_术语证据/证据/4_谱系_直领对襟与交领交襟.jpg（结构谱系）
  3. ref/本案/ 两张明墓实测图（形态参照：横卧领、斜襟、起翘、接袖位置）

── 结构（谱系：直领对襟 → 续衽 → 交领交襟；用户 2026-11-06 指正）──

  **底子是直领对襟**：前片左右各一，**前中缝竖直居中**，左右完全对称。
  **交襟不是把前片剪斜**，而是另出「续衽」沿**竖直前中缝直拼**（＋137 越中）；
  续衽的外缘才是斜的，那条边就是门襟边。前片是**一片**，续衽在片内用一条标记线分开。

     后片半 ×2   0 → 585，后中连折
     前片   ×2   0 → 585（另带 −137 的续衽），前中缝 x=0 竖直
     接袖   ×4   840 → 1105，每侧 2 片，沿袖底缝合成袖筒
     领缘条 ×1   1908 × 40 —— **横卧领**：40 宽平贴领口一圈，不立起

── 尺寸（标准图，mm）──

  后中长 845 ／ 腋深 328（腋点高 517）／ 摆半宽 585 ／ 起翘 80
  肩点 570 ／ 衣身袖长 270（→ 接袖缝 840）／ 袖根 208 ／ 接袖长 265（→ 袖口 1105，通袖 2210）
  袖口 130 ／ 前单边摆宽 722（＝585 ＋ 续衽越中 137）／ 门襟 276（肩线 → 领口底 569）
  开领条宽 98 ／ 领缘条 1908×40

单位 mm，净版（未含缝份）。坐标：x=0 前中/后中，y=0 下摆，y 向上。
"""
import copy
import sys
import io
import json
import math
import os

# 前片领口（按用户 2026-11-06 21:32 在图上画的那条线量的）
XUREN_W = 180.0        # 续衽越中宽度（拼在前中缝外侧）
UPPER_LIFT = 68.0      # 上边界 l 向上平移成 l' 的量
NECKLINE_W = 110.0     # 内领缘：距领缘边往里的宽度（用户给 11cm 试）
FRONT_NECK_W = 65.0      # 领口点 P：130 → 115 → 95 → 65（再左移 30）
FRONT_NECK_D = 130.0

CASE = dict(
    name="本案",
    L=845.0,          # 后中长（肩线 → 下摆）
    DARM=328.0,       # 腋深
    HALF=585.0,       # 摆半宽（后片）
    RISE=80.0,        # 下摆起翘
    X_SH=570.0,       # 肩点（＝衣身袖起点）
    SLV=270.0,        # 衣身袖长（肩点 → 接袖缝）
    SEAM_H=208.0,     # 袖根（接袖缝处袖高）
    JS=265.0,         # 接袖长
    CUF=130.0,        # 袖口高
    NECKW=98.0,       # 开领条宽（领口通口）
    LAP=276.0,        # 门襟（肩线 → 领口底）
    XUREN=137.0,      # 续衽越中（前单边摆 722 － 后摆半 585）
    COL_L=1908.0,     # 领缘条总长
    COL_W=40.0,       # 领缘条宽（横卧领的领高）
    R_ARM=70.0,       # 腋下圆角（模板 jiexiu 的 R=70 ）
    TIE_L=(450.0, 310.0),
    TIE_W=20.0,
    BACKDIP=40.0,     # 后领口低落
)


def derive(p):
    d = dict(p)
    d["X_ARM"] = p["X_SH"] - 152.0                 # 腋点半宽 418（标准图腋点）
    d["Y_ARM"] = p["L"] - p["DARM"]                # 腋点高 517
    d["X_JS"] = p["X_SH"] + p["SLV"]               # 接袖缝 840
    d["X_CUFF"] = d["X_JS"] + p["JS"]              # 袖口 1105
    d["S"] = 2.0 * d["X_CUFF"]                     # 通袖 2210
    d["Y_ARM_BOT"] = p["L"] - p["SEAM_H"]          # 接袖缝处袖底高 637
    d["Y_CUF_BOT"] = p["L"] - p["CUF"]             # 袖口下缘高 715
    d["Y_NECKBOT"] = p["L"] - p["LAP"]             # 领口底 569
    d["HALF_NW"] = p["NECKW"] / 2.0                # 颈侧点 49
    d["X_FRONT"] = p["HALF"] + p["XUREN"]          # 前单边摆 722（含续衽）
    return d


K = 0.5522847498307936


def hem_arc(x_end, rise, n=3):
    """下摆起翘弧：(0,0) → (x_end,rise)，(0,0) 处切线水平。返回 [(A,C1,C2,B), ...]"""
    rc = (x_end ** 2 + rise ** 2) / (2.0 * rise)
    th1 = math.asin(min(1.0, x_end / rc))

    def pt(th):
        return (rc * math.sin(th), rc - rc * math.cos(th))

    segs, dth = [], th1 / n
    for i in range(n):
        a, b = i * dth, (i + 1) * dth
        p0, p3 = pt(a), pt(b)
        k = 4.0 / 3.0 * math.tan(dth / 4.0) * rc
        segs.append((p0, (p0[0] + k * math.cos(a), p0[1] + k * math.sin(a)),
                     (p3[0] - k * math.cos(b), p3[1] - k * math.sin(b)), p3))
    return segs


def hem_y(x, x_end, rise):
    rc = (x_end ** 2 + rise ** 2) / (2.0 * rise)
    return rc - math.sqrt(max(0.0, rc * rc - x * x))


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n)


def _blend(A, tA, B, tB, k=0.92):
    """G1 三次混合：两端切线分别与相邻段一致 → 无折角（模板 jiexiu 的做法）"""
    d = math.hypot(B[0] - A[0], B[1] - A[1]) / 3.0 * k
    return ["C", [A[0] + tA[0] * d, A[1] + tA[1] * d], [B[0] - tB[0] * d, B[1] - tB[1] * d], list(B)]


def mirror(cmds):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
        else:
            out.append([c[0]] + [[-pt[0], pt[1]] for pt in c[1:]])
    return out


TPLALL = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "_template_all.json"), encoding="utf-8"))

TPL = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "_template_back.json"), encoding="utf-8"))


def arc3(A, B, C, k=0.5523):
    """过三点的圆弧 → 贝塞尔段列表（A→C，且经过 B）"""
    ax, ay = A; bx, by = B; cx, cy = C
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:                                   # 三点共线 → 直接直线
        return [["L", [cx, cy]]]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    R = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    a1 = math.atan2(by - uy, bx - ux)
    a2 = math.atan2(cy - uy, cx - ux)

    def norm(a):                                        # 归一到 (0, 2π)
        while a < 0:
            a += 2 * math.pi
        return a

    a0n, a1n, a2n = norm(a0), norm(a1), norm(a2)
    ccw = (norm(a2n - a0n) > norm(a1n - a0n))           # B 是否在 A→C 的逆时针弧上
    sweep = norm(a2n - a0n) if ccw else -norm(a0n - a2n)
    n = 4
    angs = [a0 + sweep * i / n for i in range(n)] + [a0 + sweep]   # 末角强制＝终点角
    out, prev = [], a0
    for i in range(1, n + 1):
        nxt = angs[i]
        dt = nxt - prev
        kk = 4.0 / 3.0 * math.tan(dt / 4.0) * R
        p0 = (ux + R * math.cos(prev), uy + R * math.sin(prev))
        p3 = (ux + R * math.cos(nxt), uy + R * math.sin(nxt))
        c1 = (p0[0] - kk * math.sin(prev), p0[1] + kk * math.cos(prev))
        c2 = (p3[0] + kk * math.sin(nxt), p3[1] - kk * math.cos(nxt))
        out.append(["C", [c1[0], c1[1]], [c2[0], c2[1]], [p3[0], p3[1]]])
        prev = nxt
    out[-1][3] = [cx, cy]                                           # 收尾咬死终点
    return out


def _arc_prev(arc, start):
    """arc 列表里最后一段的起点"""
    if len(arc) >= 2:
        return tuple(arc[-2][3])
    return start


def _segs(cmds):
    """cmds → (起点, [(L,A,B) / (C,A,C1,C2,B), ...])"""
    cur = start = None
    segs = []
    for c in cmds:
        if c[0] == "M":
            cur = start = tuple(c[1])
        elif c[0] == "L":
            segs.append(("L", cur, tuple(c[1]))); cur = tuple(c[1])
        elif c[0] == "C":
            segs.append(("C", cur, tuple(c[1]), tuple(c[2]), tuple(c[3]))); cur = tuple(c[3])
        elif c[0] == "Z":
            segs.append(("L", cur, start)); cur = start
    return start, segs


def reverse_cmds(cmds):
    start, segs = _segs(cmds)
    end = segs[-1][-1]
    out = [["M", list(end)]]
    for sg in reversed(segs):
        if sg[0] == "L":
            out.append(["L", list(sg[1])])
        else:
            out.append(["C", list(sg[3]), list(sg[2]), list(sg[1])])
    out.pop()                      # 末点＝起点，交给 Z
    out.append(["Z"])
    return out


def reverse_open(cmds):
    """把一段不闭合路径反向（不补 Z）"""
    cur = start = None
    segs = []
    for c in cmds:
        if c[0] == "M":
            cur = start = tuple(c[1])
        elif c[0] == "L":
            segs.append(("L", cur, tuple(c[1]))); cur = tuple(c[1])
        elif c[0] == "C":
            segs.append(("C", cur, tuple(c[1]), tuple(c[2]), tuple(c[3]))); cur = tuple(c[3])
        elif c[0] == "Z":
            segs.append(("L", cur, start)); cur = start
    end = segs[-1][-1]
    out = [["M", list(end)]]
    for sg in reversed(segs):
        if sg[0] == "L":
            out.append(["L", list(sg[1])])
        else:
            out.append(["C", list(sg[3]), list(sg[2]), list(sg[1])])
    return out


def pieces(d):
    """裁片表：只出**前片**（自带续衽）。

    S1 / S2 是**下摆**上的两段：S2 = 前中往右那一段，S1 = 前中往左（续衽下）那一段。
    两段互为**沿前中缝的镜像**，所以天然等长 —— 不量、不算。
    续衽的外缘是从领口底一路弯到下摆的那条曲线（图上手画那条）。
    """
    P = TPL["params"]
    L, HALF = P["L"], P["W_HEM"] / 2.0
    NWF, NDF = FRONT_NECK_W, FRONT_NECK_D
    XUR = HALF                     # 续衽越中＝摆半宽 → 下摆左右两段对称，S1 恒等于 S2
    y0 = L - NDF
    k = 0.5523

    back = [list(c) if c[0] == "Z" else [c[0]] + [list(pt) for pt in c[1:]] for c in TPL["cmds"]]
    hem_c = [c for c in back if c[0] == "C"][0]          # 模板摆弧 P0(0,0) C1 C2 P3
    M1 = (-hem_c[1][0], hem_c[1][1]); M2 = (-hem_c[2][0], hem_c[2][1])
    M3 = (-hem_c[3][0], hem_c[3][1])

    def hem_split(w):
        """镜像摆弧上 x=-w 处的点（de Casteljau 截取），返回 (L1,Q1,Spt,t)"""
        lo, hi = 0.0, 1.0
        for _ in range(60):
            tt = (lo + hi) / 2.0; mt = 1 - tt
            x = 3 * mt * mt * tt * M1[0] + 3 * mt * tt * tt * M2[0] + tt ** 3 * M3[0]
            if -x < w:
                lo = tt
            else:
                hi = tt
        t = (lo + hi) / 2.0
        A0 = (0.0, 0.0)
        p1 = (A0[0] + (M1[0] - A0[0]) * t, A0[1] + (M1[1] - A0[1]) * t)
        p2 = (M1[0] + (M2[0] - M1[0]) * t, M1[1] + (M2[1] - M1[1]) * t)
        p3 = (M2[0] + (M3[0] - M2[0]) * t, M2[1] + (M3[1] - M2[1]) * t)
        q1 = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
        q2 = (p2[0] + (p3[0] - p2[0]) * t, p2[1] + (p3[1] - p2[1]) * t)
        sp = (q1[0] + (q2[0] - q1[0]) * t, q1[1] + (q2[1] - q1[1]) * t)
        return p1, q1, sp

    L1, Q1, Spt = hem_split(XUR)
    h = Spt[1]                                     # 摆弧在 x=-XUR 处的高度

    # 原摆弧上 x=+XUR 的点（S2 的右端），用同样的 de Casteljau
    def hem_at(w, mir):
        C1 = (-hem_c[1][0], hem_c[1][1]) if mir else (hem_c[1][0], hem_c[1][1])
        C2 = (-hem_c[2][0], hem_c[2][1]) if mir else (hem_c[2][0], hem_c[2][1])
        C3 = (-hem_c[3][0], hem_c[3][1]) if mir else (hem_c[3][0], hem_c[3][1])
        lo2, hi2 = 0.0, 1.0
        for _ in range(60):
            tt = (lo2 + hi2) / 2.0; mt = 1 - tt
            xx = 3 * mt * mt * tt * C1[0] + 3 * mt * tt * tt * C2[0] + tt ** 3 * C3[0]
            if (xx if mir else -xx) < w:
                lo2 = tt
            else:
                hi2 = tt
        tt = (lo2 + hi2) / 2.0; mt = 1 - tt
        return (3 * mt * mt * tt * C1[0] + 3 * mt * tt * tt * C2[0] + tt ** 3 * C3[0],
                3 * mt * mt * tt * C1[1] + 3 * mt * tt * tt * C2[1] + tt ** 3 * C3[1])

    P2r = hem_at(XUR, False)                       # (≈+180, ≈9.5)

    # 领口弧（右半）
    Rc1, Rc2 = (k * NWF, y0), (NWF, L - k * NDF)
    # A1 右边顶点＝**腋下转直线的那个点**（模板里侧缝直线段的末端 A_a），A2 取它的镜像
    # A1 的边界是分段函数：侧缝直线 → 腋下 G1 圆角 → 袖底直线 …
    # A2 ＝ A1 沿前中缝逐段镜像，所以 A2 的边界同样是分段函数，不能拉成一条直线
    seen_c, A_a, blend = False, None, None
    for i2, c in enumerate(back):
        if c[0] == "C" and i2 > 0 and back[i2 - 1][0] == "C":
            blend = c                                  # 摆弧之后的第二个 C ＝ 腋下 G1 圆角
            break
    for i2, c in enumerate(back):
        if c[0] == "L" and blend is not None and c[1] == list(blend[1])[:0]:
            pass
    # 直接按照模板顺序取：back = [M, C(摆弧), L(A_a), C(腋圆角), L(袖底), L(袖口), L(肩点), L(领口), L(0,L), Z]
    A_a = tuple(back[2][1])
    bl_c1, bl_c2, B_a = tuple(back[3][1]), tuple(back[3][2]), tuple(back[3][3])

    # 左边界（A2）：(-摆角) → (-A_a) 直线 → 圆角镜像 → (-B_a) → 领口底
    # P1＝腋下转直线点（镜像侧）；P2＝圆弧与前中缝的交点（＝领口底）；两者与颈侧点同一条圆弧
    front = [["M", [-XUR, h]]]                               # ① 起点＝摆角（l 起点）
    # ② 按用户定的点位重建，并把**续衽拆成独立一片**
    #    P2＝外缘上端；P1＝l∩中缝(0,y0)；l'＝l 竖直上移；P'2＝外缘延长线∩l'；P'1＝(0,y0+LIFT)
    heel = (-P["W_HEM"] / 2.0, P["HEM_RISE"])
    P2 = (-A_a[0], A_a[1])
    P1 = (0.0, y0)
    PK = (NWF, L)
    LIFT = UPPER_LIFT
    ax_, ay_ = P2; bx_, by_ = P1; cx_, cy_ = PK
    dd = 2.0 * (ax_ * (by_ - cy_) + bx_ * (cy_ - ay_) + cx_ * (ay_ - by_))
    ox = ((ax_ * ax_ + ay_ * ay_) * (by_ - cy_) + (bx_ * bx_ + by_ * by_) * (cy_ - ay_) + (cx_ * cx_ + cy_ * cy_) * (ay_ - by_)) / dd
    oy = ((ax_ * ax_ + ay_ * ay_) * (cx_ - bx_) + (bx_ * bx_ + by_ * by_) * (ax_ - cx_) + (cx_ * cx_ + cy_ * cy_) * (bx_ - ax_)) / dd
    R = math.hypot(ax_ - ox, ay_ - oy)
    ox2, oy2 = ox, oy + LIFT
    P1p = (P1[0], P1[1] + LIFT)
    dx, dy = P2[0] - heel[0], P2[1] - heel[1]
    nn = math.hypot(dx, dy); ux_, uy_ = dx / nn, dy / nn
    bq = 2.0 * ((heel[0] - ox2) * ux_ + (heel[1] - oy2) * uy_)
    cq = (heel[0] - ox2) ** 2 + (heel[1] - oy2) ** 2 - R ** 2
    disc = bq * bq - 4 * cq
    P2p = P2
    if disc >= 0:
        t1 = (-bq + math.sqrt(disc)) / 2.0
        t2 = (-bq - math.sqrt(disc)) / 2.0
        cand = [(heel[0] + ux_ * t1, heel[1] + uy_ * t1), (heel[0] + ux_ * t2, heel[1] + uy_ * t2)]
        cand.sort(key=lambda q: math.hypot(q[0] - P2[0], q[1] - P2[1]))
        P2p = cand[0]

    def mid_arc(o, rr, A, B):
        aA = math.atan2(A[1] - o[1], A[0] - o[0])
        aB = math.atan2(B[1] - o[1], B[0] - o[0])
        if aB - aA > math.pi:
            aB -= 2 * math.pi
        elif aA - aB > math.pi:
            aB += 2 * math.pi
        am = (aA + aB) / 2.0
        return (o[0] + rr * math.cos(am), o[1] + rr * math.sin(am))

    # —— 三块拼起来：左外缘(l') / 前中段 / 右侧主体 ——
    l_arc = arc3(P1, mid_arc((ox, oy), R, P1, PK), PK)          # l：P1 → 颈侧点
    lp_arc = arc3(P2p, mid_arc((ox2, oy2), R, P2p, P1p), P1p)    # l'：P'2 → P'1
    cut = None
    for i2, c in enumerate(back):
        if c[0] == "L" and abs(c[1][0] - P["X_SHLD"]) < 1e-6 and abs(c[1][1] - L) < 1e-6:
            cut = i2
    right_body = [["L", [P["X_SHLD"], L]]] + reverse_open(back[:cut + 1])[1:]   # 肩线→袖→腋→侧缝→摆→摆弧→(0,0)
    left_hem = ["C", [-hem_c[1][0], hem_c[1][1]], [-hem_c[2][0], hem_c[2][1]], [heel[0], heel[1]]]

    # 01 前片（中缝右边）：左缘＝中缝（x=0，实线）
    # 前片：左缘只到 P1 (0,y0)，不再往上有那段「冒尖」的线
    right = [["M", [0.0, y0]]] + l_arc + right_body + [["Z"]]
    # 02 续衽（中缝左边）：右缘＝中缝
    left = [["M", [heel[0], heel[1]]], ["L", [P2[0], P2[1]]], ["L", [P2p[0], P2p[1]]]]
    left += lp_arc + [["L", [P1p[0], P1p[1]]], ["L", [0.0, 0.0]]] + [left_hem] + [["Z"]]
    # 外襟整片（供内襟镜像）
    whole = [["M", [heel[0], heel[1]]], ["L", [P2[0], P2[1]]], ["L", [P2p[0], P2p[1]]]]
    whole += lp_arc + [["L", [P1[0], P1[1]]]] + l_arc + right_body + [left_hem] + [["Z"]]

    wai_front = dict(name="前片（中缝右边）", qty=1, cmds=right, grain=[0, 1],
                     notches=[[0.0, y0]], dims=[], aux=[],
                     note="左缘＝中缝（x=0，实线）；领口/肩/袖/侧缝/摆照旧")
    # l（P2 → P1）在续衽里作辅助线，用虚线标出
    a_p2 = math.atan2(P2[1] - oy, P2[0] - ox)
    a_p1 = math.atan2(P1[1] - oy, P1[0] - ox)
    if a_p1 - a_p2 > math.pi:
        a_p1 -= 2 * math.pi
    elif a_p2 - a_p1 > math.pi:
        a_p1 += 2 * math.pi
    l_mark = [(ox + R * math.cos(a_p2 + (a_p1 - a_p2) * i / 16.0),
               oy + R * math.sin(a_p2 + (a_p1 - a_p2) * i / 16.0)) for i in range(17)]
    xur_piece = dict(name="续衽（中缝左边）", qty=1, cmds=left, grain=[0, 1],
                     notches=[[0.0, 0.0]], dims=[], aux=[], marks=[l_mark],
                     note="右缘＝中缝；左外缘 摆角→P2→P'2→l'→P'1；虚线 l 为辅助线")
    # 前片 / 续衽 / 内襟（前片镜像） / 内襟续衽（续衽镜像） / 后片
    back_piece = dict(name="后片（半·模板原样）", qty=2,
                      cmds=[list(c) if c[0] == "Z" else [c[0]] + [list(pt) for pt in c[1:]]
                            for c in TPL["cmds"]],
                      grain=[0, 1], notches=TPL.get("notches") or [],
                      dims=[("L", [0.0, 0.0], [0.0, L], "后中长 %.0f" % L)],
                      note="jiexiu 模板原样；×2 镜像")
    nei_piece = mirror_piece(dict(wai_front))
    nei_piece["name"] = "内襟（前片镜像）"
    nei_piece["qty"] = 1
    nei_xur = mirror_piece(dict(xur_piece))
    nei_xur["name"] = "内襟续衽（续衽镜像）"
    nei_xur["qty"] = 1
    out = [wai_front, nei_piece, xur_piece, nei_xur, back_piece]

    # 06 领缘条（高交领·全衣一条，用户 2026-11-08 定）
    # 约束：领宽恒＝AA′＝PB＝97.05141（B 落在中缝而重合，故左右两段连成一条带子）。
    # 长度由领口线反推：左右两段 L 弧 ＋ 后领水平段（＝2×颈侧点横坐标）。
    aA = math.atan2(P2[1] - oy, P2[0] - ox)
    aP = math.atan2(PK[1] - oy, PK[0] - ox)
    sweep = aP - aA
    if sweep < 0:
        sweep += 2.0 * math.pi
    arc_L = R * sweep
    back_neck = 2.0 * NWF
    collar_len = 2.0 * arc_L + back_neck
    collar_w = 97.05141
    out.append(dict(
        name="领缘条（高交领·全衣一条）", qty=1,
        cmds=[["M", [0.0, 0.0]], ["L", [collar_len, 0.0]],
              ["L", [collar_len, collar_w]], ["L", [0.0, collar_w]], ["Z"]],
        grain=[1, 0], notches=[],
        dims=[("L", [0.0, 0.0], [collar_len, 0.0], "领条长 %.1f" % collar_len),
              ("L", [collar_len, 0.0], [collar_len, collar_w], "领宽 %.1f" % collar_w)],
        note="反推：长＝2×L弧(%.1f)＋后领段(%.1f)＝%.1f；宽＝AA′＝PB＝%.1f（B 重合）"
             % (arc_L, back_neck, collar_len, collar_w)))
    return out
def mirror_piece(p):
    """整片镜像（画左片，和参考图同向）"""
    def mx(cmds):
        return mirror(cmds)
    p = dict(p)
    p["cmds"] = mx(p["cmds"])
    p["notches"] = [[-n[0], n[1]] for n in p.get("notches") or []]
    p["marks"] = [[[-q[0], q[1]] for q in mk] for mk in (p.get("marks") or [])]
    p["aux"] = [[[-q[0], q[1]] for q in mk] for mk in (p.get("aux") or [])]
    p["dims"] = [(dm[0], [-dm[1][0], dm[1][1]], [-dm[2][0], dm[2][1]], dm[3])
                 for dm in (p.get("dims") or [])]
    return p


def lead_edge(d, w=None, n=26):
    """领缘条内侧线（沿领缘边往衣内让 98）—— 图上「开领条宽」就是这条带子"""
    w = w if w is not None else d["NECKW"]
    XS, L, YNB = d["X_SH"], d["L"], d["Y_NECKBOT"]
    c1 = (0.0, YNB + 0.55 * d["LAP"])
    c2 = (XS - 0.55 * XS, L)
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        mt = 1 - t
        x = mt ** 3 * 0.0 + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * XS
        y = mt ** 3 * YNB + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * L
        # 法线朝衣内（+x）
        j2 = min(len(pts), n)
        pts.append([x, y])
    out = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        nn = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / nn, tx / nn
        if nx < 0:
            nx, ny = -nx, -ny
        out.append([p[0] + nx * w, p[1] + ny * w])
    return out


def bbox(cmds):
    xs, ys = [], []
    for c in cmds:
        if c[0] in ("M", "L"):
            xs.append(c[1][0]); ys.append(c[1][1])
        elif c[0] in ("C", "Q"):
            for pt in c[1:]:
                xs.append(pt[0]); ys.append(pt[1])
    return min(xs), min(ys), max(xs), max(ys)
