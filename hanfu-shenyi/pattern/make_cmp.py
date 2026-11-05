# -*- coding: utf-8 -*-
"""V2 / V3 同比例对照图（③ 平铺面视图，上下并列）

用法：python make_cmp.py
输出：../out/_cmp_v2_v3.png
中文由 Edge 渲染（与主图同一路径），避免 PIL 字体缺字变成方块。
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

FAB_W, N_PANEL = 500.0, 4
HALF_S = FAB_W * N_PANEL / 2.0          # 1000（通袖半宽）
S = HALF_S * 2                          # 2000
SLIT_HALF, LAPEL_FOLD = 80.0, 40.0
ARMPIT, HEM_HALF = 370.0, 540.0
HOOK_OUT = 60.0
NECK_H = 77.0

# 两档：衣长（＝袖肥＝袖口），成衣总长
CASES = [
    ("V2  深衣 · 宽袖礼服", 624.0, 1872.0, "宽袖 ↔ 腰线正常 ↔ 礼服（及踝）"),
    ("V3  深衣 · 窄袖便服", 195.0, 770.0, "窄袖 ↔ 腰线齐胸 ↔ 便服（普通外套长）"),
]

BLACK, GRAY, GREEN, RED, ORANGE, BLUE = (
    "#1a1a1a", "#6f6f6f", "#1d6b3a", "#b3241c", "#b85400", "#1a4d8f")

GAP = 240.0
PAD_T = 260.0
PAD_L = 320.0
CANVAS_W = S + PAD_L * 2 + 260.0

# 先算高度
_h = PAD_T
_rows = []
for name, lb, gl, _tag in CASES:
    shang = gl - lb
    k = lb / 624.0
    ah, hh = 200.0 * k, 70.0 * k
    _rows.append((name, lb, gl, shang, ah, hh, _h, _tag))
    _h += (lb + shang) + 190.0            # 衣服高 + 标题/标注余量
_h += GAP + 60
TOTAL_H = _h

s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (CANVAS_W, TOTAL_H, CANVAS_W, TOTAL_H))
s.append('<title>深衣 V2 宽袖礼服 / V3 窄袖便服 · 同比例对照</title>')
s.append('<rect width="100%%" height="100%%" fill="#ffffff"/>')
s.append('<text x="%.1f" y="90" font-family="sans-serif" font-size="56" font-weight="600" fill="%s">'
         '深衣 · 同一板型两档 · 同比例对照</text>' % (PAD_L - 120, BLACK))
s.append('<text x="%.1f" y="140" font-family="sans-serif" font-size="30" fill="%s">'
         '衣长 ＝ 袖肥 ＝ 袖口（上衣＝中段布带对折，袖子是它的两端）→ 缩衣长 = 袖口变窄 + 腰线上抬，一次完成</text>'
         % (PAD_L - 120, GRAY))

CX = PAD_L + HALF_S          # 中线画布 x


def fx(x):
    return CX + x


for name, lb, gl, shang, ah, hh, top, tag in _rows:
    # 标题（含橙色一句配档逻辑）
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="40" font-weight="600" fill="%s">'
             '%s<tspan font-size="31" font-weight="400" fill="%s">　｜　%s</tspan></text>'
             % (PAD_L - 120, top + 26, BLACK, name, ORANGE, tag))
    y0 = top + 96.0
    # 肩线 y（衣身顶边）
    ty = y0
    wy = y0 + lb                 # 腰线
    by = y0 + lb + shang         # 摆

    g = ['<g stroke="%s" stroke-width="3" fill="none">' % BLACK]
    # 袖带：两端＝袖口（高 = 衣长），上边＝肩线，下边＝腰线
    g.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f"/>' % (
        fx(-HALF_S), ty, fx(-HALF_S), wy, fx(HALF_S), wy, fx(HALF_S), ty))
    # 肩线（折边）：领条折转段两侧断开
    for a, b in ((-HALF_S, -SLIT_HALF), (-LAPEL_FOLD, LAPEL_FOLD), (SLIT_HALF, HALF_S)):
        g.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (fx(a), ty, fx(b), ty))
    # 拼幅缝
    for i in range(1, N_PANEL):
        xx = -HALF_S + FAB_W * i
        g.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.6" opacity="0.55"/>'
                 % (fx(xx), ty, fx(xx), wy))
    # 裳（正面轮廓）
    g.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f"/>' % (
        fx(-ARMPIT), wy, fx(-HEM_HALF), by, fx(HEM_HALF), by, fx(ARMPIT), wy))
    g.append('</g>')
    s += g

    # 中心：领条 / 后片 / 领条，贯通到摆
    c = ['<g stroke="%s" fill="none">' % BLACK]
    for sx in (-1, 1):
        c.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="3"/>' % (
            fx(sx * SLIT_HALF), ty, fx(sx * SLIT_HALF), by))
    for sx in (-1, 1):
        c.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.6"/>' % (
            fx(sx * LAPEL_FOLD), ty - NECK_H * min(1.0, lb / 624.0), fx(sx * LAPEL_FOLD), by))
    c.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.6" stroke-dasharray="24 14"/>' % (
        fx(0), ty, fx(0), by))
    c.append('</g>')
    s += c

    # 领条折转段（梯形）
    s.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" stroke="%s" stroke-width="3" fill="none"/>' % (
        fx(-SLIT_HALF), ty, fx(-44.5), ty - NECK_H * min(1.0, lb / 624.0),
        fx(44.5), ty - NECK_H * min(1.0, lb / 624.0), fx(SLIT_HALF), ty, BLACK))

    # 腋下：垂线 + 外弯
    a = ['<g stroke="%s" stroke-width="3" fill="none">' % GREEN]
    for sx in (-1, 1):
        xa, xf2 = fx(sx * ARMPIT), fx(sx * (ARMPIT + HOOK_OUT))
        a.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (xa, wy, xa, wy - ah))
        yb = wy - hh
        a.append('  <path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f"/>' % (
            xa, yb, xa, yb + 0.45 * (wy - yb), xa + 0.55 * (xf2 - xa), wy, xf2, wy))
    a.append('</g>')
    s += a

    # 标注
    t = ['<g font-family="sans-serif" font-size="30" fill="%s">' % BLACK]
    t.append('  <text x="%.1f" y="%.1f">衣长 %d（＝袖口）</text>' % (fx(HALF_S + 34), ty + lb * 0.58, round(lb)))
    t.append('  <text x="%.1f" y="%.1f">裳 %d</text>' % (fx(HALF_S + 34), wy + shang * 0.5, round(shang)))
    t.append('</g>')
    s += t

    # 通袖尺寸（衣身上方）
    dy = ty - 104
    s.append('<g stroke="%s" stroke-width="2" fill="none">'
             '<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/></g>'
             % (GRAY, fx(-HALF_S), dy, fx(HALF_S), dy,
                fx(-HALF_S), dy - 14, fx(-HALF_S), dy + 14, fx(HALF_S), dy - 14, fx(HALF_S), dy + 14))
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="30" fill="%s" '
             'text-anchor="middle">通袖 %d（4 幅 × 500）</text>' % (fx(0), dy - 16, BLACK, round(S)))

    # 右侧总长竖向尺寸
    dx = fx(HALF_S) + 190
    s.append('<g stroke="%s" stroke-width="2" fill="none">'
             '<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/></g>'
             % (GRAY, dx, ty, dx, by, dx - 14, ty, dx + 14, ty, dx - 14, by, dx + 14, by))
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="30" fill="%s" '
             'transform="rotate(90 %.1f %.1f)" text-anchor="middle">总长 %d</text>'
             % (dx - 8, (ty + by) / 2, GRAY, dx - 8, (ty + by) / 2, round(lb + shang)))

# 标尺
bx0, by0 = PAD_L - 120, TOTAL_H - 70
s.append('<g stroke="%s" stroke-width="2.4" fill="none">' % BLACK)
for k in range(11):
    hh2 = 26 if k % 5 == 0 else 13
    s.append('<path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh2))
s.append('<path d="M %.1f %.1f L %.1f %.1f"/></g>' % (bx0, by0, bx0 + 1000, by0))
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="%s">'
         '100mm 标尺（两件严格同比例，可直接比对袖口高度与下摆位置）</text>' % (bx0 + 1030, by0 + 8, BLACK))
s.append('</svg>')

svg_path = os.path.join(HERE, "_cmp_v2_v3.svg")
open(svg_path, "w", encoding="utf-8").write("\n".join(s))
png_path = os.path.join(ROOT, "out", "_cmp_v2_v3.png")
preview.render(svg_path, png_path, 0.62)
os.remove(svg_path)
print(json.dumps({"png": png_path, "canvas": [CANVAS_W, round(TOTAL_H, 1)]}, ensure_ascii=False))
