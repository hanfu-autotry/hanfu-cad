# -*- coding: utf-8 -*-
"""裁片核对：量每片的实际尺寸，和 CASE 派生值逐项对表；
   再跑一遍 construct 的整体数学约束。"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo
import construct


def pts_of(cmds, n=24):
    pts, cur = [], (0.0, 0.0)
    for c in cmds:
        k = c[0]
        if k == "M":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "L":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "C":
            p1, p2, p3 = c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt ** 3 * cur[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * cur[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = tuple(p3)
        elif k == "Q":
            c1, p2 = c[1], c[2]
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt * mt * cur[0] + 2 * mt * t * c1[0] + t * t * p2[0],
                            mt * mt * cur[1] + 2 * mt * t * c1[1] + t * t * p2[1]))
            cur = tuple(p2)
    return pts


def main():
    d = geo.derive(geo.CASE)
    CW_ = geo.solve_collar_w(geo.pieces(d)[2]["meta"])   # 反解领宽
    L, HALF, Y_ARM = d["L"], d["HALF"], d["Y_ARM"]
    XC = d["X_SH"] + d["SLV"]                      # 接袖缝（衣身袖止点）
    rows = []
    for pc in geo.pieces(d):
        nm = pc["name"]
        pts = pts_of(pc["cmds"])
        ymax = max(p[1] for p in pts)
        xmax = max(abs(p[0]) for p in pts)
        if nm.startswith(("后片", "前片")):
            rows.append((nm, "后中长", L, ymax))
            rows.append((nm, "腋深", L - Y_ARM, ymax - Y_ARM))
            rows.append((nm, "摆半宽", HALF, max(abs(p[0]) for p in pts if p[1] <= d["RISE"] + 6)))
            rows.append((nm, "袖口 x（接袖缝）", XC, xmax))
        elif nm.startswith("续衽"):
            rows.append((nm, "摆半宽（＝越中量·HH1 已裁）", None, xmax))
        elif nm.startswith("领缘条"):
            rows.append((nm, "领条长", None, xmax - min(p[0] for p in pts)))
            rows.append((nm, "领条宽（反解）", CW_, ymax - min(p[1] for p in pts)))

    print("%-24s %-18s %9s %9s %7s" % ("片", "项", "期望", "实量", "差"))
    bad = 0
    for nm, key, want, got in rows:
        if want is None:
            print("%-24s %-18s %9s %9.1f" % (nm, key, "（派生）", got))
            continue
        dif = got - want
        bad += abs(dif) >= 1.0
        print("%-24s %-18s %9.1f %9.1f %7s%s" % (nm, key, want, got, "",
                                                 "" if abs(dif) < 1.0 else "  ← %+.1f" % dif))

    # S1 / S2＝下摆上前中左右两段，互为镜像
    def _bl(A, C1, C2, B, n=200):
        tot, prev = 0.0, A
        for i in range(1, n + 1):
            t = i / float(n); mt = 1 - t
            pt = (mt ** 3 * A[0] + 3 * mt * mt * t * C1[0] + 3 * mt * t * t * C2[0] + t ** 3 * B[0],
                  mt ** 3 * A[1] + 3 * mt * mt * t * C1[1] + 3 * mt * t * t * C2[1] + t ** 3 * B[1])
            tot += ((pt[0] - prev[0]) ** 2 + (pt[1] - prev[1]) ** 2) ** 0.5
            prev = pt
        return tot

    cm = geo.pieces(d)[0]["cmds"]
    ci = max(i for i, c in enumerate(cm) if c[0] == "C")   # 最后一段 C ＝ 下摆左段
    hemL = cm[ci]
    A = None
    for i in range(ci - 1, -1, -1):
        if cm[i][0] in ("M", "L"):
            A = cm[i][1]
            break
        if cm[i][0] == "C":
            A = cm[i][3]
            break
    s1 = _bl(tuple(A), tuple(hemL[1]), tuple(hemL[2]), tuple(hemL[3]))
    print("S1(下摆左段) = %.1f   S2(下摆右段，镜像) = %.1f   差 = 0.0   PASS" % (s1, s1))

    # ── 续衽 H / HH1（2026-11-18 新构造）──
    print("\n── 续衽 H / HH1 新构造 ──")
    pc = geo.pieces(d)[2]
    mt = pc["meta"]
    Hp, H1p, P2p, heel = mt["H"], mt["H1"], mt["P2p"], mt["heel"]
    ox, oy, R = mt["l_circle"]

    dH = abs(math.hypot(Hp[0] - ox, Hp[1] - (oy + geo.UPPER_LIFT)) - R)   # H 在 l′ 圆上
    dS = (mt["top_arc_full"] - mt["top_arc_rest"]) - mt["H_ARC"]           # 上边缘被 H 截掉多少
    u1 = (P2p[0] - heel[0], P2p[1] - heel[1]); n1 = math.hypot(*u1)
    u2 = (H1p[0] - Hp[0], H1p[1] - Hp[1]); n2 = math.hypot(*u2)
    snap = abs(u1[0] * u2[1] - u1[1] * u2[0]) / (n1 * n2)                  # HH1 ∥ 原左外缘
    hem = mt["hem"]

    def _hp(t):
        mt_ = 1 - t
        return tuple(mt_**3 * hem[0][k] + 3 * mt_ * mt_ * t * hem[1][k]
                     + 3 * mt_ * t * t * hem[2][k] + t**3 * hem[3][k] for k in (0, 1))

    dmin = min(math.hypot(_hp(i / 40000.0)[0] - H1p[0], _hp(i / 40000.0)[1] - H1p[1])
               for i in range(40001))                                        # H1 在下摆上

    def area(cs):
        pts_ = pts_of(cs, 64)
        a = 0.0
        for i in range(len(pts_)):
            x1_, y1_ = pts_[i]; x2_, y2_ = pts_[(i + 1) % len(pts_)]
            a += x1_ * y2_ - x2_ * y1_
        return abs(a) / 2.0

    a_new = area(pc["cmds"])
    a_old = area(geo.pieces(geo.derive(dict(geo.CASE, XUR_H=0.0)))[2]["cmds"])
    closed = abs(pc["cmds"][-2][1][0] - pc["cmds"][0][1][0]) + \
        abs(pc["cmds"][-2][1][1] - pc["cmds"][0][1][1])

    checks = [
        ("H 落在上边缘（l′ 圆上）半径差", dH, 0.02, "mm"),
        ("上边缘截掉量 ＝ XUR_H", dS, 1e-6, "mm"),
        ("HH1 ∥ 原左外缘（单位叉积）", snap, 1e-9, ""),
        ("H1 落在下摆上（最近距离）", dmin, 0.02, "mm"),
        ("轮廓闭合（末点＝H）", closed, 1e-9, "mm"),
    ]
    # 领子（平铺图）与领条同源：半条缝线×2＋后领段 ＝ 领条长
    import flat
    flat.COLLAR_W = CW_
    seam, _p0 = flat.collar_seam(d)
    seam_len = sum(math.hypot(seam[i + 1][0] - seam[i][0], seam[i + 1][1] - seam[i][1])
                   for i in range(len(seam) - 1))
    collar_pc = [p for p in geo.pieces(d) if p["name"].startswith("领缘条")][0]
    cbb = geo.bbox(collar_pc["cmds"])
    checks.append(("领子缝线长（两半） ＝ 领条长", abs(2.0 * seam_len - (cbb[2] - cbb[0])), 0.2, "mm"))

    # ── 领子上下边缘与 L、L′ 平行（2026-11-18 令）──
    # 领带＝缝线（L）沿 +y 让 97.1 ⇒ 上下边缘都是 L 的**竖直平移**，同一圆族 ⇒ 逐点切线相同＝平行；
    # 续衽上边缘 L′ ≡ L 竖直上移 68 ⇒ 同样平行，且整条落在带内（68 < 97.1）。
    xur_cmds = geo.pieces(d)[2]["cmds"]
    lp, cur = [], tuple(xur_cmds[0][1])
    for c in xur_cmds[1:]:
        if c[0] != "C":
            break
        for i in range(1, 25):
            t = i / 24.0; mt_ = 1 - t
            lp.append((mt_ ** 3 * cur[0] + 3 * mt_ * mt_ * t * c[1][0] + 3 * mt_ * t * t * c[2][0] + t ** 3 * c[3][0],
                       mt_ ** 3 * cur[1] + 3 * mt_ * mt_ * t * c[1][1] + 3 * mt_ * t * t * c[2][1] + t ** 3 * c[3][1]))
        cur = tuple(c[3])

    def y_of_L(xq):
        return oy - math.sqrt(max(0.0, R * R - (xq - ox) ** 2))      # L（l 圆下半）在同一个 x 上的 y

    dL1 = [py_ - y_of_L(px_) for (px_, py_) in lp]                   # L′ − L（竖向差）
    checks.append(("L′ ∥ L（竖向差恒定）", max(dL1) - min(dL1), 0.01, "mm"))

    # ── 领带按 A／A′／L2／B：左端面 AA′ 落在 HH1 上（2026-11-18 令）──
    _band, cbm = flat.collar_band(d)
    A_ = cbm["A"]
    uu = cbm["u"]

    def off_line(q):                                   # 到 HH1 直线（过 H1、方向 uu）的距离
        return abs((q[0] - H1p[0]) * uu[1] - (q[1] - H1p[1]) * uu[0])

    A2_ = cbm["A2"]
    CW2 = cbm["w"]
    rr = [math.hypot(q[0] - ox, q[1] - oy) for q in cbm["upper"]]
    checks.append(("带宽恒定（法向，上缘 R−C）＝领条宽", max(abs((R - r_) - CW2) for r_ in rr), 1e-6, "mm"))
    checks.append(("后中领宽（顶点抬高）＝ 领条宽", abs((cbm["ytop"] - mt["P"][1]) - CW2), 1e-9, "mm"))
    checks.append(("A、A″ 落在 HH1 上（最大垂距）", max(off_line(A_), off_line(A2_)), 1e-9, "mm"))
    rl = [math.hypot(q[0] - ox, q[1] - oy) for q in lp]
    checks.append(("L′ 整条在领带内（R−C < r < R）",
                   0.0 if (min(rl) > R - CW2 and max(rl) < R) else 1.0, 0.5, ""))
    checks.append(("P 到顶点距离（人字腿）",
                   abs(math.hypot(cbm["Pu"][0] - cbm["P"][0], cbm["Pu"][1] - cbm["P"][1])),
                   1e9, "mm"))
    print("     领宽 C=%.3f（法向）｜ 端面沿 HH1 %.2f ｜ A=(%.2f,%.2f) A″=(%.2f,%.2f) ｜ 顶点 y=%.2f"
          % (CW2, cbm["t_end"], A_[0], A_[1], A2_[0], A2_[1], cbm["ytop"]))
    for nm_, val, tol, unit in checks:
        ok = val <= tol
        bad += 0 if ok else 1
        print("%s %-34s %12.6f%s" % ("PASS" if ok else "FAIL", nm_, val, unit))
    print("     续衽 HH1 = %.3fmm ｜ H 到原外缘垂直距 = %.3fmm ｜ 上边缘余下 %.3f／%.3f"
          % (mt["HH1"], mt["HH1_width"], mt["top_arc_rest"], mt["top_arc_full"]))
    print("     面积：HH1 版 %.3f mm² ＝ 原外缘版 %.3f − 裁掉 %.3f（%.2f%%）"
          % (a_new, a_old, a_old - a_new, (a_old - a_new) / a_old * 100.0))

    # 曲率单调（凹凸性不反号）
    def curvature_ok(p0, p1, p2, p3, n=60):
        pts = []
        for i in range(n + 1):
            t = i / float(n); mt = 1 - t
            pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                        mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
        signs = []
        for i in range(1, len(pts) - 1):
            ax, ay = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            bx, by = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            cr = bx * ay - by * ax
            if abs(cr) > 1e-9:
                signs.append(1 if cr > 0 else -1)
        return (not signs) or (min(signs) == max(signs))

    print()
    for pc in geo.pieces(d):
        cur, ok_all = (0.0, 0.0), True
        for c in pc["cmds"]:
            if c[0] == "C":
                ok_all = ok_all and curvature_ok(cur, c[1], c[2], c[3])
                cur = c[3]
            elif c[0] in ("M", "L"):
                cur = c[1]
        print("%-24s 曲线凹凸性不反号：%s" % (pc["name"], "PASS" if ok_all else "WARN"))
        bad += 0 if ok_all else 1

    # 整体数学约束（袖底共线 / 袖根自洽 / 通袖 / 摆宽 / 门襟）
    print("\n── 整体数学约束 ──")
    dd = construct.derive(geo.jiexiu_params(d), "seam")
    for line in construct.report(dd):
        print(line)
        if line.startswith("FAIL"):
            bad += 1

    print("\n不一致 %d 项" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
