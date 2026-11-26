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
  **交襟不是把前片剪斜**，而是另出「续衽」沿**竖直前中缝**拼上去（＋137 越中）。

  **续衽是独立一片**，上缘 **L′ 由领条外缘派生**（2026-11-26 现行构造，非旧版）：
  过 `P1′`（＝L ∩ 中缝，(0,715)）作平行于水平面的直线，截领条外缘 `Γ_C`（|X−o| = R−C）得 X；
  `L′ = Γ_C 弧（A′→X）＋ 水平段（X→P1′）`，所以 C 一变、L′ 跟着变；
  片角 `A′` 是 `HH1 ∩ Γ_C`，与领条端面 `[A, A′]` 的上端同一点。
  续衽左缘 `HH1` 平行于原外缘，位置由 `H`（l′ 定位弧上离 P2′ `XUR_H`）定，落到下摆得 `H1`。
  （把「续衽上端接到领条外缘」称作**高位接衽**是工艺层面的说法，只写在 `使用说明.md` / `构造分步图说.md`，
   几何代码只认上面这几条数学定义。）

     后片半 ×2   0 → 585，后中连折（直接调 hanfu-jiexiu 的构造）
     前片   ×2   前中缝 x=0 竖直；上缘＝领口线 L 弧：(0,715) → (65,845)
     续衽   ×2   中缝左边；上缘＝L′（领条外缘弧 A′→X ＋ 水平段 X→P1′）；左缘＝HH1（A′→H1）
     领缘条 ×1   1448.5 × 86.7 —— 高交领一条带：内缘＝L 弧（P0→P），外缘同心 R−C，
                 端面 [A, A′] 沿 HH1，后中收成顶点 (0, 931.71)

── 尺寸（标准图，mm）──

  后中长 845 ／ 腋深 328（腋点高 517）／ 摆半宽 585 ／ 起翘 80
  肩点 570 ／ 衣身袖长 270（→ 袖缝 840）／ 袖根 208 ／ 通袖 2210
  前单边摆宽 722（＝585 ＋ 续衽越中 137）／ 门襟 276（肩线 → 领口深）
  续衽上缘 L′ 439.896（弧 331.550 ＋ 水平 108.346）／ 领条 1448.49 × 86.71

