# -*- coding: utf-8 -*-
"""
原始直领交襟衣 V1B · 裁片/排料图（V1 的双长变体）
────────────────────────────────────────────────────────────────
和 V1 的唯一差别：**四块布不再一样高**。

  V1  ：**四块布**（每块一幅 500 × 1248，三道拼幅缝 x = ±500 / 0）等高横拼成一片料 2000 × 1248，
        上下对折 → 衣长 ＝ 袖口高 ＝ 624（袖底与下摆是同一条线，所以两个数必然相等）
  V1B ：同样四块、同样的缝位置、同样一次对折；幅宽仍 **500（上古幅宽，不动）**，通袖仍 2000，
        只有经向长分两种：
        内侧块 ×2（贴中缝）经向 ＝ 2 × **衣身长**（对折后 ＝ 成衣衣长，走中缝那一条）
        外侧块 ×2（靠袖口）经向 ＝ 2 × **接袖长**（对折后 ＝ 袖口高）

  ★ **四块布共用同一条折线（肩线 y ＝ 衣身长）**：外侧块只是「短」，两头各短一截，
    居中骑在折线上，短出来的部分全落在**袖口那一头**。所以袖在肩上，不在下摆
    （2026-11-27 修：前一版把外侧块对齐下摆，袖子就接反了，成了倒悬）。

默认值＝厂商版（`hanfu-cad` vendor 男 M）：衣身长 770（衣长，以中缝长为准）／
接袖长 277.2（**袖根长** ＝ 衣长 770 − 腋深 492.8，不是袖口 160）。两个旋钮互不影响：
衣身长只动内侧块与开领弦长（→ 领条长跟着变），接袖长只动外侧块与袖口高。

折后（成衣）按 y 从下往上两段：
  0 … 衣身长−接袖长   侧缝段（x ＝ ±500，前片缝后片）
  衣身长−接袖长 … 衣身长  袖段（外侧块在这里，袖口高 ＝ 接袖长；x ＝ ±1000 是袖口）

★ 所以 V1 → V1B 没有「加块」「加缝」这一步：四块布与三条缝的位置一模一样，
  变的是**外侧块两头各短 L_BODY − JS**，于是 x = ±500 那条边被切成两段重新赋义
  （y (L_BODY−JS)…L_BODY ＝ 接袖缝，y 0…(L_BODY−JS) ＝ 侧缝），
  并且**袖底从下摆抬到了 y ＝ L_BODY − JS**（默认 492.8 ＝ 厂商腋点高）。

口径仍是**古制**：一片料（四块拼成）＋ 一次折叠。环境变量 HANFU_PARAMS 覆盖参数；HANFU_OUT 指定产物路径。
"""
import math, os, json
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collar

_DEF = dict(
    FAB_W=500.0,        # 幅宽（上古幅宽，锁死 500）
    N_PANEL=4,          # 总幅数：内侧 2 ＋ 外侧 2
    L_BODY=770.0,       # ★衣身长（＝对折后衣长＝中缝长）—— 控内侧块
    JS=277.2,           # ★接袖长（＝对折后袖口高＝袖根长）—— 控外侧块
                        #   默认取厂商版袖根长：衣长 770 − 腋深 492.8（hanfu-cad vendor 男 M）
                        #   ⇒ 袖底落在腋点高 492.8，袖管是直的（不再是 160 的细管）
    NECK_W=160.0,       # ★领口宽（＝前中剪开两道之间的间距）
    COLLAR_W=30.0,      # ★领条宽（＝立起高）
)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

FAB_W = P["FAB_W"]; N_PANEL = int(P["N_PANEL"])
L_BODY = P["L_BODY"]; JS = P["JS"]
NECK_W = P["NECK_W"]; COLLAR_W = P["COLLAR_W"]

if JS > L_BODY:
    raise SystemExit("接袖长 %.0f > 衣身长 %.0f：袖口比衣身还高，外侧块无处安放，先调衣身长" % (JS, L_BODY))

N_SIDE = N_PANEL // 2                 # 每侧 2 幅（内 1 ＋ 外 1）
X_SPLIT = FAB_W                       # 内外缝位置：中缝 → 内外缝 ＝ 1 幅
HALF_S = FAB_W * N_SIDE               # 单侧总长 ＝ 1000
S = HALF_S * 2                        # 通袖 2000

