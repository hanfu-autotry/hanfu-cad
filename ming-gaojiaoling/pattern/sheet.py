# -*- coding: utf-8 -*-
"""裁片图排版 + SVG/pieces.json 输出（只用标准库）"""
import json
import math
import os

import geo

GAP = 200.0
MARGIN = 420.0
MAXW = 2400.0
TITLE_H = 520.0

INK = "#1a1a1a"
RED = "#c0392b"
BLUE = "#1f5fa8"
GRAY = "#8a8a8a"
GREEN = "#1e7a4a"


def sample(cmds, n=24):
    pts, cur = [], (0.0, 0.0)
    for c in cmds:
        k = c[0]
        if k == "M":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "L":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "C":
            p0, p1, p2, p3 = cur, tuple(c[1]), tuple(c[2]), tuple(c[3])
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = p3
        elif k == "Q":
            p0, c1, p2 = cur, tuple(c[1]), tuple(c[2])
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt * mt * p0[0] + 2 * mt * t * c1[0] + t * t * p2[0],
                            mt * mt * p0[1] + 2 * mt * t * c1[1] + t * t * p2[1]))
            cur = p2
    return pts


def real_bbox(cmds):
    pts = sample(cmds)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def path_d(cmds, ox, oy):
    """服装坐标（y 向上）→ 页面坐标（y 向下）"""
    out = []
    for c in cmds:
        k = c[0]
        if k == "Z":
            out.append("Z"); continue
        if k == "M":
            out.append("M %.1f %.1f" % (c[1][0] + ox, oy - c[1][1]))
        elif k == "L":
            out.append("L %.1f %.1f" % (c[1][0] + ox, oy - c[1][1]))
        elif k == "C":
            a, b, e = c[1], c[2], c[3]
            out.append("C %.1f %.1f %.1f %.1f %.1f %.1f" % (
                a[0] + ox, oy - a[1], b[0] + ox, oy - b[1], e[0] + ox, oy - e[1]))
        elif k == "Q":
            a, e = c[1], c[2]
            out.append("Q %.1f %.1f %.1f %.1f" % (a[0] + ox, oy - a[1], e[0] + ox, oy - e[1]))
    return " ".join(out)


def place(sheet, maxw=MAXW):
    """逐片排布：把每片按 bbox 左上角对齐到行内"""
    placed, cur_x, cur_y, row_h = [], MARGIN, MARGIN, 0.0
    for p in sheet:
        x0, y0, x1, y1 = real_bbox(p["cmds"])
        w, h = x1 - x0, y1 - y0
        if cur_x + w > maxw and cur_x > MARGIN:
            cur_x, cur_y, row_h = MARGIN, cur_y + row_h + GAP, 0.0
        ox, oy = cur_x - x0, cur_y + y1
        p["_ox"], p["_oy"] = ox, oy
        p["_box"] = (cur_x, cur_y, cur_x + w, cur_y + h)
        placed.append(p)
        cur_x += w + GAP
        row_h = max(row_h, h)
    return placed, cur_y + row_h


