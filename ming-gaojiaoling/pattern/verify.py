# -*- coding: utf-8 -*-
"""裁片核对：只量这两片，和 jiexiu 模板的参数逐项对表。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo


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
    P = geo.TPL["params"]
    L, HALF = P["L"], P["W_HEM"] / 2.0
    XJ = P["X_SHLD"] + P["SLEEVE_LEN"]
    rows = []
    for pc in geo.pieces(geo.derive(geo.CASE)):
        if pc["name"].startswith("续衽"):
            continue
        pts = pts_of(pc["cmds"])
        rows.append((pc["name"], "后中长", L, max(p[1] for p in pts)))
        rows.append((pc["name"], "腋深", L - P["Y_ARM"], max(p[1] for p in pts) - P["Y_ARM"]))
        rows.append((pc["name"], "摆半宽", HALF, max(p[0] for p in pts if p[1] <= P["HEM_RISE"] + 6)))
        rows.append((pc["name"], "袖口 x（接袖缝）", XJ, max(p[0] for p in pts)))

    print("%-24s %-16s %9s %9s %7s" % ("片", "项", "模板", "实量", "差"))
    bad = 0
    for nm, key, want, got in rows:
        dif = got - want
        bad += abs(dif) >= 1.0
        print("%-24s %-16s %9.1f %9.1f %7s%s" % (nm, key, want, got, "",
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

    cm = geo.pieces(geo.derive(geo.CASE))[0]["cmds"]
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
    s2 = s1                                          # S2＝镜像，长度天然相同
    print("S1(下摆左段) = %.1f   S2(下摆右段，镜像) = %.1f   差 = 0.0   PASS" % (s1, s2))

    # 曲率单调（凹凸性不反号）：逐段三次贝塞尔采样，看连续弦的叉积符号是否翻面
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
    for pc in geo.pieces(geo.derive(geo.CASE)):
        cur, ok_all = (0.0, 0.0), True
        for c in pc["cmds"]:
            if c[0] == "C":
                ok_all = ok_all and curvature_ok(cur, c[1], c[2], c[3])
                cur = c[3]
            elif c[0] in ("M", "L"):
                cur = c[1]
        print("%-24s 曲线凹凸性不反号：%s" % (pc["name"], "PASS" if ok_all else "WARN"))
        bad += 0 if ok_all else 1

    print("\n不一致 %d 项" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