CLOTH_H = L_BODY * 2                  # 内侧块经向长（展开）
OUT_H = JS * 2                        # 外侧块经向长（展开）
Y_FOLD = L_BODY                       # 折线（肩线）—— 四块共用
Y_OUT_LO = L_BODY - JS                # 外侧块展开下界（折后 ＝ 袖底）
Y_OUT_HI = L_BODY + JS                # 外侧块展开上界（折后 ＝ 肩线的另一层）
Y_ARM = L_BODY - JS                   # 折后：袖底下缘，侧缝与接袖缝的分界

SLIT_HALF = NECK_W / 2.0
_CG = collar.geom(SLIT_HALF, L_BODY, COLLAR_W)
EDGE_LEN, N_X, N_Y = _CG["edge"], _CG["nx"], _CG["ny"]
COLLAR_L, NTH, NECK_H = _CG["length"], _CG["top_half"], _CG["stand"]
LAPEL_FOLD = COLLAR_W

# ── 裁片 ───────────────────────────────────────────────────────────
def body_inner():
    """内侧布 ×2：幅宽 500 × 经向 2×衣身长；贴中缝，骑在折线上"""
    return {
        "name": "内侧布", "qty": 2, "grain": (0, 1),
        "cmds": [("M", (0, 0)), ("L", (FAB_W, 0)),
                 ("L", (FAB_W, CLOTH_H)), ("L", (0, CLOTH_H)), ("Z",)],
        "seams": [],
        "notches": [(0, 0), (SLIT_HALF, Y_FOLD), (0, Y_FOLD), (FAB_W, Y_FOLD), (FAB_W, Y_ARM)],
        "dims": [("L", (0, 0), (FAB_W, 0), "幅宽 %d" % round(FAB_W)),
                 ("L", (FAB_W + 45, 0), (FAB_W + 45, CLOTH_H),
                  "经向 %d ＝ 2 × 衣身长 %d" % (round(CLOTH_H), round(L_BODY)))],
    }


def body_outer():
    """外侧布 ×2：幅宽 500 × 经向 2×接袖长；同一条折线居中，上下各 接袖长"""
    return {
        "name": "外侧布", "qty": 2, "grain": (0, 1),
        "cmds": [("M", (0, 0)), ("L", (FAB_W, 0)),
                 ("L", (FAB_W, OUT_H)), ("L", (0, OUT_H)), ("Z",)],
        "seams": [],
        "notches": [(FAB_W, JS), (0, JS), (FAB_W, OUT_H)],
        "dims": [("L", (0, 0), (FAB_W, 0), "幅宽 %d" % round(FAB_W)),
                 ("L", (FAB_W + 45, 0), (FAB_W + 45, OUT_H),
                  "经向 %d ＝ 2 × 接袖长 %d" % (round(OUT_H), round(JS)))],
    }


def collar_piece():
    return {
        "name": "领条", "qty": 1, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (COLLAR_L, 0)),
                 ("L", (COLLAR_L, COLLAR_W)), ("L", (0, COLLAR_W)), ("Z",)],
        "seams": [], "notches": [(COLLAR_L / 2 - 80, 0), (COLLAR_L / 2 + 80, 0)],
        "dims": [("L", (0, 0), (COLLAR_L, 0), "领条 %d × %d" % (round(COLLAR_L), round(COLLAR_W)))],
    }


PIECES = [body_inner(), body_outer(), collar_piece()]

# ── 布局 ───────────────────────────────────────────────────────────
MARGIN = 170.0
CANVAS_W = 3400.0
MAIN_OX = CANVAS_W / 2.0
MAIN_OY = 380.0
LEG_H = 640.0
FLAT_OY = MAIN_OY + CLOTH_H + LEG_H + 250
FLAT_H = L_BODY
COLLAR_OY = FLAT_OY + FLAT_H + 540
TOTAL_H = COLLAR_OY + 320 + 300

placed = []
for p in PIECES:
    if p["name"] == "内侧布":
        p["_ox"], p["_oy"] = MAIN_OX, MAIN_OY
        box = (MAIN_OX - FAB_W, MAIN_OY, MAIN_OX + FAB_W, MAIN_OY + CLOTH_H)
    elif p["name"] == "外侧布":
        p["_ox"], p["_oy"] = MARGIN + COLLAR_L + 320, COLLAR_OY
        box = (p["_ox"], COLLAR_OY, p["_ox"] + FAB_W, COLLAR_OY + OUT_H)
    else:
        p["_ox"], p["_oy"] = MARGIN, COLLAR_OY
        box = (MARGIN, COLLAR_OY, MARGIN + COLLAR_L, COLLAR_OY + COLLAR_W)
    p["_box"] = box
    placed.append(p)