def write_sheet(d, sheet, out_svg, title, subtitle, notes):
    placed, body_h = place(sheet)
    total_w = MAXW + 2 * MARGIN
    total_h = body_h + MARGIN + TITLE_H

    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (total_w, total_h, total_w, total_h),
         '<title>%s</title>' % title,
         '<rect width="100%%" height="100%%" fill="#ffffff"/>',
         '<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7"'
         ' orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.1"/></marker></defs>'
         % GRAY]

    # 轮廓
    s.append('<g id="OUTLINE" stroke="%s" stroke-width="2.2" fill="none" stroke-linejoin="round">' % INK)
    for p in placed:
        s.append('  <path id="%s_ot" data-qty="%d" d="%s"/>' % (p["name"], p["qty"], path_d(p["cmds"], p["_ox"], p["_oy"])))
    s.append('</g>')

    # 刀口
    s.append('<g id="NOTCH" stroke="%s" stroke-width="2.6">' % RED)
    for p in placed:
        for nx, ny in p["notches"]:
            px, py = nx + p["_ox"], p["_oy"] - ny
            s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>' % (
                px - 10, py - 10, px + 10, py + 10, px - 10, py + 10, px + 10, py - 10))
    s.append('</g>')

    # 片内标记线（前中缝、续衽线等）
    s.append('<g id="MARK" stroke="%s" stroke-width="1.6" stroke-dasharray="16 10" fill="none">' % BLUE)
    for p in placed:
        for mk in p.get("marks") or []:
            d_ = "M %.1f %.1f" % (mk[0][0] + p["_ox"], p["_oy"] - mk[0][1])
            for q in mk[1:]:
                d_ += " L %.1f %.1f" % (q[0] + p["_ox"], p["_oy"] - q[1])
            s.append('  <path d="%s"/>' % d_)
    s.append('</g>')

    # 辅助实线（l' 之类，实线但细）
    s.append('<g id="AUX_PATH" stroke="%s" stroke-width="1.3" fill="none">' % GRAY)
    for p in placed:
        for mk in p.get("aux") or []:
            d_ = "M %.1f %.1f" % (mk[0][0] + p["_ox"], p["_oy"] - mk[0][1])
            for q in mk[1:]:
                d_ += " L %.1f %.1f" % (q[0] + p["_ox"], p["_oy"] - q[1])
            s.append('  <path d="%s"/>' % d_)
    s.append('</g>')

    # 布纹
    s.append('<g id="GRAIN" stroke="%s" stroke-width="1.6">' % GREEN)
    for p in placed:
        x0, y0, x1, y1 = p["_box"]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        ln = min(max(x1 - x0, 160.0), max(y1 - y0, 160.0)) * 0.55
        gx, gy = p["grain"]
        n = math.hypot(gx, gy) or 1.0
        gx, gy = gx / n, -gy / n
        ax, ay = cx - gx * ln / 2, cy - gy * ln / 2
        bx, by = cx + gx * ln / 2, cy + gy * ln / 2
        s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-end="url(#ar)"/>' % (ax, ay, bx, by))
    s.append('</g>')

    # 标注（一律推到片外：沿「片中 → 尺寸线中点」方向外移，带引出线）
    s.append('<g id="DIM" stroke="%s" stroke-width="0.9" fill="%s" font-family="sans-serif" font-size="26">' % (GRAY, GRAY))
    for p in placed:
        bx0, by0, bx1, by1 = p["_box"]
        cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
        for dm in p["dims"]:
            a, b, txt = dm[1], dm[2], dm[3]
            ax, ay = a[0] + p["_ox"], p["_oy"] - a[1]
            bx, by = b[0] + p["_ox"], p["_oy"] - b[1]
            mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
            vx, vy = mx - cx, my - cy
            n = math.hypot(vx, vy) or 1.0
            off = 80.0
            ax2, ay2 = ax + vx / n * off, ay + vy / n * off
            bx2, by2 = bx + vx / n * off, by + vy / n * off
            s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f" fill="none" stroke-width="0.7"/>'
                     % (ax, ay, ax2, ay2, bx, by, bx2, by2))
            s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-start="url(#ar)" marker-end="url(#ar)" fill="none"/>'
                     % (ax2, ay2, bx2, by2))
            rot = math.degrees(math.atan2(by2 - ay2, bx2 - ax2))
            if rot > 90:
                rot -= 180
            elif rot < -90:
                rot += 180
            s.append('  <text x="%.1f" y="%.1f" text-anchor="middle" transform="rotate(%.1f %.1f %.1f)"'
                     ' stroke="none">%s</text>' % ((ax2 + bx2) / 2, (ay2 + by2) / 2, rot,
                                                   (ax2 + bx2) / 2, (ay2 + by2) / 2, txt))
    s.append('</g>')

    # 片名
    s.append('<g id="LABEL" fill="%s" font-family="sans-serif">' % INK)
    for i, p in enumerate(placed):
        x0, y0 = p["_box"][0], p["_box"][1]
        s.append('  <text x="%.1f" y="%.1f" font-size="34" font-weight="600">%02d %s ×%d</text>'
                 % (x0, y0 - 46, i + 1, p["name"], p["qty"]))
        if p.get("note"):
            s.append('  <text x="%.1f" y="%.1f" font-size="24" fill="%s">%s</text>'
                     % (x0, y0 - 14, GRAY, p["note"]))
    s.append('</g>')

    # 图签
    ty = body_h + MARGIN * 0.5
    s.append('<g id="BLOCK" stroke="%s" stroke-width="1.6" fill="none">' % INK)
    s.append('  <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (MARGIN, ty, total_w - 2 * MARGIN, TITLE_H - 110))
    s.append('</g>')
    s.append('<g font-family="sans-serif" fill="%s">' % INK)
    s.append('  <text x="%.1f" y="%.1f" font-size="44" font-weight="600">%s</text>' % (MARGIN + 40, ty + 78, title))
    s.append('  <text x="%.1f" y="%.1f" font-size="26" fill="%s">%s</text>' % (MARGIN + 40, ty + 128, GRAY, subtitle))
    y = ty + 178
    for ln in notes:
        s.append('  <text x="%.1f" y="%.1f" font-size="27">%s</text>' % (MARGIN + 40, y, ln))
        y += 40
    s.append('</g>')

    # 100mm 标尺
    bx0, by0 = MARGIN + 40, ty + TITLE_H - 150
    s.append('<g id="SCALE" stroke="%s" stroke-width="2.2" fill="none">' % INK)
    for k in range(11):
        hh = 30 if k % 5 == 0 else 16
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0, by0, bx0 + 1000, by0))
    s.append('</g>')
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="25" fill="%s">'
             '100mm 校验标尺（1:1 打印后实测，误差应 ≤0.5mm）</text>' % (bx0, by0 + 44, INK))
    s.append('</svg>')

    os.makedirs(os.path.dirname(out_svg) or ".", exist_ok=True)
    open(out_svg, "w", encoding="utf-8").write("\n".join(s))

    side = out_svg.rsplit(".", 1)[0] + ".pieces.json"
    json.dump({
        "params": {k: v for k, v in d.items() if isinstance(v, (int, float))},
        "resolved": {k: round(v, 2) for k, v in d.items() if isinstance(v, float)},
        "canvas": [total_w, total_h],
        "pieces": [dict(name=p["name"], qty=p["qty"], ox=p["_ox"], oy=p["_oy"],
                        box=[round(v, 1) for v in p["_box"]],
                        cmds=p["cmds"], grain=p["grain"], marks=p.get("marks") or [],
                        notches=[list(n) for n in p["notches"]]) for p in placed],
    }, open(side, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    return dict(svg=out_svg, side=side, size=[total_w, total_h],
                pieces=[dict(name=p["name"], qty=p["qty"],
                             w=round(p["_box"][2] - p["_box"][0], 1),
                             h=round(p["_box"][3] - p["_box"][1], 1)) for p in placed])
