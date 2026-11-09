# -*- coding: utf-8 -*-
"""唐圆领 · 版型几何（逐步构建）

底：沿用 ming-gaojiaoling 的后片模板 `_template_back.json`（只读它的参数与后片）。
唐圆领自己的东西都写在本目录，不改父版型一行代码。

口径（用户 2026-11-09）：**前片（前身）包含内襟与外襟，我们现在画的是外襟**。
外襟 = 中缝右边的衣身 ＋ 越过中缝拼在左边的续衽；内襟是它的镜像，
本图**不画内襟、不做镜像**。

第 1 步：前片的领口点 P 与关于前中缝对称的 P'
第 2 步：以 PP' 为直径画圆，取下半圆为领口
第 3 步：领口偏小，P 沿顶边右移 3cm；P' 仍对称，圆心不动、半径与领口弧随之重算
第 4 步：过 P' 作续衽片左缘，直线，平行于衣身左缘
第 5 步：上领子 —— 过左缘直线定 A、B（AB = 领宽，P' 在 AB 上），
         对称得 A'B'；领子 = 一个定积分
第 6 步：镜像得内襟，补后片，出平铺预览
第 7 步：续衽左缘斜率可调（两端恒为 P' 与「左缘∩下摆」）；
         下摆是一条简单曲线，续衽面积靠**沿边界分段积分**求得
         （边界含领口弧与续衽左缘两条不同性质的边，不能一个公式算完）
第 8 步：出完整裁片图 —— 领条 / 前片原生 / 前片续衽 / 后片
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TPL_PATH = os.path.join(HERE, "..", "..", "ming-gaojiaoling", "pattern",
                        "_template_back.json")
TPL = json.load(open(TPL_PATH, encoding="utf-8"))

# 尺寸：先用模板那套（唐圆领自己的尺寸待定，给一个就换一个）
CASE = dict(name="本案", **{k: v for k, v in TPL["params"].items()
                            if isinstance(v, (int, float))})

# 用户定：领口偏小，P 沿顶边（+x）右移 3cm = 30mm。
# P' 由对称自动左移同样距离；圆心 C 仍在前中缝上，r 与下半圆按新 |PP'| 重算。
P_SHIFT = 30.0                       # mm

# 领宽（用户 2026-11-09 定：暂取 7cm = 70mm；模板 COL_W 正好也是 70）
COLLAR_W = 70.0
# 用户定：A、B 是沿左缘直线随便取的一段，**暂定 P' 为 AB 中点**。
COLLAR_SPLIT = 0.5                   # 0 = P' 落在 A 端，1 = 落在 B 端

# 续衽左缘斜率（用户 2026-11-09：斜率**可调**）。
#   None  ＝ 平行衣身左缘（第 4 步原口径，默认，产物不变）
#   数值  ＝ 与竖直方向的夹角（度），向右倾为正
# 也可在参数字典里给 XUREN_TILT_DEG 覆盖。
XUREN_TILT_DEG = None

# 后片**不挖后领**（用户 2026-11-09 最终决定，考虑过挖浅窝后否掉）。
# 顶边到后中保持模板的水平直线，领子段 ② 就沿这条直线装。
# 不要再自作主张加后领窝、下挖深度或 BACK_NECK_DIP 之类参数。


def derive(p):
    d = dict(p)
    d["HALF"] = p["W_HEM"] / 2.0 * p.get("EASE", 1.0)
    return d


def neck_points(d):
    """领口点 P 与它的对称点 P'。

    P  ＝ 领口点：领口弧与前片顶边（肩线）的交点，落在**前中缝右边**。
         x = NECK/2 + P_SHIFT（P_SHIFT 默认 30mm，即模板点右移 3cm）。
    P' ＝ P 关于前中缝（x = 0）的对称点，随 P 一起动。
    """
    shift = float(d.get("P_SHIFT", P_SHIFT))
    P = (d["NECK"] / 2.0 + shift, d["L"])
    Pp = (-P[0], P[1])
    return P, Pp


def neck_circle(d):
    """以 PP' 为直径的圆。

    圆心 C 是 P、P' 的中点，落在前中缝 x = 0 上（P 右移时 C 不动）；
    半径 r = |PP'| / 2 = NECK / 2 + P_SHIFT。返回 (C, r)。
    """
    P, Pp = neck_points(d)
    C = ((P[0] + Pp[0]) / 2.0, (P[1] + Pp[1]) / 2.0)
    r = abs(P[0] - Pp[0]) / 2.0
    return C, r


def neck_arc(d, n=64):
    """领口弧 ＝ 这个圆的下半圆（y <= C_y），从 P' 走到 P 的 CAD 坐标点列。

    x = Cx + r*cos(t), y = Cy - r*sin(t)，t 由 pi 到 0：
      t = pi   → P' (Cx-r, Cy)
      t = pi/2 → 最低点 (Cx, Cy-r)
      t = 0    → P  (Cx+r, Cy)
    """
    C, r = neck_circle(d)
    out = []
    for i in range(n + 1):
        t = math.pi * (1.0 - i / float(n))
        out.append((C[0] + r * math.cos(t), C[1] - r * math.sin(t)))
    return out


def body_left_edge(d):
    """衣身左缘（外襟衣身的侧缝，镜像到前中缝 x=0 左侧作方向参照）。

    取模板后片 `cmds` 里「摆角 → 腋下转直线点」那条直线段，再关于 x=0 镜像。
    返回 (A, B)：A = 摆角，B = 腋下点；方向 v = B - A 指向右上。
    """
    cmds = TPL["cmds"]
    a = b = None
    for i, c in enumerate(cmds):
        if c[0] == "C" and i + 1 < len(cmds) and cmds[i + 1][0] == "L":
            a, b = tuple(c[3]), tuple(cmds[i + 1][1])
            break
    if a is None:
        raise ValueError("模板后片里找不到「摆弧 → 侧缝直线」")
    return ((-a[0], a[1]), (-b[0], b[1]))


def xuren_dir(d):
    """续衽左缘的单位方向（指向右上）。

    斜率可调：给 XUREN_TILT_DEG 就按「与竖直夹角」取方向；
    不给（默认 None）则平行衣身左缘，保持第 4 步原状。
    """
    A, B = body_left_edge(d)
    vx, vy = B[0] - A[0], B[1] - A[1]
    n0 = math.hypot(vx, vy)
    tilt = d.get("XUREN_TILT_DEG", XUREN_TILT_DEG)
    if tilt is None:
        return (vx / n0, vy / n0)
    th = math.radians(float(tilt))
    return (math.sin(th), math.cos(th))


def hem_curve(d, n=200):
    """下摆：模板后片摆弧镜像到左侧的一条**简单曲线**（三次贝塞尔）。

    从 (0,0) 走到摆角 (-HALF, HEM_RISE)，x 单调递减。
    """
    cmds = TPL["cmds"]
    p0 = (-cmds[0][1][0], cmds[0][1][1])
    c = next(cmd for cmd in cmds if cmd[0] == "C")
    p1 = (-c[1][0], c[1][1])
    p2 = (-c[2][0], c[2][1])
    p3 = (-c[3][0], c[3][1])
    out = []
    for i in range(n + 1):
        t = i / float(n)
        mt = 1.0 - t
        out.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
                    + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                    mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
                    + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def hem_y_at(x, hem):
    """简单下摆曲线上给定 x 的 y（折线线性插值；x 单调递减）。"""
    if x >= hem[0][0]:
        return hem[0][1]
    if x <= hem[-1][0]:
        return hem[-1][1]
    for i in range(len(hem) - 1):
        x0, y0 = hem[i]
        x1, y1 = hem[i + 1]
        if x1 <= x <= x0:
            t = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
            return y0 + (y1 - y0) * t
    return hem[-1][1]


def hem_intersection(d, n=200):
    """续衽左缘与下摆（简单曲线）的交点：沿直线从上往下二分求 y 相等。"""
    P, Pp = neck_points(d)
    u = xuren_dir(d)
    hem = hem_curve(d, n)

    def f(s):
        qx = Pp[0] - u[0] * s
        qy = Pp[1] - u[1] * s
        return qy - hem_y_at(qx, hem)

    lo, hi = 0.0, Pp[1] / u[1] * 1.5
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if f(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    s = (lo + hi) / 2.0
    Q = (Pp[0] - u[0] * s, Pp[1] - u[1] * s)
    if Q[0] < hem[-1][0]:
        raise ValueError("续衽左缘倾角过大：与下摆的交点落到摆角之外 "
                         "(x=%.1f < %.1f)，请把 XUREN_TILT_DEG 调小"
                         % (Q[0], hem[-1][0]))
    return Q


def xuren_left_edge(d, y_end=None):
    """外襟·续衽片左缘：过 P' 的**直线**，斜率可调。

    两个端点恒为（用户 2026-11-09 定）：
      上端 P'，下端＝「左缘与下摆的交点」（y_end 给数值时才改用 y=y_end）。
    返回 (P', 下端点, 方向向量 v)；v 与衣身左缘同量纲，默认时完全等于 B-A。
    """
    P, Pp = neck_points(d)
    u = xuren_dir(d)
    A, B = body_left_edge(d)
    n0 = math.hypot(B[0] - A[0], B[1] - A[1])
    V = (u[0] * n0, u[1] * n0)
    if y_end is None:
        Q = hem_intersection(d)
    else:
        t = (y_end - Pp[1]) / u[1]
        Q = (Pp[0] + u[0] * t, y_end)
    return Pp, Q, V


def xuren_data(d, n=200):
    """续衽面积 = 沿闭合边界的**分段线积分** A = ½∮(x dy − y dx)。

    下摆只是一条简单曲线（三次贝塞尔），但续衽的边界还有中缝、领口弧、
    续衽左缘直线两条不同性质的边 —— 所以面积必须分四段各自积分再相加：

      ① 下摆   左缘∩下摆 → (0,0)，沿下摆简单曲线
      ② 中缝   (0,0) → 领口最低点 (0, C_y-r)
      ③ 领口   领口最低点 → P'，沿下半圆弧左半
      ④ 左缘   P' → 左缘∩下摆，直线

    每段给：点列、面积积分贡献、弧长积分；四段贡献之和即续衽面积。
    斜率 XUREN_TILT_DEG 变了，交点与面积都跟着变。
    """
    P, Pp = neck_points(d)
    C, r = neck_circle(d)
    Q0, Q1, V = xuren_left_edge(d)
    hem = hem_curve(d, n)
    idx = min(range(len(hem)), key=lambda i: abs(hem[i][0] - Q1[0]))

    seg_hem = list(reversed(hem[:idx + 1]))
    seg_hem[0], seg_hem[-1] = Q1, (0.0, 0.0)
    yb = C[1] - r
    seg_mid = [(0.0, yb * i / float(n)) for i in range(n + 1)]
    seg_neck = [(C[0] + r * math.cos(math.pi / 2 + math.pi / 2 * i / n),
                 C[1] - r * math.sin(math.pi / 2 + math.pi / 2 * i / n))
                for i in range(n + 1)]
    seg_edge = [(Pp[0] + (Q1[0] - Pp[0]) * i / float(n),
                 Pp[1] + (Q1[1] - Pp[1]) * i / float(n))
                for i in range(n + 1)]

    def integrate(pts):
        a = 0.0
        L = 0.0
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            a += 0.5 * (x0 * y1 - x1 * y0)      # ½∮(x dy − y dx) 的离散形式
            L += math.hypot(x1 - x0, y1 - y0)
        return a, L

    parts, total_a, total_L = [], 0.0, 0.0
    for name, pts in (("① 下摆（简单曲线）", seg_hem), ("② 中缝", seg_mid),
                      ("③ 领口弧", seg_neck), ("④ 续衽左缘（直线）", seg_edge)):
        a, L = integrate(pts)
        total_a += a
        total_L += L
        parts.append(dict(name=name, area_contrib=round(a, 4), length=round(L, 4),
                          points=[[round(q[0], 4), round(q[1], 4)] for q in pts]))

    tilt = d.get("XUREN_TILT_DEG", XUREN_TILT_DEG)
    return dict(
        schema="tang-yuanling/xuren@1",
        unit="mm",
        note="续衽面积 = 沿闭合边界的分段线积分 A = ½∮(x dy − y dx)；"
             "下摆是一条简单曲线，分段是因为还有领口弧与续衽左缘两条边。"
             "各段 area_contrib 是相对原点的有向面积代数分量，只有四段之和才是续衽面积",
        tilt_deg=tilt,
        tilt_source="平行衣身左缘" if tilt is None else "XUREN_TILT_DEG 指定",
        endpoints=dict(Pp=[round(q, 4) for q in Q0],
                       hem_cross=[round(q, 4) for q in Q1]),
        integral=dict(formula="A = ½∮(x dy − y dx) = Σ 四段贡献",
                      area=round(abs(total_a), 4), perimeter=round(total_L, 4)),
        segments=parts,
        outline=[q for seg in (seg_hem, seg_mid, seg_neck, seg_edge) for q in seg],
    )


def collar_points(d):
    """上领子第 1 小步：过续衽左缘直线定 A、B；A'、B' 关于前中缝对称。

    条件（用户 2026-11-09 定）：
      · AB 落在**续衽左缘直线**上（方向 u0，指向右上）；
      · |AB| = 领宽 = 7cm；
      · P' 为 AB **中点**（A 沿 -u0、B 沿 +u0）；
      · A' = (-Ax, Ay)、B' = (-Bx, By)，即关于 x=0 中缝的镜像。
    A、B 本身「随便取」，只是领子端边的标记；领子的量由后面的积分定。

    返回 (A, B, Ap, Bp, u0, u1)；u1 是 A'B' 的单位方向（u0 的镜像）。
    """
    P, Pp = neck_points(d)
    Q0, Q1, V = xuren_left_edge(d)
    n = math.hypot(V[0], V[1])
    ux, uy = V[0] / n, V[1] / n
    w = float(d.get("COLLAR_W", COLLAR_W))
    s = float(d.get("COLLAR_SPLIT", COLLAR_SPLIT))
    A = (Pp[0] - s * w * ux, Pp[1] - s * w * uy)
    B = (Pp[0] + (1.0 - s) * w * ux, Pp[1] + (1.0 - s) * w * uy)
    Ap, Bp = (-A[0], A[1]), (-B[0], B[1])
    return A, B, Ap, Bp, (ux, uy), (-ux, uy)


def collar_dir(t, u0, u1):
    """积分路径上参数 t 处的端边单位方向：从 u0 按角度线性过渡到镜像 u1。"""
    t0 = math.atan2(u0[1], u0[0])
    t1 = math.atan2(u1[1], u1[0])
    while t1 < t0:
        t1 += 2.0 * math.pi
    th = t0 + (t1 - t0) * t
    return (math.cos(th), math.sin(th))


def collar_integral(d, n=400):
    """领子 = 一个定积分。

    把端边 AB 沿**领口下半圆弧**从 P' 扫到 P：端边方向由 u0 连续过渡到
    镜像方向 u1（这样末端正好落在 A'B' 上），宽恒为领宽 w。
    于是领子就是「端边沿曲线的积分」，领长为弧长定积分

        L = ∫_{P'}^{P} ds = ∫_0^π r dt = π r

    数值上用累加弦长做定积分（n 段），与解析值 πr 对照。
    返回 (spine, edge_a, edge_b, L_num, L_exact)。
    """
    A, B, Ap, Bp, u0, u1 = collar_points(d)
    C, r = neck_circle(d)
    w = float(d.get("COLLAR_W", COLLAR_W))
    s = float(d.get("COLLAR_SPLIT", COLLAR_SPLIT))
    spine, edge_a, edge_b = [], [], []
    for i in range(n + 1):
        t = i / float(n)
        ang = math.pi * (1.0 - t)            # t=0 → P'，t=1 → P
        Q = (C[0] + r * math.cos(ang), C[1] - r * math.sin(ang))
        ux, uy = collar_dir(t, u0, u1)
        spine.append(Q)
        edge_a.append((Q[0] - s * w * ux, Q[1] - s * w * uy))
        edge_b.append((Q[0] + (1.0 - s) * w * ux, Q[1] + (1.0 - s) * w * uy))
    L_num = sum(math.hypot(spine[i + 1][0] - spine[i][0],
                           spine[i + 1][1] - spine[i][1]) for i in range(n))
    return spine, edge_a, edge_b, L_num, math.pi * r


# ── 第 6 步：内襟（外襟镜像）、后片、领子完整数据 ─────────────────

def mirror_pt(p):
    """关于前中缝 x=0 的镜像。"""
    return (-p[0], p[1])


def mirror_pts(pts):
    return [mirror_pt(q) for q in pts]


def mirror_cmds(cmds):
    """后片半 cmds 的镜像（M/L/C/Z，逐点翻 x）。"""
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
        else:
            out.append([c[0]] + [[-q[0], q[1]] for q in c[1:]])
    return out


def back_halves():
    """后片：模板后片半（右半）＋ 镜像的左半。返回 (right_cmds, left_cmds)。"""
    right = TPL["cmds"]
    return right, mirror_cmds(right)


def inner_geometry(d):
    """内襟 = 外襟关于前中缝的镜像（用户：前片含内襟与外襟）。

    返回镜像后的：续衽缘、衣身侧缝参照、领子两条边、两条端边、A/B/A'/B' 四点。
    """
    Q0, Q1, V = xuren_left_edge(d)
    EA0, EB0 = body_left_edge(d)
    A, B, Ap, Bp, u0, u1 = collar_points(d)
    sp, ea, eb, Lnum, Lex = collar_integral(d)
    return dict(
        seam=(mirror_pt(Q0), mirror_pt(Q1)),
        body_edge=(mirror_pt(EA0), mirror_pt(EB0)),
        band=(mirror_pts(ea), mirror_pts(eb)),
        ends=(mirror_pts([A, B]), mirror_pts([Ap, Bp])),
        points=dict(A=mirror_pt(A), B=mirror_pt(B),
                    Ap=mirror_pt(Ap), Bp=mirror_pt(Bp)),
    )


def collar_data(d, n=400):
    """领子完整数据：定积分明细 ＋ 三条点列 ＋ 闭合裁片轮廓 ＋ 展开尺寸。

    这是「领子为一个定积分」的完整可交付数据，可直接导出裁片或后续工序使用。
    """
    A, B, Ap, Bp, u0, u1 = collar_points(d)
    C, r = neck_circle(d)
    P, Pp = neck_points(d)
    sp, ea, eb, Lnum, Lex = collar_integral(d, n)
    w = float(d.get("COLLAR_W", COLLAR_W))
    s = float(d.get("COLLAR_SPLIT", COLLAR_SPLIT))

    integ, acc = [], 0.0
    for i in range(n):
        ds = math.hypot(sp[i + 1][0] - sp[i][0], sp[i + 1][1] - sp[i][1])
        acc += ds
        t = (i + 0.5) / float(n)
        ux, uy = collar_dir(t, u0, u1)
        integ.append(dict(i=i, t=round(t, 6), ds=round(ds, 6),
                          s=round(acc, 6), ux=round(ux, 6), uy=round(uy, 6)))

    def pts(seq):
        return [[round(q[0], 6), round(q[1], 6)] for q in seq]

    outline = list(ea) + list(reversed(eb))
    return dict(
        schema="tang-yuanling/collar@1",
        unit="mm",
        note="领子 = 端边沿领口下半圆弧的定积分扫掠；A、B 随便取，P' 暂取 AB 中点",
        params=dict(collar_w=w, split=s, center=[C[0], C[1]], r=r,
                    neck_diameter=2 * r, samples=n,
                    P=[P[0], P[1]], Pp=[Pp[0], Pp[1]]),
        ends=dict(AB=pts([A, B]), ApBp=pts([Ap, Bp]),
                  u0=[round(q, 6) for q in u0], u1=[round(q, 6) for q in u1]),
        integral=dict(formula="L = ∫ ds = ∫_0^π r dt = π r",
                      numeric=round(Lnum, 6), exact=round(Lex, 6),
                      error=round(Lex - Lnum, 6)),
        flat=dict(length=round(Lnum, 6), width=w,
                  note="长方形领条：长由弧长定积分给出，宽＝领宽"),
        detail=integ,
        points=dict(spine=pts(sp), edge_a=pts(ea), edge_b=pts(eb)),
        outline=pts(outline),
    )


def collar_route(d, n_front=400, n_back=160):
    """领子路线（用户 2026-11-09 定）：三段连续，**开放、不闭合**。

        ① 外襟 P' → P                 外襟前领口（下半圆）        πr
        ② 外襟 P → 后片 → 内襟 P'     后片后领段（顶边直线）      2r
        ③ 内襟 P' → P                 内襟前领口（下半圆）        πr

    起点＝外襟 P'（AB 端边），终点＝内襟 P（A'B' 端边），**不闭合**，
    L = ∫ds = 2πr + 2r。内襟是外襟关于中缝的镜像，其 P'/P 与外襟同坐标、
    不同片；故 ① 与 ③ 在平铺图上几何重合，但分属两片、各走一次。
    返回三段，每段含所属片、解析长度、点列。
    """
    C, r = neck_circle(d)
    P, Pp = neck_points(d)
    L = d["L"]

    front_arc = []
    for i in range(n_front):
        t = i / float(n_front)
        ang = math.pi * (1.0 - t)
        front_arc.append((C[0] + r * math.cos(ang), C[1] - r * math.sin(ang)))
    front_arc.append(P)

    back_seg = []
    for i in range(0, n_back + 1):        # 含起点 P，段内正好 n_back 个整段
        t = i / float(n_back)
        back_seg.append((P[0] + (Pp[0] - P[0]) * t, L))

    return [
        dict(no=1, on="外襟", name="外襟 P′→P（前领下半圆）",
             exact=math.pi * r, points=list(front_arc)),
        dict(no=2, on="后片", name="外襟 P→后片→内襟 P′（后领段）",
             exact=2.0 * r, points=back_seg),
        dict(no=3, on="内襟", name="内襟 P′→P（前领下半圆）",
             exact=math.pi * r, points=list(front_arc)),
    ]


def full_collar_data(d, n_front=400, n_back=160):
    """完整领子 = 沿三段路线的**一条连续、不闭合的带子**。

    端边方向：① u0→u1，② u1→u0，③ u0→u1，三段接缝处方向连续；
    两端分别是 AB（外襟 P'）与 A'B'（内襟 P），展开就是一根开放长条。
    """
    front = collar_data(d, n_front)
    route = collar_route(d, n_front, n_back)
    A, B, Ap, Bp, u0, u1 = collar_points(d)
    w = float(d.get("COLLAR_W", COLLAR_W))
    s = float(d.get("COLLAR_SPLIT", COLLAR_SPLIT))

    # 三段首尾相接成一条 spine；方向按段号切换，接缝处连续
    spine, dirs = [], []
    for seg in route:
        pts = seg["points"]
        for j, Q in enumerate(pts):
            t = j / float(max(len(pts) - 1, 1))
            ux, uy = (collar_dir(1.0 - t, u0, u1) if seg["no"] == 2
                      else collar_dir(t, u0, u1))
            spine.append(Q)
            dirs.append((ux, uy, seg["no"], seg["on"]))

    ea, eb, detail, acc = [], [], [], 0.0
    seg_numeric = {1: 0.0, 2: 0.0, 3: 0.0}
    for i, Q in enumerate(spine):
        ux, uy, no, on = dirs[i]
        ea.append((Q[0] - s * w * ux, Q[1] - s * w * uy))
        eb.append((Q[0] + (1.0 - s) * w * ux, Q[1] + (1.0 - s) * w * uy))
        if i < len(spine) - 1:
            R = spine[i + 1]
            ds = math.hypot(R[0] - Q[0], R[1] - Q[1])
            acc += ds
            seg_numeric[no] += ds
            detail.append(dict(i=i, seg=no, on=on, ds=round(ds, 6),
                               s=round(acc, 6),
                               ux=round(ux, 6), uy=round(uy, 6)))

    def pts(seq):
        return [[round(q[0], 6), round(q[1], 6)] for q in seq]

    exact = sum(seg["exact"] for seg in route)
    return dict(
        schema="tang-yuanling/collar-full@2",
        unit="mm",
        note="完整领子＝沿三段路线（外襟 P′→P ／ 外襟 P→后片→内襟 P′ ／ 内襟 P′→P）"
             "的一条**连续、不闭合**带子；两端为 AB 与 A′B′",
        flat=dict(length=round(acc, 6), width=w, closed=False,
                  start="外襟 P′ / AB", end="内襟 P / A′B′",
                  note="开放长条；长由三段弧长定积分给出，宽＝领宽"),
        integral=dict(formula="L = ∫ ds = 2πr + 2r", numeric=round(acc, 6),
                      exact=round(exact, 6), error=round(exact - acc, 6)),
        segments=[
            dict(no=seg["no"], name=seg["name"], on=seg["on"],
                 exact=round(seg["exact"], 6),
                 numeric=round(seg_numeric[seg["no"]], 6),
                 samples=len(seg["points"]))
            for seg in route
        ],
        ends=dict(AB=pts([A, B]), ApBp=pts([Ap, Bp]),
                  u0=[round(q, 6) for q in u0], u1=[round(q, 6) for q in u1]),
        points=dict(spine=pts(spine), edge_a=pts(ea), edge_b=pts(eb)),
        outline=pts(list(ea) + list(reversed(eb))),
        detail=detail,
        front=front,
    )


# ── 第 8 步：完整裁片（领条 / 前片原生 / 前片续衽 / 后片）─────────

def _cmds_points(cmds, n=24):
    """cmds（M/L/C/Z）→ 折线点列，C 段按 n 段采样。"""
    out, cur = [], None
    for c in cmds:
        if c[0] == "M":
            cur = tuple(c[1])
            out.append(cur)
        elif c[0] == "L":
            cur = tuple(c[1])
            out.append(cur)
        elif c[0] == "C":
            A = cur
            C1, C2, B = [tuple(q) for q in c[1:4]]
            for i in range(1, n + 1):
                t = i / float(n)
                mt = 1.0 - t
                out.append((mt ** 3 * A[0] + 3 * mt * mt * t * C1[0]
                            + 3 * mt * t * t * C2[0] + t ** 3 * B[0],
                            mt ** 3 * A[1] + 3 * mt * mt * t * C1[1]
                            + 3 * mt * t * t * C2[1] + t ** 3 * B[1]))
            cur = B
    return out


def front_body_cmds(d, n=32):
    """前片原生（外襟衣身本体，中缝右边、含袖）的闭合 cmds。

    骨架照模板后片半（摆弧／侧缝／腋圆角／袖底／袖口／肩点全不改），
    只把领口换成圆领：顶边走到颈侧点 P，沿下半圆右四分之一下到
    领口最低点 (0, C_y-r)，再沿前中缝回 (0,0)。
    """
    P, Pp = neck_points(d)
    C, r = neck_circle(d)
    right = TPL["cmds"]
    out = [["M", list(right[0][1])]]
    for c in right[1:]:
        if c[0] == "L" and abs(c[1][1] - d["L"]) < 1e-6 and c[1][0] < 100.0:
            break                              # 到后片颈侧点 (50,800) 为止
        out.append([c[0]] + [list(q) for q in c[1:]])
    out.append(["L", [P[0], P[1]]])            # 顶边 → 颈侧点 P
    for i in range(1, n + 1):                  # 圆领：P → (0, C_y-r)
        a = (math.pi / 2.0) * i / n
        out.append(["L", [C[0] + r * math.cos(a), C[1] - r * math.sin(a)]])
    out.append(["L", [0.0, 0.0]])              # 前中缝
    out.append(["Z"])
    return out


def back_whole_points(d, n=24):
    """后片整片：模板后片半（右）＋ 镜像半（左）拼成一条闭合外轮廓。

    注意：**裁片图不用它**（裁片图按半片 ×2 出，见 sheet_pieces）；
    它只给「面积／拼合示意」这类要整片量的事用。
    """
    R, Lf = back_halves()
    a = _cmds_points(R, n)                     # (0,0) → (0,800)
    b = _cmds_points(Lf, n)                    # (0,0) → (0,800)
    return a + list(reversed(b))               # 右半上去、左半回来


def shoelace(pts):
    """闭合折线面积（有向，取绝对值即用）。"""
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def piece_data(d):
    """四片完整裁片数据：领条 / 前片原生 / 前片续衽 / 后片。"""
    C, r = neck_circle(d)
    F = full_collar_data(d)
    X = xuren_data(d)
    cw = F["flat"]["width"]
    cl = F["flat"]["length"]
    collar = [(0.0, 0.0), (cl, 0.0), (cl, cw), (0.0, cw)]
    front = _cmds_points(front_body_cmds(d))
    xuren = [tuple(q) for q in X["outline"]]
    back = back_whole_points(d)
    x_cuff = d["X_SHLD"] + d["SLEEVE_LEN"]

    def pc(name, qty, outline, note, dims):
        return dict(name=name, qty=qty,
                    outline=[[round(q[0], 4), round(q[1], 4)] for q in outline],
                    area=round(abs(shoelace(outline)), 4),
                    dims=dims, note=note)

    return dict(
        schema="tang-yuanling/pieces@1",
        unit="mm",
        note="四片各自摊开。内襟＝前片原生的镜像、内襟续衽＝前片续衽的镜像，"
             "故 qty 记 2；后片为模板后片半×2 拼成的整片。",
        collar_route=dict(segments=F["segments"], length=cl, width=cw,
                          closed=F["flat"]["closed"],
                          start=F["flat"]["start"], end=F["flat"]["end"]),
        pieces=[
            pc("领条", 1, collar,
               "三段连续开放长条；长＝∫ds＝2πr+2r，两端 AB / A′B′",
               dict(length=round(cl, 4), width=cw, closed=False)),
            pc("前片原生", 2, front,
               "外襟衣身本体（中缝右边、含袖）；骨架＝模板后片半，领口换成圆领",
               dict(back_length=d["L"], to_sleeve_seam=x_cuff,
                    neck_radius=r, neck_bottom=C[1] - r)),
            pc("前片续衽", 2, xuren,
               "越中拼在前中缝左侧；面积由四段边界积分得到",
               dict(area=X["integral"]["area"], perimeter=X["integral"]["perimeter"],
                    tilt_deg=X["tilt_deg"],
                    hem_cross=X["endpoints"]["hem_cross"])),
            pc("后片", 1, back,
               "模板后片半 ×2 拼成整片（后中缝为对折／缝合线）",
               dict(back_length=d["L"], half_width=d["HALF"],
                    to_sleeve_seam=x_cuff, hem_rise=d["HEM_RISE"])),
        ],
    )


def sheet_pieces(d):
    """裁片图片表（照 `ming-gaojiaoling/pattern/geo.pieces()` 的同一套口径）。

    与 `piece_data()` 的差别只有一处、但很要紧：**后片按「模板后片半 ×2」出**，
    不再把左右两半拼成一片整的。理由：
      · 明制高交领 / 接袖 / 深衣的裁片图里，后片一律是「半·模板原样」×2；
      · 后中缝本来就是拼幅缝（或对折线），画成整片会让人误以为是一片裁；
      · 后片不挖领，半片的顶边到后中就是模板那条水平直线，原样照抄即可。

    每片字段与 sheet.write_sheet 对齐：name / qty / cmds / grain / notches /
    dims / marks / note。grain 用服装坐标（y 向上），[0,1]＝沿后中竖直。
    """
    F = full_collar_data(d)
    X = xuren_data(d)
    P, Pp = neck_points(d)
    cw = F["flat"]["width"]
    cl = F["flat"]["length"]
    Q0, Q1, _V = xuren_left_edge(d)

    collar_cmds = [["M", [0.0, 0.0]], ["L", [cl, 0.0]],
                   ["L", [cl, cw]], ["L", [0.0, cw]], ["Z"]]

    front = front_body_cmds(d)

    xur = [["M", list(X["outline"][0])]] + [["L", list(q)] for q in X["outline"][1:]]
    xur.append(["Z"])

    back_half = [["M", list(TPL["cmds"][0][1])]]
    for c in TPL["cmds"][1:]:
        back_half.append([c[0]] + ([list(q) for q in c[1:]] if c[0] != "Z" else []))

    return [
        dict(name="领条", qty=1, cmds=collar_cmds, grain=[1, 0], notches=[],
             marks=[],
             dims=[("L", [0.0, 0.0], [cl, 0.0], "领条长 %.1f（开放·不闭合）" % cl),
                   ("L", [cl, 0.0], [cl, cw], "领宽 %.0f" % cw)],
             note="三段连续，不闭合"),
        dict(name="前片原生", qty=2, cmds=front, grain=[0, 1],
             notches=[[0.0, 0.0], [round(P[0], 4), round(P[1], 4)]]
                     + [[round(q[0], 4), round(q[1], 4)]
                        for q in (TPL.get("notches") or []) if abs(q[0]) > 1e-9],
             marks=[],
             dims=[("L", [0.0, 0.0], [0.0, d["L"]], "后中长 %.0f" % d["L"])],
             note="外襟衣身；左缘＝前中缝"),
        dict(name="前片续衽", qty=2, cmds=xur, grain=[0, 1],
             notches=[[round(Q0[0], 4), round(Q0[1], 4)],
                      [round(Q1[0], 4), round(Q1[1], 4)]],
             marks=[],
             # 尺寸线不能取左缘本身：它与「片心→中点」几乎共线，偏移方向会退化，
             # 文字会压在片上（第一版就是这样）。改成下摆那条横边。
             dims=[("L", [0.0, 0.0], [round(Q1[0], 4), 0.0],
                    "下摆段 %.0f" % abs(Q1[0]))],
             note="越中拼在中缝左侧"),
        dict(name="后片（半·模板原样）", qty=2, cmds=back_half,
             grain=list(TPL.get("grain") or [0, 1]),
             notches=[[round(q[0], 4), round(q[1], 4)]
                      for q in (TPL.get("notches") or [])],
             marks=[],
             dims=[("L", [0.0, 0.0], [0.0, d["L"]], "后中长 %.0f" % d["L"])],
             note="模板原样；×2 镜像"),
    ]
