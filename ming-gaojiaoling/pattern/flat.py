# -*- coding: utf-8 -*-
"""平铺线稿：五片铺平 ＋ 领子（领缘条原位）

产物：
  out/平铺线稿.svg  —— 前片/续衽 在前，内襟/内襟续衽 压在下层，后片影；领子一条带铺在领口上

领子口径（2026-11-18 定）：
  下缘＝P 所在的 L 弧；上缘＝同心 R−C（法向等宽，宽＝领条宽 C，由 `geo.solve_collar_w` 反解）；
  左端面沿 HH1（＝AA′）；两半在后中收成一个顶点（人字），P 连到该顶点。
"""
import math

import geo
import sheet

# 领宽：不再硬编码，由 geo.solve_collar_w() 反解（B 落中缝）；此处仅作未初始化时的兜底
COLLAR_W = 97.05141


def bb(cmds):
    xs, ys = [], []
    for c in cmds:
        if c[0] in ("M", "L"):
            xs.append(c[1][0]); ys.append(c[1][1])
        else:
            for p in c[1:]:
                xs.append(p[0]); ys.append(p[1])
    return min(xs), min(ys), max(xs), max(ys)


def shift(cmds, dx, dy=0.0):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
        else:
            out.append([c[0]] + [[p[0] + dx, p[1] + dy] for p in c[1:]])
    return out


def collar_seam(d, n=64):
    """领子缝线（定义口径，**半条**）：P0 →(l 圆)→ 颈侧点 P → 后中 (0, L)

    P0＝**续衽左边缘（HH1）与领口线（l 圆）的交点**——领缘沿门襟往上装到这儿为止
    （旧版门襟边＝原外缘时，P0 就是 P2）。半条长 = (P0→P 的 l 弧) + 后领半段，
    两条合起来恒等于领条长 2×(l 弧) + 后领段；**在后中 x=0 剖开**画成两半，
    避免沿中缝交叠绕成自交（交领的 V 口在 (0,y0)，整圈画必然打结）。
    """
    mt = geo.pieces(d)[2]["meta"]
    ox, oy, R = mt["l_circle"]
    P0, PK = mt["P0"], mt["P"]
    aH = math.atan2(P0[1] - oy, P0[0] - ox)
    aK = math.atan2(PK[1] - oy, PK[0] - ox)
    sw = aK - aH
    while sw < 0:
        sw += 2.0 * math.pi
    arc = [(ox + R * math.cos(aH + sw * i / float(n)),
            oy + R * math.sin(aH + sw * i / float(n))) for i in range(n + 1)]
    half_back = [(PK[0] * (1.0 - i / 4.0), PK[1]) for i in range(1, 5)]   # P → 后中 (0,L)
    return arc + half_back, tuple(P0)


