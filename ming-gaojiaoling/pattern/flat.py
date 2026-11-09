# -*- coding: utf-8 -*-
"""平铺线稿（领子由用户手绘，本程序不画领子）

产物：
  out/平铺线稿.svg  —— 五片铺平（前片/续衽 在前，内襟/内襟续衽 压在下层，后片影）＋ 领子
  out/领条.svg      —— 由领子反推的领条（总长 × 宽）

领子（横卧领）：沿领口一圈的带子 —— 前领口 l 弧（外襟侧）＋ 后领口 ＋ 内襟侧 l 弧；
带宽取模板 COL_W。领条＝这条带子展开成直条。
"""
import math

import geo
import sheet

# 领宽（用户 2026-11-08 定 97.1）：AA- ＝ PB ＝ COLLAR_W。
# 精确值由「左右两个 B 落在中缝 x=0 而重合」反解得到（本案 97.05141）；
# 领宽 110 时两 B 相距 17.34mm 不重合，故不取 110。
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


def ribbon(path, w, side=1):
    A, B = [], []
    for i, p in enumerate(path):
        q = path[min(i + 1, len(path) - 1)]
        r = path[max(i - 1, 0)]
        tx, ty = q[0] - r[0], q[1] - r[1]
        n = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / n * side, tx / n * side
        A.append(list(p))
        B.append([p[0] + nx * w, p[1] + ny * w])
    return [["M", A[0]]] + [["L", p] for p in A[1:]] + [["L", p] for p in reversed(B)] + [["Z"]]


def neck_path(d):
    """领口一圈：外襟 l 弧（中缝顶→颈侧点）→ 后领口 → 内襟 l 弧（镜像）"""
    NWF, L = geo.FRONT_NECK_W, d["L"]     # 几何已由 CASE 驱动，不再读模板参数
    front = geo.pieces(d)[0]["cmds"]
    seg, cur = [], None
    for c in front:
        if c[0] == "M":
            cur = tuple(c[1]); seg.append(cur)
        elif c[0] == "C":
            A, C1, C2, B = cur, tuple(c[1]), tuple(c[2]), tuple(c[3])
            for i in range(1, 13):
                t = i / 12.0; mt = 1 - t
                seg.append((mt ** 3 * A[0] + 3 * mt * mt * t * C1[0] + 3 * mt * t * t * C2[0] + t ** 3 * B[0],
                            mt ** 3 * A[1] + 3 * mt * mt * t * C1[1] + 3 * mt * t * t * C2[1] + t ** 3 * B[1]))
            cur = B
        elif c[0] == "L":
            cur = tuple(c[1]); seg.append(cur)
        if cur and cur[0] >= NWF - 0.5:
            break
    back_neck = [(NWF - 2 * NWF * i / 8.0, L) for i in range(1, 9)]
    other = [(-x, y) for x, y in reversed(seg)]
    return seg + back_neck + other