单位 mm，净版（未含缝份）。坐标：x=0 前中/后中，y=0 下摆，y 向上。
"""
import copy
import sys
import io
import json
import math
import os

# 后片不另写一份几何：直接调接袖版（谱系父）的纯函数构造。
# 「取用父版型的片」＝调用它的构造，不复制源码；父版型改结构，这里跟着改。
_JX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "hanfu-jiexiu", "pattern")
if _JX_DIR not in sys.path:
    sys.path.insert(0, _JX_DIR)
import construct as JX          # noqa: E402

# 前片领口（按用户 2026-11-06 21:32 在图上画的那条线量的）
XUREN_W = 180.0        # 续衽越中宽度（拼在前中缝外侧）
UPPER_LIFT = 68.0      # l′ ＝ l 竖直上移量；2026-11-26 起只用于定位 H，不再是裁片边
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
    XUR_H=20.0,       # 续衽 H 点：沿上边缘（l′ 弧）自 P2′ 向中缝方向的弧长 ＝新左边缘 HH1 的定位（标准 20）
    COL_L=1908.0,     # 旧「横卧领」领缘条总长——现为派生量（2×L 弧＋后领段），保留键位不做输入
    COL_W=40.0,       # 旧「横卧领」领条宽——现为反解量（86.711），保留键位不做输入
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


def jiexiu_params(d):
    """把明制的 CASE 翻成接袖版（后片谱系父）的参数字典。

    口径：**SEAM_H（袖根，标准图实测）作输入**，由它反解腕口高
    —— 对应 construct.derive(seam_mode="seam")。这样袖根是硬指标，
    腕口跟着直线袖底走（差 1mm 级），不会被反过来锁死。
    """
    return dict(
        L=d["L"], W_HEM=2.0 * d["HALF"], EASE=1.0,
        X_ARM=d["X_ARM"], Y_ARM=d["Y_ARM"], X_SHLD=d["X_SH"],
        SLEEVE_LEN=d["SLV"], JS=d["JS"], CUFF=d["CUF"], WRIST=d["CUF"],
        NECK=d["NECKW"], OV=2.0 * d["XUREN"], HEM_RISE=d["RISE"],
        TILT_DEG=0.8, COL_W=d["COL_W"], SEAM_H=d["SEAM_H"],
    )


def back_half(d):
    """后片半：调父版型的构造（吃本版参数），当前 SEAM_H 驱动。"""
    return JX.back_half(JX.derive(jiexiu_params(d), "seam"))


# ── 贝塞尔链的弧长 / 截断（续衽 H 点与 H1 靠它精确定位，不用采样折线）──
def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _bz_pt(P0, C1, C2, P3, t):
    mt = 1.0 - t
    return (mt ** 3 * P0[0] + 3 * mt * mt * t * C1[0] + 3 * mt * t * t * C2[0] + t ** 3 * P3[0],
            mt ** 3 * P0[1] + 3 * mt * mt * t * C1[1] + 3 * mt * t * t * C2[1] + t ** 3 * P3[1])


def _bz_split(P0, C1, C2, P3, t):
    """de Casteljau 在 t 处切成两段，返回 (前段四点, 后段四点)；端点严格不动。"""
    p01, p12, p23 = _lerp(P0, C1, t), _lerp(C1, C2, t), _lerp(C2, P3, t)
    p012, p123 = _lerp(p01, p12, t), _lerp(p12, p23, t)
    m = _lerp(p012, p123, t)
    return (P0, p01, p012, m), (m, p123, p23, P3)


def _bz_len(P0, C1, C2, P3, n=64, t=1.0):
    """[0, t] 段弧长（弦长累加，n 段）"""
    tot, prev = 0.0, P0
    for i in range(1, n + 1):
        q = _bz_pt(P0, C1, C2, P3, t * i / float(n))
        tot += math.hypot(q[0] - prev[0], q[1] - prev[1])
        prev = q
    return tot


def _chain(start, cmds):
    """[["C",c1,c2,b], ...] → [(P0,C1,C2,P3), ...]"""
    out, cur = [], tuple(start)
    for c in cmds:
        out.append((cur, tuple(c[1]), tuple(c[2]), tuple(c[3])))
        cur = tuple(c[3])
    return out


def chain_len(start, cmds, n=64):
    return sum(_bz_len(*sg, n=n) for sg in _chain(start, cmds))


def chain_cut(start, cmds, s, n=64):
    """按弧长 s 把链切开：返回 (断点, 前段 cmds, 后段 cmds)。s=0 时前段为空。"""
    left, brk = max(0.0, float(s)), tuple(start)
    head, tail = [], []
    for P0, C1, C2, P3 in _chain(start, cmds):
        L = _bz_len(P0, C1, C2, P3, n=n)
        if left >= L - 1e-12:                       # 整段留在前段
            head.append(["C", list(C1), list(C2), list(P3)])   # C 只存 3 点，起点＝当前位置
            left -= L
            brk = P3
            continue
        if left <= 1e-12:                           # 整段归后段
            tail.append(["C", list(C1), list(C2), list(P3)])
            continue
        lo, hi = 0.0, 1.0                           # 段内二分定 t
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if _bz_len(P0, C1, C2, P3, n=n, t=mid) < left:
                lo = mid
            else:
                hi = mid
        a, b = _bz_split(P0, C1, C2, P3, (lo + hi) / 2.0)
        head.append(["C", list(a[1]), list(a[2]), list(a[3])])
        tail.append(["C", list(b[1]), list(b[2]), list(b[3])])
        brk = b[0]
        left = 0.0
    return brk, head, tail


def line_hit_bez(H, dv, P0, C1, C2, P3, n=800):
    """直线 H + t·dv 与三次贝塞尔求交（叉积扫描 + 二分）：返回 (交点, u, 前段 cmds)"""
    def f(u):
        q = _bz_pt(P0, C1, C2, P3, u)
        return (q[0] - H[0]) * dv[1] - (q[1] - H[1]) * dv[0]

    us = [i / float(n) for i in range(n + 1)]
    prev, u = f(us[0]), None
    for i in range(1, n + 1):
        cur = f(us[i])
        if abs(prev) < 1e-12 or (prev < 0) != (cur < 0):
            lo, hi = us[i - 1], us[i]
            for _ in range(60):
                mid = (lo + hi) / 2.0
                if (f(lo) < 0) != (f(mid) < 0):
                    hi = mid
                else:
                    lo = mid
            u = (lo + hi) / 2.0
            break
        prev = cur
    if u is None:
        u = 1.0
    a, _b = _bz_split(P0, C1, C2, P3, u)
    ph = _bz_pt(P0, C1, C2, P3, u)
    cmds = [["C", list(a[1]), list(a[2]), list(a[3])]] if u > 1e-12 else []   # 起点＝(0,0)
    return ph, u, cmds


def solve_collar_w(mt):
    """领宽 C 的反解（唯一未知量 C，一条方程）。

    记  o = mt["l_circle"][:2],  R = mt["l_circle"][2],  L = mt["P"][1],  k = L − oy
        Γ_L = { X : |X − o| = R }                       （P 所在 L 弧的载体圆）
        Γ_C = { X : |X − o| = R − C }                   （上缘载体圆 = Γ_L 的法向等距 C）
    约束（后片连接左右襟处的领宽 = 领条宽）：
        (0, L + C) ∈ Γ_C            ⇔            ox² + (k + C)² = (R − C)²
    闭式解：
        C = (R² − ox² − k²) / (2(k + R))
    """
    ox, oy, R = mt["l_circle"]
    k = mt["P"][1] - oy
    return (R * R - ox * ox - k * k) / (2.0 * (k + R))


def pieces(d):
    """裁片表：只出**前片**（自带续衽）。

    S1 / S2 是**下摆**上的两段：S2 = 前中往右那一段，S1 = 前中往左（续衽下）那一段。
    两段互为**沿前中缝的镜像**，所以天然等长 —— 不量、不算。
    续衽的外缘是从领口底一路弯到下摆的那条曲线（图上手画那条）。
    """
    L, HALF = d["L"], d["HALF"]
    NWF, NDF = FRONT_NECK_W, FRONT_NECK_D
    XUR = HALF                     # 续衽越中＝摆半宽 → 下摆左右两段对称，S1 恒等于 S2
    y0 = L - NDF
    k = 0.5523

    _bk = back_half(d)
    back = [list(c) if c[0] == "Z" else [c[0]] + [list(pt) for pt in c[1:]] for c in _bk["cmds"]]
    hem_c = [c for c in back if c[0] == "C"][0]          # 后片摆弧 P0(0,0) C1 C2 P3
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
    heel = (-HALF, d["RISE"])
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
    # **领口线统一为 L（2026-11-26 用户定）**：
    #   前片上缘 ＝ l 弧（P1 → PK）——不再有 P1′→n 水平段，那个曲边三角形整块删除；
    #   续衽上缘 ＝ l 弧（P1 → P0）——不再沿 l′ 冒出 68 一节，「突出被领条包裹的部分」全删；
    #   l′ 只剩一个作用：定位 H（续衽左边缘 HH1 的动点），不出现在任何裁片边上。
    #   领条只由 L 与领条宽决定，与本改动无关（端面 A＝P0 不变）。
    #   **P1′ ＝ L 与中缝所在直线（x=0）的交点**（2026-11-26 定）＝(0,715)，与 P1 重合；
    #   原来「l′ ＝ L 竖直上移 68」只留给 H 定位用，端点改名 P1L，不再叫 P1′。
    P1L = (P1[0], P1[1] + LIFT)                              # l′ 弧端点（只用来定位 H）
    l_arc = arc3(P1, mid_arc((ox, oy), R, P1, PK), PK)       # l：P1 → PK（前片上缘）
    lp_arc = arc3(P2p, mid_arc((ox2, oy2), R, P2p, P1L), P1L)    # l'：P'2 → P'1（只用于定 H）
    cut = None
    for i2, c in enumerate(back):
        if c[0] == "L" and abs(c[1][0] - d["X_SH"]) < 1e-6 and abs(c[1][1] - L) < 1e-6:
            cut = i2
    right_body = [["L", [d["X_SH"], L]]] + reverse_open(back[:cut + 1])[1:]   # 肩线→袖→腋→侧缝→摆→摆弧→(0,0)
    left_hem = ["C", [-hem_c[1][0], hem_c[1][1]], [-hem_c[2][0], hem_c[2][1]], [heel[0], heel[1]]]

    # ── 续衽左边缘 HH1（2026-11-18 用户定，原版没有这条构造）──
    #   H＝上边缘（l′ 弧）上的动点，自 P2′ 沿弧向中缝方向移动 XUR_H（标准 20mm）；
    #   HH1 恒平行于续衽原左外缘（heel→P2′），H1 落在下摆上；HH1 即**新的续衽左边缘**。
    #   被裁掉的那条（原外缘 heel→P2→P2′ ＋ 下摆 H1→heel）改画灰色辅助线，如实留档。
    H_ARC = max(0.0, float(d.get("XUR_H") or 0.0))
    H, _lp_head, lp_rest = chain_cut(P2p, lp_arc, H_ARC)      # 上边缘：P2′→H | H→P1′
    u_edge = _unit(heel, P2p)                                  # 原左外缘方向（下→上）
    H1, _u1, hem_head = line_hit_bez(H, u_edge, (0.0, 0.0),
                                     tuple(left_hem[1]), tuple(left_hem[2]), heel)
    hh1_len = math.hypot(H1[0] - H[0], H1[1] - H[1])
    hh1_perp = abs((H[0] - heel[0]) * u_edge[1] - (H[1] - heel[1]) * u_edge[0])
    # 门襟边 HH1 与领口线（l 圆）的交点 P0＝领缘沿门襟往上装到哪儿为止（定义口径）。
    # 旧版这个点就是 P2（原外缘与 l 圆相交处）；HH1 内让后交点随之内移。
    _hx, _hy = H1[0] - ox, H1[1] - oy
    _bq = 2.0 * (_hx * u_edge[0] + _hy * u_edge[1])
    _cq = _hx * _hx + _hy * _hy - R * R
    _disc = _bq * _bq - 4.0 * _cq
    P0 = None
    if _disc >= 0:
        for _t in ((-_bq + math.sqrt(_disc)) / 2.0, (-_bq - math.sqrt(_disc)) / 2.0):
            if -1e-9 <= _t <= hh1_len + 1e-9:      # 只取落在 HH1 这段上的那个
                P0 = (H1[0] + u_edge[0] * _t, H1[1] + u_edge[1] * _t)
    if P0 is None:
        P0 = P2

    # ── 续衽上缘 L′：由**领条缘**派生（2026-11-26 第二次定）──
    #   P1′ ＝ L 与中缝（x=0）的交点 ＝(0,715)；
    #   领条外缘 Γ_C ＝ { X : |X − o| = R − C }，C＝领条宽（反解）；
    #   过 P1′ 作**平行于水平面**的直线，截 Γ_C 于 X（取靠中缝那个）；
    #   L′ ＝ Γ_C 弧（A′ → X）＋ 水平段（X → P1′）。
    #   A′＝HH1∩Γ_C，就是领条端面 [A, A′] 的上端 ⇒ 续衽的左缘从 A′ 起、走 HH1 到下摆。
    P1p = (P1[0], P1[1])                                      # P1′ ＝ L ∩ 中缝（与 P1 重合）
    _CW = solve_collar_w(dict(l_circle=[ox, oy, R], P=list(PK)))
    R2 = R - _CW
    X_pt = (ox + math.sqrt(max(0.0, R2 * R2 - (P1p[1] - oy) ** 2)), P1p[1])
    _bq2 = 2.0 * (_hx * u_edge[0] + _hy * u_edge[1])
    _cq2 = _hx * _hx + _hy * _hy - R2 * R2
    _dis2 = _bq2 * _bq2 - 4.0 * _cq2
    A2p = None
    if _dis2 >= 0:
        # A′ 比 H 还高（在 l′ 之上），不能卡 hh1_len 上限：取两个正根里**离 H1 较近**那个
        # （另一个交点在脖子另一侧，远在 1300 以上）
        _ts = [t for t in ((-_bq2 + math.sqrt(_dis2)) / 2.0,
                           (-_bq2 - math.sqrt(_dis2)) / 2.0) if t > 0]
        if _ts:
            _t = min(_ts)
            A2p = (H1[0] + u_edge[0] * _t, H1[1] + u_edge[1] * _t)
    if A2p is None:
        A2p = P0

    # 01 前片（中缝右边）：左缘＝中缝（x=0，实线），上缘＝领口线 L 弧（P1 → PK）
    right = ([["M", list(P1)]] + l_arc + right_body + [["Z"]])
    # 02 续衽（中缝左边）：右缘＝中缝（到 P1′）；上缘＝L′（水平 X→P1′ ＋ Γ_C 弧 A′→X）；
    #    左缘＝HH1（A′ → H1）。领条端面 [A, A′] 正好压在片的左上角上。
    arc_c = arc3(X_pt, mid_arc((ox, oy), R2, X_pt, A2p), A2p)
    hem_full = [["M", [0.0, 0.0]]] + hem_head
    left = ([["M", list(P1p)], ["L", list(X_pt)]] + arc_c + [["L", list(H1)]]
            + reverse_open(hem_full)[1:] + [["Z"]])


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
    # HH1 已把外端裁掉 → 虚线 l 只留新片内那一段，起点精确落在 HH1 上（不留半截悬空）
    _sgn = 1.0 if ((P1L[0] - H[0]) * u_edge[1] - (P1L[1] - H[1]) * u_edge[0]) >= 0 else -1.0

    def _side(q):
        return ((q[0] - H[0]) * u_edge[1] - (q[1] - H[1]) * u_edge[0]) * _sgn

    l_full = [(ox + R * math.cos(a_p2 + (a_p1 - a_p2) * i / 48.0),
               oy + R * math.sin(a_p2 + (a_p1 - a_p2) * i / 48.0)) for i in range(49)]
    l_mark = []
    for i, q in enumerate(l_full):
        if _side(q) >= -1e-9:
            if i and _side(l_full[i - 1]) < 0:                  # 跨过 HH1：补交点
                a_, b_ = l_full[i - 1], q
                sa, sb = _side(a_), _side(b_)
                tt = sa / (sa - sb) if abs(sa - sb) > 1e-15 else 0.0
                l_mark.append([a_[0] + (b_[0] - a_[0]) * tt, a_[1] + (b_[1] - a_[1]) * tt])
            l_mark.append([q[0], q[1]])
    xur_meta = dict(P2=list(P2), P2p=list(P2p), P1p=list(P1p), P1=list(P1), heel=list(heel),
                    P=list(PK), H=list(H), H1=list(H1), H_ARC=H_ARC, P0=list(P0),
                    X_LP=list(X_pt), A2=list(A2p), collar_w=_CW, R2=R2,
                    top_arc_full=chain_len(P2p, lp_arc), top_arc_rest=chain_len(H, lp_rest),
                    HH1=hh1_len, HH1_width=hh1_perp,
                    l_circle=[ox, oy, R], hem=[[0.0, 0.0]] + [list(q) for q in left_hem[1:]])
    xur_piece = dict(name="续衽（中缝左边）", qty=1, cmds=left, grain=[0, 1],
                     notches=[[0.0, 0.0]], dims=[], marks=[l_mark] if len(l_mark) >= 2 else [],
                     aux=[[[heel[0], heel[1]], [P2[0], P2[1]], [P2p[0], P2p[1]]],
                          [[H1[0], H1[1]], [heel[0], heel[1]]]],
                     meta=xur_meta,
                     note="右缘＝中缝；上缘＝L′（领条外缘弧 A′→X ＋ 水平段 X→P1′）；左缘＝HH1")

    # 前片 / 续衽 / 内襟（前片镜像） / 内襟续衽（续衽镜像） / 后片
    back_piece = dict(name="后片（半·模板原样）", qty=2,   # 片名沿用（gates 按名对账），几何已由构造生成
                      cmds=[list(c) if c[0] == "Z" else [c[0]] + [list(pt) for pt in c[1:]]
                            for c in _bk["cmds"]],
                      grain=[0, 1], notches=[list(n) for n in (_bk.get("notches") or [])],
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
    # **领条随续衽同步（2026-11-18）**：门襟边改成 HH1 后，领缘的起点＝**HH1 与 l 圆的交点 P0**
    # （旧版该点就是 P2）。缝线＝P0→PK 的 l 弧，长度与平铺图领子同源，不再各自为政。
    aA = math.atan2(P0[1] - oy, P0[0] - ox)
    aP = math.atan2(PK[1] - oy, PK[0] - ox)
    sweep = aP - aA
    if sweep < 0:
        sweep += 2.0 * math.pi
    arc_L = R * sweep
    back_neck = 2.0 * NWF
    collar_len = 2.0 * arc_L + back_neck
    collar_w = solve_collar_w(xur_meta)   # 反解（B 落中缝），不再是硬编码
    out.append(dict(
        name="领缘条（高交领·全衣一条）", qty=1,
        cmds=[["M", [0.0, 0.0]], ["L", [collar_len, 0.0]],
              ["L", [collar_len, collar_w]], ["L", [0.0, collar_w]], ["Z"]],
        grain=[1, 0], notches=[],
        dims=[("L", [0.0, 0.0], [collar_len, 0.0], "领条长 %.1f" % collar_len),
              ("L", [collar_len, 0.0], [collar_len, collar_w], "领宽 %.1f" % collar_w)],
        note="反推：长＝2×(P0→颈侧点 L 弧 %.1f)＋后领段 %.1f＝%.1f；宽＝AA′＝PB＝%.1f"
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
    if p.get("meta"):                                # meta 里的点也镜像，免得内外襟读串
        mt = {}
        for k, v in p["meta"].items():
            if isinstance(v, (list, tuple)) and len(v) == 2 and all(
                    isinstance(q, (int, float)) for q in v):
                mt[k] = [-v[0], v[1]]
            elif isinstance(v, (list, tuple)) and len(v) == 3 and all(
                    isinstance(q, (int, float)) for q in v):
                mt[k] = [-v[0], v[1], v[2]]          # 圆心 + 半径
            elif isinstance(v, (list, tuple)) and v and all(
                    isinstance(q, (list, tuple)) and len(q) == 2 for q in v):
                mt[k] = [[-q[0], q[1]] for q in v]
            else:
                mt[k] = v
        p["meta"] = mt
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