# ── SVG ────────────────────────────────────────────────────────────
BLACK, RED, BLUE = "#1a1a1a", "#b3241c", "#1a4d8f"
GRAY, GREEN, ORANGE = "#6f6f6f", "#1d6b3a", "#b85400"
s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (CANVAS_W, TOTAL_H, CANVAS_W, TOTAL_H))
s.append('<title>原始直领交襟衣 V1B · 四块布双长（衣身长 / 接袖长）</title>')
s.append('<rect width="100%" height="100%" fill="#ffffff"/>')

def X(x): return x + MAIN_OX
def Y(y): return MAIN_OY + (CLOTH_H - y)

def seg(x1, y1, x2, y2, color, w=2.0, dash=""):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="%.1f" fill="none"%s/>'
            % (X(x1), Y(y1), X(x2), Y(y2), color, w, d))

def txt(x, y, t, size=30, color=BLACK, anchor="start", weight=None):
    wt = ' font-weight="600"' if weight else ""
    return ('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" fill="%s" '
            'text-anchor="%s"%s>%s</text>' % (X(x), Y(y), size, color, anchor, wt, t))

# ---- 主图：四块布（外侧块骑在折线上）----
s.append('<g id="CLOTH" stroke="%s" stroke-width="3" fill="none" stroke-linejoin="round">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-FAB_W), Y(0), X(FAB_W), Y(0), X(FAB_W), Y(CLOTH_H), X(-FAB_W), Y(CLOTH_H)))
for sx in (-1, 1):
    x0, x1 = sx * X_SPLIT, sx * HALF_S
    s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
        X(x0), Y(Y_OUT_LO), X(x1), Y(Y_OUT_LO), X(x1), Y(Y_OUT_HI), X(x0), Y(Y_OUT_HI)))
s.append('</g>')

# 一条折线（肩线）：横穿四块
s.append('<g id="FOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="46 16 10 16">' % ORANGE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 40), Y(Y_FOLD), X(HALF_S + 40), Y(Y_FOLD)))
s.append('</g>')

# 拼幅缝：中缝（通高）＋ 内外缝（只在外侧块那一段）
s.append('<g id="SEAM" stroke="%s" stroke-width="2.2" fill="none" stroke-dasharray="26 10">' % BLUE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(0), Y(0), X(0), Y(CLOTH_H)))
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
        X(sx * X_SPLIT), Y(Y_OUT_LO), X(sx * X_SPLIT), Y(Y_OUT_HI)))
s.append('</g>')

# 内侧块的布边：外侧块没盖到的那两段
s.append('<g id="FREEEDGE" stroke="%s" stroke-width="1.6" fill="none">' % GRAY)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * X_SPLIT), Y(0), X(sx * X_SPLIT), Y(Y_OUT_LO)))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * X_SPLIT), Y(Y_OUT_HI), X(sx * X_SPLIT), Y(CLOTH_H)))
s.append('</g>')

# 前中剪开（弦）
s.append('<g id="SLIT" stroke="%s" stroke-width="3.4" fill="none">' % RED)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * SLIT_HALF), Y(L_BODY), X(0.0), Y(0)))
s.append('</g>')

# 领条内缘
s.append('<g id="LAPELFOLD" stroke="%s" stroke-width="2.4" fill="none" stroke-dasharray="18 12">' % GREEN)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
        X(sx * (SLIT_HALF + N_X * COLLAR_W)), Y(L_BODY + N_Y * COLLAR_W),
        X(sx * N_X * COLLAR_W), Y(N_Y * COLLAR_W)))
s.append('</g>')

# 尺寸
def dim_h(x1, x2, y, label, color=BLUE, size=26, dy=-18):
    out = [seg(x1, y, x2, y, color, 1.2)]
    for x in (x1, x2):
        out.append(seg(x, y - 22, x, y + 22, color, 1.2))
    out.append(txt((x1 + x2) / 2, y + dy, label, size, color, "middle"))
    return "".join(out)

def dim_v(x, y1, y2, label, color=BLUE, size=26, dx=18, anchor="start"):
    out = [seg(x, y1, x, y2, color, 1.2)]
    for y in (y1, y2):
        out.append(seg(x - 22, y, x + 22, y, color, 1.2))
    out.append(txt(x + dx, (y1 + y2) / 2, label, size, color, anchor))
    return "".join(out)

s.append('<g id="DIM">')
s.append(dim_h(-HALF_S, HALF_S, CLOTH_H + 100,
               "通袖 %d ＝ %d 幅 × %.0f（幅宽锁死，不动）" % (round(S), N_PANEL, FAB_W), BLUE, 28, 36))