def write(d, out_svg):
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






    # ─── 领子构建（逐步累加；外襟与内襟同步镜像）────────────────────
    # 第 1 步：A＝P2，领宽 AA′＝COLLAR_W（B 重合那一版）；PB 同为该值
    A = (-d["X_ARM"] + 0.0, 0.0)          # 占位，下面用实际 P2
    pcs0 = geo.pieces(d)[2]["cmds"]       # 续衽片：[M(摆角), L(P2), L(P'2), …]
    P2 = tuple(pcs0[1][1])                # ★ A 取 P2（l 起点），不是 P'2
    AA = COLLAR_W
    segs = []
    # A′ 在「外缘延长线」上：从摆角指向 P2 的方向，外延 w
    heel = (-d["HALF"], d["RISE"])
    dvx, dvy = P2[0] - heel[0], P2[1] - heel[1]
    dn = math.hypot(dvx, dvy) or 1.0
    dvx, dvy = dvx / dn, dvy / dn
    for sx in (1.0, -1.0):
        ax_, ay_ = sx * abs(P2[0]), P2[1]
        bx_ = ax_ - sx * dvx * AA         # 沿外缘延长线外移 w（朝中缝一侧）
        by_ = ay_ + dvy * AA
        segs.append(((ax_, ay_), (bx_, by_)))

    for (a1, b1) in segs:
        s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#c0392b" stroke-width="2.0"/>'
                 % (a1[0] + ox, oy - a1[1], b1[0] + ox, oy - b1[1]))
        for pt, lab in ((a1, "A"), (b1, "A′")):
            s.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#c0392b"/>' % (pt[0] + ox, oy - pt[1]))
            s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="#c0392b">%s</text>'
                     % (pt[0] + ox + 8, oy - pt[1] - 10, lab))
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="#c0392b">AA′ = PB = %.1f</text>'
             % (segs[0][0][0] + ox - 30, oy - segs[0][0][1] + 46, AA))

    # ─── 第 2 步：过 A′ 作 L 的平行线 L2（同心圆）───
    mk = (geo.pieces(d)[2].get("marks") or [[]])[0]
    if len(mk) >= 5:
        p1_, p2_, p3_ = mk[0], mk[len(mk) // 2], mk[-1]
        d2 = 2.0 * (p1_[0] * (p2_[1] - p3_[1]) + p2_[0] * (p3_[1] - p1_[1]) + p3_[0] * (p1_[1] - p2_[1]))
        if abs(d2) > 1e-9:
            Ox = ((p1_[0] ** 2 + p1_[1] ** 2) * (p2_[1] - p3_[1]) +
                  (p2_[0] ** 2 + p2_[1] ** 2) * (p3_[1] - p1_[1]) +
                  (p3_[0] ** 2 + p3_[1] ** 2) * (p1_[1] - p2_[1])) / d2
            Oy = ((p1_[0] ** 2 + p1_[1] ** 2) * (p3_[0] - p2_[0]) +
                  (p2_[0] ** 2 + p2_[1] ** 2) * (p1_[0] - p3_[0]) +
                  (p3_[0] ** 2 + p3_[1] ** 2) * (p2_[0] - p1_[0])) / d2
            # 外襟（左，P2 所在侧）：A′=segs[1][1]，圆心 (Ox,Oy)，半径 444.57
            # 内襟（右，镜像）    ：A′=segs[0][1]，圆心 (-Ox,Oy)，半径同为 444.57
            # L2 暂不截断：画出整个圆弧 = 完整一圈 360°，左右各一条、互为镜像
            N = 720
            for Ap, Oc in ((segs[1][1], (Ox, Oy)),
                           (segs[0][1], (-Ox, Oy))):
                R2 = math.hypot(Ap[0] - Oc[0], Ap[1] - Oc[1])
                pts = [[Oc[0] + R2 * math.cos(2 * math.pi * i / N),
                        Oc[1] + R2 * math.sin(2 * math.pi * i / N)] for i in range(N + 1)]
                cm = [["M", pts[0]]] + [["L", q] for q in pts[1:]] + [["Z"]]
                put(cm, "#2e8b57", 1.6, dash="14 9")
                top = (Oc[0], Oc[1] + R2)
                s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="#2e8b57">L2</text>'
                         % (top[0] + ox + 8, oy - top[1] - 10))

            # ─── 第 3 步：颈侧点 P 与 L2 上的点 B，使 PB = AA′ = 领宽 w ───
            # 以 P 为圆心、w 为半径的圆与 L2 求交，一般两个解；取与 A′ 同向角偏移的
            # 那个（与 AA′ 的构造对应），另一个是反向解。
            # 领宽取 COLLAR_W，使左右两个 B 落在中缝 x=0 上而重合。
            # 只画 点P、点B、线PB，不画定位圆、不留多余辅助线。
            PB = AA
            Pn = (geo.FRONT_NECK_W, d["L"])       # 颈侧点 (65, 800)
            A0, Ap0 = segs[1][0], segs[1][1]      # 外襟：A=P2，A′

            def _inter(c0, r0, c1, r1):
                dx, dy = c1[0] - c0[0], c1[1] - c0[1]
                D = math.hypot(dx, dy)
                if D < 1e-9:
                    return []
                a = (r0 * r0 - r1 * r1 + D * D) / (2.0 * D)
                h = math.sqrt(max(0.0, r0 * r0 - a * a))
                ux, uy = dx / D, dy / D
                bx, by = c0[0] + a * ux, c0[1] + a * uy
                return [(bx - h * uy, by + h * ux), (bx + h * uy, by - h * ux)]

            def _wrap(t):
                return math.atan2(math.sin(t), math.cos(t))

            for mir in (1.0, -1.0):
                if mir > 0:                       # 外襟
                    Oc, Pc, Ac, Apc = (Ox, Oy), Pn, A0, Ap0
                else:                             # 内襟＝镜像同步
                    Oc = (-Ox, Oy)
                    Pc = (-Pn[0], Pn[1])
                    Ac, Apc = (-A0[0], A0[1]), (-Ap0[0], Ap0[1])
                R2b = math.hypot(Apc[0] - Oc[0], Apc[1] - Oc[1])
                dA = _wrap(math.atan2(Apc[1] - Oc[1], Apc[0] - Oc[0]) -
                           math.atan2(Ac[1] - Oc[1], Ac[0] - Oc[0]))
                aP = math.atan2(Pc[1] - Oc[1], Pc[0] - Oc[0])
                cands = _inter(Oc, R2b, Pc, PB)
                B = next((q for q in cands
                          if _wrap(math.atan2(q[1] - Oc[1], q[0] - Oc[0]) - aP) * dA > 0),
                         cands[0] if cands else Pc)
                s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#c0392b" stroke-width="2.0"/>'
                         % (Pc[0] + ox, oy - Pc[1], B[0] + ox, oy - B[1]))
                for pt, lab in ((Pc, "P"), (B, "B")):
                    s.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#c0392b"/>'
                             % (pt[0] + ox, oy - pt[1]))
                    # 两侧 B 已重合于中缝，标签只标一个
                    if lab == "B" and mir < 0:
                        continue
                    labx = pt[0] + ox + (8.0 if mir > 0 else -30.0)
                    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="#c0392b">%s</text>'
                             % (labx, oy - pt[1] - 10, lab))

    s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#e0e6ec" stroke-width="1.4" stroke-dasharray="14 12"/>'
             % (ox, oy - 900, ox, oy + 100))
    s.append('<text x="150" y="150" font-family="sans-serif" font-size="50" font-weight="600" fill="#1a1a1a">'
             '平铺线稿</text>')
    s.append('<text x="150" y="210" font-family="sans-serif" font-size="26" fill="#555">'
             '实线＝前片＋续衽（外襟）｜灰细线＝内襟／内襟续衽｜灰虚线＝后片（共用侧缝与接袖缝，标在后层）</text>')
    s.append('</svg>')
    open(out_svg, "w", encoding="utf-8").write("\n".join(s))

    svg2 = None
    ln = 0.0
    return out_svg, svg2, ln
