# -*- coding: utf-8 -*-
"""直领对襟 · 平铺预览（**只做正面线稿**，白底纯黑线，不填色、不做背视）

    python pattern/flat.py
      → out/平铺预览.svg

画的就是 `hanfu-shenyi` 原始直领交襟衣 V1 ③「成衣平铺」那一格的线：
原始直领是通裁（整块对折），这里是分裁（前后片），**除剪裁方式外产物几乎一样**，
所以平铺只看领襟关系：
  外轮廓 ＝ 后片（半 ×2 合成整片）
  中央四条竖线 ＝ 剪开线 ±80（前襟边）＋ 领条内边 ±40
  后中缝 ＝ x=0 虚线（下摆→肩线，不进领口）
  顶边在 ±40…±80 断开 —— 领条从那里横跨过去
  转折处 ＝ 领条在领口立起来：外缘由 ±80 斜收到 ±44.5（高 77），
           而**内缘 ±40 是一直直通到顶的**（V1 就是这么画的），
           所以立起那段是"外缘收、内缘直"，不是一块实心梯形。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet

INK, GRAY = "#1a1a1a", "#6f6f6f"

W, H = 2200, 1400
OX, OY = W / 2.0, 1090.0            # 前中 / 下摆基线


def txt(x, y, s, size=22, color=INK, anchor="start", weight=None):
    w = ' font-weight="600"' if weight else ""
    return ('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" '
            'fill="%s" text-anchor="%s"%s>%s</text>' % (x, y, size, color, anchor, w, s))


def poly(pts):
    d = "M %.1f %.1f" % (OX + pts[0][0], OY - pts[0][1])
    for p in pts[1:]:
        d += " L %.1f %.1f" % (OX + p[0], OY - p[1])
    return d + " Z"


def seg(a, b, w=2.2, dash=None, color=INK):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="%.1f" '
            'fill="none" stroke-linecap="round"%s/>'
            % (OX + a[0], OY - a[1], OX + b[0], OY - b[1], color, w, d))


# ── 几何（全部来自 geo）────────────────────────────────────────────
Q = geo.params()
P = {p["name"]: p for p in geo.step2_pieces(Q)}
back_half = sheet.sample(P["后片"]["cmds"], 32)
back_whole = back_half + list(reversed([(-x, y) for x, y in back_half]))

L = max(y for _, y in back_whole)          # 肩线
HW = max(x for x, _ in back_whole)         # 半宽
CUT = geo.slit_half(Q)                     # 80 剪开线（前襟边）
BAND = Q["LAPEL_FOLD"]                     # 40 领条内边（压边可见宽）
TOP_HALF = geo.NECK_TOP_HALF               # 44.5 立起段顶半宽
NECK_H = Q["NECK_H"]                       # 77 立起露出高
TOP = L + NECK_H                           # 立起段顶边 y

s = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
     'viewBox="0 0 %d %d">' % (W, H, W, H),
     '<rect width="100%" height="100%" fill="#ffffff"/>',
     txt(56, 62, "直领对襟 · 平铺（正面线稿）", 38, INK, weight=1),
     txt(56, 102, "外轮廓＝后片（半 ×2 合成整片）　中央：剪开线 ±%.0f ／ 领条内边 ±%.0f ／ "
                  "后中缝虚线　顶部：领条外缘 ±%.0f 斜收到 ±%.0f（立起 %.0f）"
                  % (CUT, BAND, CUT, TOP_HALF, NECK_H), 21, GRAY)]

# 1 外轮廓（后片整片）
s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" '
         'stroke-linejoin="round"/>' % (poly(back_whole), INK))

# 2 顶边在 ±40…±80 断开：领条从那里横跨过去
for sx in (-1, 1):
    a, b = sorted((sx * BAND, sx * CUT))
    s.append(seg((a, L), (b, L), 6.0, color="#ffffff"))

# 3 中央竖线
for sx in (-1, 1):
    s.append(seg((sx * CUT, 0), (sx * CUT, L), 3.0))        # 剪开线（前襟边）
    s.append(seg((sx * BAND, 0), (sx * BAND, TOP), 1.6))    # 领条内边：直通到顶
# 后中缝（虚线，只到下摆→肩线）
s.append(seg((0, 0), (0, L), 1.6, "26 14"))

# 4 转折处：领条在领口立起 —— 外缘 ±80 斜收到 ±44.5，顶边连过去
#    （内缘 ±40 已在第 3 步直通到顶，所以这里只画外缘两条斜边 + 顶边）
for sx in (-1, 1):
    s.append(seg((sx * CUT, L), (sx * TOP_HALF, TOP), 2.6))
s.append(seg((-TOP_HALF, TOP), (TOP_HALF, TOP), 2.6))

# 5 布纹（两侧各一道，细虚线）
for sx in (-1, 1):
    x = sx * (CUT + 250)
    s.append(seg((x, L * 0.20), (x, L * 0.70), 1.4, "18 10", GRAY))

# 6 标注（都在衣外）
s.append(txt(OX - CUT - 14, OY - TOP + 6, "立起 %.0f" % NECK_H, 19, INK, "end"))
s.append(txt(OX + TOP_HALF + 12, OY - TOP - 4, "顶 %.0f" % (TOP_HALF * 2), 19, INK))
s.append(txt(OX + CUT + 24, OY - L * 0.62, "剪开线 ±%.0f（前襟边）" % CUT, 19, INK))
s.append(txt(OX + BAND + 22, OY - L * 0.30, "领条内边 ±%.0f（压边可见）" % BAND, 19, INK))
s.append(txt(OX - BAND - 16, OY - L * 0.42, "后中缝", 19, GRAY, "end"))

s.append(txt(OX, OY + 52, "中央由里向外：露出后片 %.0f ｜ 领条 %.0f ｜ 剪开线 ±%.0f"
             % (BAND * 2, BAND, CUT), 23, INK, "middle"))
s.append(txt(OX, OY + 88, "平铺宽 %.0f（2 × %.0f）　高（到下摆）%.0f　立起再加 %.0f"
             % (HW * 2, HW, L, NECK_H), 21, GRAY, "middle"))

# 平铺宽尺寸线
s.append(seg((-HW, -96), (HW, -96), 1.0, color=GRAY))
s.append(seg((-HW, -86), (-HW, -106), 1.0, color=GRAY))
s.append(seg((HW, -86), (HW, -106), 1.0, color=GRAY))

# 100mm 标尺
bx, by = 56, H - 44
s.append('<g id="SCALE" stroke="%s" stroke-width="2.2" fill="none">' % INK)
for k in range(11):
    hh = 28 if k % 5 == 0 else 15
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx + k * 100, by, bx + k * 100, by - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx, by, bx + 1000, by))
s.append('</g>')
s.append(txt(bx, by + 30, "100mm 校验标尺（1:1 打印后实测，误差应 ≤0.5mm）", 20, INK))
s.append('</svg>')

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)
fn = os.path.join(OUT, "平铺预览.svg")
open(fn, "w", encoding="utf-8").write("\n".join(s))
print(fn)
print("平铺 %.0f × %.0f ｜ 剪开线 ±%.0f ｜ 领条内边 ±%.0f ｜ 立起 %.0f ｜ 顶 %.0f"
      % (HW * 2, L, CUT, BAND, NECK_H, TOP_HALF * 2))