s.append(dim_h(-FAB_W, FAB_W, -150, "衣身宽 %d（内侧 2 幅）" % round(2 * FAB_W), BLUE, 26, -18))
# 内侧/外侧经向不另标尺寸链：两种布的尺寸已直接写在块上（见下面两条 txt）
s.append(dim_v(-HALF_S - 120, Y_ARM, L_BODY, "袖口高 %d" % round(JS), BLUE, 26, -24, "end"))
s.append(dim_v(-HALF_S - 420, 0, L_BODY, "衣身长 %d" % round(L_BODY), BLUE, 26, -24, "end"))
s.append(dim_h(-SLIT_HALF, SLIT_HALF, L_BODY + 90, "剪口 %d" % round(NECK_W), BLUE, 24, 30))
s.append('</g>')

# 标题
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="96" font-size="52" font-weight="600">四块布 · V1B（衣身长 %d ／ 接袖长 %d）</text>'
         % (MARGIN, round(L_BODY), round(JS)))
s.append('  <text x="%.1f" y="152" font-size="30" fill="%s">幅宽 %.0f 不动 · 内侧块 ×2 经向 ＝ 2×衣身长 · 外侧块 ×2 经向 ＝ 2×接袖长 · '
         '四块共用同一条折线 · 沿中缝对称 · 通袖 %d</text>'
         % (MARGIN, GRAY, FAB_W, round(S)))
s.append('  <text x="%.1f" y="200" font-size="30" fill="%s">默认：衣身长 ＝ 厂商版衣长 770（中缝长）／ 接袖长 ＝ 厂商版袖根长 277.2（衣长 770 − 腋深 492.8，袖底落在腋点）</text>'
         % (MARGIN, GRAY))
s.append('</g>')

# 图例
ly = -260
s.append('<g font-family="sans-serif" font-size="28" fill="%s">' % BLUE)
s.append('  <text x="%.1f" y="%.1f">┄ 拼幅缝：中缝 x=0（通高）、内外缝 x=±%.0f（只在外侧块那一段）</text>'
         % (MARGIN, Y(ly), X_SPLIT))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="28" fill="%s">' % ORANGE)
s.append('  <text x="%.1f" y="%.1f">┈ 对折线（肩线）y=%d：四块共用一条，外侧块骑在两侧、两头各短 %d（短在袖口一头）</text>'
         % (MARGIN, Y(ly - 48), round(Y_FOLD), round(L_BODY - JS)))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="28" fill="%s">' % RED)
s.append('  <text x="%.1f" y="%.1f">— 前中剪开：颈侧点 (±%d, %d) → 下摆中点 (0, 0)，两道</text>'
         % (MARGIN, Y(ly - 96), round(SLIT_HALF), round(L_BODY)))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="28" fill="%s">' % GRAY)
s.append('  <text x="%.1f" y="%.1f">— 细灰：内侧块布边（外侧块没盖到的上下两段）→ 折后就是侧缝段 y 0…%d</text>'
         % (MARGIN, Y(ly - 144), round(Y_ARM)))
s.append('</g>')

# ---- 副图：成衣平铺（袖在肩上）----
FY = FLAT_OY
def F(y): return FY + (FLAT_H - y)

s.append('<g id="FLAT" stroke="%s" stroke-width="3" fill="none" stroke-linejoin="round">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-HALF_S), F(Y_ARM), X(-HALF_S), F(L_BODY), X(HALF_S), F(L_BODY), X(HALF_S), F(Y_ARM),
    X(X_SPLIT), F(Y_ARM), X(X_SPLIT), F(0), X(-X_SPLIT), F(0), X(-X_SPLIT), F(Y_ARM)))
s.append('</g>')

s.append('<g id="FSEAM" stroke="%s" stroke-width="1.8" fill="none">' % BLACK)
for xx in (-X_SPLIT, X_SPLIT):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(xx), F(0), X(xx), F(L_BODY)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-dasharray="24 14"/>' % (X(0.0), F(0), X(0.0), F(L_BODY)))
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="3"/>' % (
        X(sx * SLIT_HALF), F(L_BODY), X(0.0), F(0)))
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8"/>' % (
        X(sx * (SLIT_HALF + N_X * COLLAR_W)), F(L_BODY) - N_Y * COLLAR_W,
        X(sx * N_X * COLLAR_W), F(0) + N_Y * COLLAR_W))
s.append('</g>')

s.append('<g id="FCOLLAR" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-SLIT_HALF), F(L_BODY), X(-NTH), F(L_BODY) - NECK_H,
    X(NTH), F(L_BODY) - NECK_H, X(SLIT_HALF), F(L_BODY)))
s.append('</g>')