def collar_band(d, n=96, mirror=False):
    """领带（一条闭合轮廓，跨后中不闭合于中缝）。符号：

        o, R      L 弧载体圆圆心/半径（mt["l_circle"]）
        C         领宽 = geo.solve_collar_w(mt)
        A = P0    HH1 ∩ Γ_L           （mt["P0"]）
        P         颈侧点 (NECKW/2, L)（mt["P"]）
        û         (H − H1)/|H − H1|  （HH1 方向）
        A″        HH1 ∩ Γ_C，Γ_C = { X : |X − o| = R − C }，取 t = |A A″| 的最小正根

    内缘（缝线）：
        Γ_in  = { o + R(cosθ, sinθ) : θ ∈ [θ_A, θ_P] } ∪ [P, (0,L)] ∪ mirror(前段)
        |Γ_in| = 2·659.245 + 130 = 1448.49 = 领条长
    上缘：
        Γ_out = { o + (R−C)(cosθ, sinθ) : θ ∈ [θ_A″, θ_top] }，θ_top = arg(0, L+C)
        ⇒ ∀X ∈ Γ_out : |X − o| = R − C（法向等宽 C）
    端面：  [A, A″] ⊂ HH1，length = |A″ − A|
    后中：  Γ_in 取水平段 (P.x, L) → (−P.x, L)（穿过 x = 0）；Γ_out 取顶点 (0, L+C)（两半在此共点）
    P→顶点：∀s ∈ {±1} : 线段 [ (s·P.x, L), (0, L+C) ]
    """
    mt = geo.pieces(d)[2]["meta"]
    ox, oy, R = mt["l_circle"]
    A, P, H1, H = mt["P0"], mt["P"], mt["H1"], mt["H"]
    C = geo.solve_collar_w(mt)
    R2 = R - C
    u = geo._unit(H1, H)
    ytop = P[1] + C

    hx, hy = A[0] - ox, A[1] - oy
    bq = 2.0 * (hx * u[0] + hy * u[1])
    cq = hx * hx + hy * hy - R2 * R2
    disc = bq * bq - 4.0 * cq
    ts = [t for t in ((-bq + math.sqrt(max(0.0, disc))) / 2.0,
                      (-bq - math.sqrt(max(0.0, disc))) / 2.0) if t > 0]
    A2 = (A[0] + u[0] * min(ts), A[1] + u[1] * min(ts)) if ts else A

    def ang(q):
        return math.atan2(q[1] - oy, q[0] - ox)

    aA, aP, aA2, aT = ang(A), ang(P), ang(A2), ang((0.0, ytop))
    sw = aP - aA
    while sw < 0:
        sw += 2.0 * math.pi
    inner_l = [(ox + R * math.cos(aA + sw * i / float(n)),
                oy + R * math.sin(aA + sw * i / float(n))) for i in range(n + 1)]
    inner_l[0] = [A[0], A[1]]
    sw2 = aT - aA2
    while sw2 < 0:
        sw2 += 2.0 * math.pi
    upper_l = [(ox + R2 * math.cos(aA2 + sw2 * i / float(n)),
                oy + R2 * math.sin(aA2 + sw2 * i / float(n))) for i in range(n + 1)]
    upper_l[0] = [A2[0], A2[1]]
    upper_l[-1] = [0.0, ytop]

    def mir(q):
        return (-q[0], q[1])

    inner = ([tuple(q) for q in inner_l] + [(0.0, P[1])]
             + [mir(q) for q in reversed(inner_l)])
    pts = (inner + [mir(A2)]
           + [mir(q) for q in upper_l][1:]
           + [tuple(q) for q in reversed(upper_l)])
    if mirror:
        pts = [(-q[0], q[1]) for q in pts]
    path = [["M", list(pts[0])]] + [["L", list(q)] for q in pts[1:]] + [["Z"]]
    return path, dict(A=A, A2=A2, P=P, Pu=(0.0, ytop), u=u, w=C,
                      t_end=math.hypot(A2[0] - A[0], A2[1] - A[1]),
                      ytop=ytop, inner=inner_l, upper=upper_l, pts=pts)


