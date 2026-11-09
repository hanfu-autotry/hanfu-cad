# -*- coding: utf-8 -*-
"""拼合平铺图：把裁片按穿着状态合起来。

① 前视（交襟）—— 右襟在下、左襟压上；领缘条 40 宽平贴领口一圈（横卧领）
② 后视（平铺）—— 后片半 ×2 + 接袖 ×2，领缘条沿后领口

**不变量**：装配只做「摆放」（镜像/压叠顺序），不改裁片几何。
"""
import math

import geo
import sheet

STYLE = {
    "cut":   dict(stroke="#1a1a1a", width=2.6, dash="", fill="none"),
    "over":  dict(stroke="#1a1a1a", width=3.0, dash="", fill="#fcfcfc"),
    "under": dict(stroke="#7c8b9e", width=1.8, dash="", fill="none"),
    "band":  dict(stroke="#8a5a1e", width=1.8, dash="", fill="#f6eddc"),
    "ghost": dict(stroke="#cfcfcf", width=1.5, dash="24 12", fill="none"),
    "tie":   dict(stroke="#c0392b", width=1.6, dash="", fill="#fbe6e3"),
}


def _shift(cmds, dx, dy=0.0):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
        else:
            out.append([c[0]] + [[p[0] + dx, p[1] + dy] for p in c[1:]])
    return out


def neck_back_path(d, n=16):
    HN, L, DIP = d["NECKW"] / 2.0, d["L"], d["BACKDIP"]
    return [(HN - 2 * HN * i / float(n), L - DIP * 4 * (i / float(n)) * (1 - i / float(n)))
            for i in range(n + 1)]


def offset_band(path, w, ref):
    """双线带：路径 + 向内偏 w 的一条。ref＝内部参考点，用来决定法线朝内"""
    out_a, out_b = [], []
    for i, p in enumerate(path):
        q = path[min(i + 1, len(path) - 1)]
        r = path[max(i - 1, 0)]
        tx, ty = q[0] - r[0], q[1] - r[1]
        n = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / n, tx / n
        if (ref[0] - p[0]) * nx + (ref[1] - p[1]) * ny < 0:
            nx, ny = -nx, -ny
        ylo, yhi = min(q[1] for q in path), max(q[1] for q in path)
        out_a.append(p)
        out_b.append((p[0] + nx * w, min(max(p[1] + ny * w, ylo), yhi)))
    cmds = [["M", list(out_a[0])]]
    for p in out_a[1:]:
        cmds.append(["L", list(p)])
    for p in reversed(out_b):
        cmds.append(["L", list(p)])
    cmds.append(["Z"])
    return cmds


def band_front(d):
    """领缘条：左门襟底 → 左领口 → 后领口 → 右领口 → 右门襟底，向衣内偏 40"""
    L, YNB, HN, XU = d["L"], d["Y_NECKBOT"], d["NECKW"] / 2.0, d["XUREN"]
    hy = geo.hem_y(XU, d["HALF"], d["RISE"])
    path = [(XU, hy), (0.0, YNB), (-HN, L)] + neck_back_path(d)[1:] + [(HN, L), (0.0, YNB), (-XU, hy)]
    return offset_band(path, d["COL_W"], (0.0, 300.0))


def band_back(d):
    return offset_band(neck_back_path(d), d["COL_W"], (0.0, 300.0))


def layers(d, view="front"):
    """装配只做摆放，不改几何。

    片序（geo.pieces 的返回顺序）：
      P0 前片（中缝右边）  P1 内襟（前片镜像）  P2 续衽（中缝左边）
      P3 内襟续衽（续衽镜像）  P4 后片半  P5 领缘条
    一件前身＝前片＋续衽（外襟）；内襟是其镜像那一套。
    """
    P = geo.pieces(d)
    front, inner = P[0]["cmds"], P[1]["cmds"]
    xur, inner_xur = P[2]["cmds"], P[3]["cmds"]
    back = P[4]["cmds"]

    if view == "back":
        return [dict(name="后片半（左）", cmds=geo.mirror(back), kind="cut"),
                dict(name="后片半（右）", cmds=back, kind="cut"),
                dict(name="领缘条", cmds=band_back(d), kind="band")]

    return [dict(name="后片（影·右）", cmds=back, kind="ghost"),
            dict(name="后片（影·左）", cmds=geo.mirror(back), kind="ghost"),
            dict(name="内襟续衽（下）", cmds=inner_xur, kind="under"),
            dict(name="内襟（下）", cmds=inner, kind="under"),
            dict(name="续衽（上）", cmds=xur, kind="over"),
            dict(name="前片（上）", cmds=front, kind="over"),
            dict(name="领缘条（横卧）", cmds=band_front(d), kind="band"),
            dict(name="系带（长 450）", cmds=[["M", [-10.0, 566.0]], ["L", [-440.0, 470.0]],
                                         ["L", [-438.0, 490.0]], ["L", [-8.0, 586.0]], ["Z"]], kind="tie"),
            dict(name="系带（短 310）", cmds=[["M", [-10.0, 520.0]], ["L", [-300.0, 450.0]],
                                         ["L", [-298.0, 470.0]], ["L", [-8.0, 540.0]], ["Z"]], kind="tie")]


def write(d, out_svg):
    L = d["L"]
    panels = [("front", "前视（交襟：右襟在下、左襟压上）", 1300.0),
              ("back", "后视（平铺）", 2700.0)]
    W, H = 2600.0, 3050.0
    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="100%" height="100%" fill="#ffffff"/>']
    for v, cap, offy in panels:
        offx = W / 2.0
        s.append('<g id="AXIS_%s" stroke="#e3e8ee" stroke-width="1.4" stroke-dasharray="14 12">' % v)
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (offx, offy - L - 200, offx, offy + 100))
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (offx - 1200, offy - L, offx + 1200, offy - L))
        s.append('</g>')
        for lay in layers(d, v):
            st = STYLE[lay["kind"]]
            s.append('  <path d="%s" stroke="%s" stroke-width="%.1f" fill="%s"%s/>' % (
                sheet.path_d(lay["cmds"], offx, offy), st["stroke"], st["width"], st["fill"],
                (' stroke-dasharray="%s"' % st["dash"]) if st["dash"] else ""))
        s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="38" fill="#1a1a1a">%s</text>'
                 % (offx - 1200, offy + 220, cap))
    s.append('<text x="160" y="140" font-family="sans-serif" font-size="50" font-weight="600" fill="#1a1a1a">'
             '明制高交领（横卧领）· 拼合平铺图</text>')
    s.append('<text x="160" y="200" font-family="sans-serif" font-size="28" fill="#555">'
             '直领对襟底子 ＋ 续衽直拼　｜　通袖 %.0f ／ 后中长 %.0f ／ 摆半宽 %.0f ／ 袖根 %.0f ／ 袖口 %.0f ／ 门襟 %.0f ／ 开领条宽 %.0f ／ 领缘条 %.0f×%.0f'
             '　　净版 mm　（灰虚线＝后片影；灰细线＝压在下面那襟）</text>'
             % (d["S"], d["L"], d["HALF"], d["SEAM_H"], d["CUF"], d["LAP"], d["NECKW"], d["COL_L"], d["COL_W"]))
    s.append('</svg>')
    open(out_svg, "w", encoding="utf-8").write("\n".join(s))
    return out_svg