s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600">③ 成衣平铺：身长 %d、袖口高 %d，袖在肩上</text>'
         % (MARGIN, FY - 120, round(L_BODY), round(JS)))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">平铺 %d（通袖）× 高 %d（衣长）｜ 袖 %d 长 × 袖口 %d 高 ｜ 侧缝 y 0…%d，接袖缝 y %d…%d</text>'
         % (MARGIN, FY - 68, GRAY, round(S), round(L_BODY), round(X_SPLIT), round(JS),
            round(Y_ARM), round(Y_ARM), round(L_BODY)))
s.append('</g>')

# ---- 领条 / 外侧布 / 内侧布 裁片 ----
cp = [p for p in placed if p["name"] == "领条"][0]
op = [p for p in placed if p["name"] == "外侧布"][0]
s.append('<g id="CUT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    cp["_ox"], cp["_oy"], cp["_ox"] + COLLAR_L, cp["_oy"],
    cp["_ox"] + COLLAR_L, cp["_oy"] + COLLAR_W, cp["_ox"], cp["_oy"] + COLLAR_W))
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    op["_ox"], op["_oy"], op["_ox"] + FAB_W, op["_oy"],
    op["_ox"] + FAB_W, op["_oy"] + OUT_H, op["_ox"], op["_oy"] + OUT_H))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="34" font-weight="600" fill="%s">'
         '④ 领条 ×1 ｜ %d × %d ｜ 跟着衣身长变（衣长变 → 弦长变 → 领条长变）</text>'
         % (MARGIN, cp["_oy"] - 34, BLACK, round(COLLAR_L), round(COLLAR_W)))
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="32" font-weight="600" fill="%s">'
         '⑤ 外侧布 ×2 ｜ %d × %d（对折后 袖口高 %d）</text>'
         % (op["_ox"], cp["_oy"] + OUT_H + 60, BLACK, round(FAB_W), round(OUT_H), round(JS)))
# 主图里的两种布直接标在图形上
s.append(txt(-FAB_W + 40, CLOTH_H - 70, "内侧布 ×2 ｜ 幅宽 %d × 经向 %d（对折后 衣身长 %d）"
             % (round(FAB_W), round(CLOTH_H), round(L_BODY)), 28, BLACK))
s.append(txt(-HALF_S + 30, Y_OUT_HI + 55, "外侧布 ×2 ｜ 经向 %d（对折后 袖口高 %d）"
             % (round(OUT_H), round(JS)), 26, BLACK))

# 100mm 标尺
bx0, by0 = MARGIN, TOTAL_H - 110
s.append('<g id="SCALE" stroke="%s" stroke-width="2.4" fill="none">' % BLACK)
for k in range(11):
    hh = 30 if k % 5 == 0 else 16
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0, by0, bx0 + 1000, by0))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="%s">100mm 校验标尺（打印后实测，误差应 ≤0.5mm）</text>'
         % (bx0, by0 + 46, BLACK))
s.append('</svg>')

HERE = os.path.dirname(os.path.abspath(__file__))
fp = os.environ.get("HANFU_OUT") or os.path.join(HERE, "原始直领交襟衣_V1B.svg")
open(fp, "w", encoding="utf-8").write("\n".join(s))

_side = fp.rsplit(".", 1)[0] + ".pieces.json"
json.dump({
    "params": P,
    "resolved": {"S": S, "HALF_S": HALF_S, "X_SPLIT": X_SPLIT, "CLOTH_H": CLOTH_H,
                 "OUT_H": OUT_H, "L_BODY": L_BODY, "JS": JS, "Y_FOLD": Y_FOLD,
                 "Y_OUT_LO": Y_OUT_LO, "Y_OUT_HI": Y_OUT_HI, "Y_ARM": Y_ARM,
                 "SLIT_HALF": SLIT_HALF, "FAB_W": FAB_W,
                 "COLLAR_L": COLLAR_L, "COLLAR_W": COLLAR_W},
    "canvas": [CANVAS_W, TOTAL_H],
    "pieces": [{"name": p["name"], "qty": p["qty"], "ox": p["_ox"], "oy": p["_oy"],
                "box": list(p["_box"]), "cmds": p["cmds"], "grain": list(p["grain"]),
                "notches": [list(n) for n in p["notches"]]} for p in placed],
}, open(_side, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(json.dumps({"file": fp, "S": S, "衣身长": L_BODY, "接袖长": JS,
                  "内侧经向": CLOTH_H, "外侧经向": OUT_H,
                  "侧缝段": [0, Y_ARM], "袖段": [Y_ARM, L_BODY],
                  "领条": [round(COLLAR_L, 2), COLLAR_W]}, ensure_ascii=False))