def write(d, out_svg):
    global COLLAR_W
    COLLAR_W = geo.solve_collar_w(geo.pieces(d)[2]["meta"])   # 领宽反解（B 落中缝）
    pcs = geo.pieces(d)
    front, nei, xur, nei_xur, back = [p["cmds"] for p in pcs[:5]]
    # 后片与前后片共用坐标（侧缝/接袖缝重合），直接叠画成虚线，表示在后层
    back_shift = [list(c) if c[0] == "Z" else [c[0]] + [list(pt) for pt in c[1:]] for c in back]

    W, H = 2600.0, 2200.0
    ox, oy = 1300.0, 1400.0
    # viewBox 上边界抬到 -150：L2 整圆顶部约在页面 y=-18，留白后完整可见、不被视口截断
    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 -150 %d %d">' % (W, H, W, H),
         '<rect width="100%" height="100%" fill="#ffffff"/>']

    def put(cm, stroke, wd, fill="none", dash=""):
        s.append('<path d="%s" stroke="%s" stroke-width="%.1f" fill="%s"%s/>'
                 % (sheet.path_d(cm, ox, oy), stroke, wd, fill,
                    (' stroke-dasharray="%s"' % dash) if dash else ""))

    put(back_shift, "#c9c9c9", 1.4, dash="22 12")
    put(nei, "#9aa7b4", 1.6)
    put(nei_xur, "#9aa7b4", 1.6)
    put(front, "#1a1a1a", 2.4)
    put(xur, "#1a1a1a", 2.4)
    put(nei_xur, "#9aa7b4", 1.6)
    # 各片的辅助线（续衽里的 l）同步画成蓝虚线
    for pc in pcs[:4]:
        for mk in pc.get("marks") or []:
            cm = [["M", list(mk[0])]] + [["L", list(q)] for q in mk[1:]]
            put(cm, "#4a78c8", 1.4, dash="18 10")

    # ─── 领子（领缘条原位：缝线＝领口线、带宽＝COLLAR_W、恒向领口外）───
    seam, P0 = collar_seam(d)
    seg_len = sum(math.hypot(seam[i + 1][0] - seam[i][0], seam[i + 1][1] - seam[i][1])
                  for i in range(len(seam) - 1))
    collar_pc = [p for p in pcs if p["name"].startswith("领缘条")][0]
    bx = geo.bbox(collar_pc["cmds"])
    band, cm = collar_band(d)
    put(band, "#1a1a1a", 2.0)          # 外→后→内 一条带，跨后中不断
    # 领口点 P 连到上缘顶点（后领段与前后领的交界）
    pp, pu = cm["P"], cm["Pu"]
    for sx in (1.0, -1.0):
        s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#1a1a1a" stroke-width="1.8"/>'
                 % (sx * pp[0] + ox, oy - pp[1], sx * pu[0] + ox, oy - pu[1]))
    print("  领子：A=(%.2f,%.2f) A″=(%.2f,%.2f) 端面 %.2f｜上缘 y %.2f"
          % (cm["A"][0], cm["A"][1], cm["A2"][0], cm["A2"][1], cm["t_end"],
             cm["P"][1] + cm["w"]))
    print("  领子：半条缝线 %.2f ×2 ＋ 后领 %.1f ＝ %.2f｜领条长 %.2f"
          % (seg_len - geo.FRONT_NECK_W, geo.FRONT_NECK_W * 2, seg_len, bx[2] - bx[0]))






    # ─── A／A′ 标记：端面就落在 HH1 上，AA′ ＝ 领宽 C ───
    A_, A2_ = cm["A"], cm["A2"]
    for sx in (1.0, -1.0):
        s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#c0392b" stroke-width="2.0"/>'
                 % (sx * A_[0] + ox, oy - A_[1], sx * A2_[0] + ox, oy - A2_[1]))
        for q, lab in ((A_, "A"), (A2_, "A′")):
            s.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#c0392b"/>'
                     % (sx * q[0] + ox, oy - q[1]))
            s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="#c0392b">%s</text>'
                     % (sx * q[0] + ox + (8.0 if sx > 0 else -30.0), oy - q[1] - 10, lab))
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="#c0392b">AA′ = PB = %.1f</text>'
             % (A_[0] + ox - 30, oy - A_[1] + 46, cm["w"]))

    s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#e0e6ec" stroke-width="1.4" stroke-dasharray="14 12"/>'
             % (ox, oy - 900, ox, oy + 100))
    s.append('<text x="150" y="150" font-family="sans-serif" font-size="50" font-weight="600" fill="#1a1a1a">'
             '平铺线稿</text>')
    s.append('<text x="150" y="210" font-family="sans-serif" font-size="26" fill="#555">'
             '实线＝前片＋续衽（外襟）｜灰细线＝内襟／内襟续衽｜灰虚线＝后片（共用侧缝与接袖缝，标在后层）</text>')
    s.append('<text x="150" y="250" font-family="sans-serif" font-size="26" fill="#555">'
             '黑粗带＝领子（领缘条原位，一条跨后中不断）：下缘＝L、上缘＝同心 R−C（法向等宽 %.1f）、'
             '左端面沿 HH1、P 连顶点；两半缝线 %.1f×2＋后领 %.0f＝领条长 %.1f</text>'
             % (COLLAR_W, seg_len - geo.FRONT_NECK_W, geo.FRONT_NECK_W * 2, bx[2] - bx[0]))

    # （原「一步一画」辅助标注：P1′→n 水平段 + 曲边三角形 ∫(P1′-L)dx 并入前片——
    #   2026-11-26 领口线统一为 L 后整块删除，图上不再有那条水平段与绿色三角。）
    s.append('</svg>')
    open(out_svg, "w", encoding="utf-8").write("\n".join(s))

    svg2 = None
    ln = 0.0
    return out_svg, svg2, ln
