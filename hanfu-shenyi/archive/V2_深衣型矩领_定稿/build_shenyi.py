# -*- coding: utf-8 -*-
"""
深衣型矩领（V2）· 裁片与制作 ①材料 ②对折 ③平铺
────────────────────────────────────────────────────────────────
依据：sources/fig_深衣型矩领_三步.png（用户提供，1440×810）
  · 材料 = 4 幅 × 3 段，段段等分
  · 中段对折（折线在中段正中）→ 上衣前后 = 衣长 624
  · 上段、下段折过来 → 下裳（各 4 幅 × 1248）
  · 前中剪开两道（间距 160），两襟各向里折 40，中间露出后片 80，上领条
  · 腰线（衣身接缝）= 中段的上下边 = 齐胸高腰
  · 腰线上 ±372 处为**腋点**：向外是袖底缝（前片与后片缝合，侧面由倒U闭成0），
    向内是裳的接缝。袖底缝两端顶点共点于腋点。

像素反测（1 幅 = 87.75 px 剪裁图 / 84 px 平铺 → 5.698 / 5.952 mm/px）
  段高 218.5 px → 1248 ｜ 衣长 109 px → 624 ｜ 裳高 215 px → 1248
  剪开间距 27 px → 160 ｜ 腰宽 125 px → 744 ｜ 摆宽 181 px → 1077
  腋点 ±68 px → ±388 ≈ ±372（= 腰宽/2）
坐标系：x 右为正、y 上为正，原点 = 布片下边中点
"""
import os, json

_DEF = dict(
    FAB_W=500.0,        # 单幅宽
    N_PANEL=4,          # 拼幅数（= 通袖 4 匹）
    SEG_H=1248.0,       # 每段高（对折后 = 衣长 624）
    N_SEG=3,            # 段数：中段＝上衣，上下两段＝裳
    SLIT_HALF=80.0,     # 前中剪开线半间距（→ 间距 160）
    LAPEL_FOLD=40.0,    # 各向里折 40（折后布边在 ±40，中间露出后片 80）
    COLLAR_W=95.0,      # 领条宽
    NECK_TOP_HALF=44.5, # 领条向上折转段顶半宽
    NECK_H=77.0,        # 领条折转露出高度
    ARMPIT=370.0,       # 躯干衣身边缘到中线的距离（钩形记号竖段；高分辨率图量得 ±368；**与裳无关**）
    ARMPIT_H=200.0,     # 竖缝长 = 腋点距腰线高度（剪裁图量 195，平铺量 205）
    HOOK_OUT=60.0,      # 钩形记号：竖线在腰线上再向外弯出的水平量（量得 56~88）
    HOOK_H=70.0,        # 钩形记号：弯折段的高度（量得 68）
    HEM_HALF=540.0,     # 摆半宽（裳正面轮廓，≈ 半周长 2000/2 再收）
)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

FAB_W = P["FAB_W"]; N_PANEL = int(P["N_PANEL"])
SEG_H = P["SEG_H"]; N_SEG = int(P["N_SEG"])
SLIT_HALF = P["SLIT_HALF"]; LAPEL_FOLD = P["LAPEL_FOLD"]
COLLAR_W = P["COLLAR_W"]; NECK_TOP_HALF = P["NECK_TOP_HALF"]; NECK_H = P["NECK_H"]
ARMPIT = P["ARMPIT"]; ARMPIT_H = P["ARMPIT_H"]; HEM_HALF = P["HEM_HALF"]
HOOK_OUT = P["HOOK_OUT"]; HOOK_H = P["HOOK_H"]

HALF_S = FAB_W * N_PANEL / 2.0          # 1000
S = HALF_S * 2                          # 通袖 2000
CLOTH_H = SEG_H * N_SEG                 # 布片高 3744
Y_SEG1 = SEG_H                          # 中段下边 = 腰线（一层）
Y_FOLD = SEG_H * 1.5                    # 中段正中 = 对折线 = 肩线
Y_SEG2 = SEG_H * 2                      # 中段上边 = 腰线（另一层）
L_BODY = SEG_H / 2.0                    # 衣长 624
SHANG_H = SEG_H                         # 裳高 1248
HALF_WAIST = ARMPIT                     # 裳腰半宽（平铺正面轮廓）
COLLAR_L = 2 * (L_BODY + SHANG_H) + SLIT_HALF * 2   # 一条直的，绕两襟到摆

# ── 布局 ───────────────────────────────────────────────────────────
CANVAS_W = 3100.0
MARGIN = 150.0
MAIN_OX = CANVAS_W / 2.0
MAIN_OY = 360.0
CLOTH_BOT = MAIN_OY + CLOTH_H
LEG_H = 460.0
FTOP = CLOTH_BOT + 150 + LEG_H + 150     # 平铺顶边（画布 y）
FLAT_H = L_BODY + SHANG_H                # 1872
COLLAR_OY = FTOP + FLAT_H + 300
TOTAL_H = COLLAR_OY + COLLAR_W + 300

BLACK, RED, BLUE, GRAY, GREEN, ORANGE, PURPLE = (
    "#1a1a1a", "#b3241c", "#1a4d8f", "#6f6f6f", "#1d6b3a", "#b85400", "#6a2c91")

s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (CANVAS_W, TOTAL_H, CANVAS_W, TOTAL_H))
s.append('<title>深衣型矩领 · 裁片与制作（V2）</title>')
s.append('<rect width="100%" height="100%" fill="#ffffff"/>')

def X(x): return MAIN_OX + x
def Y(y): return MAIN_OY + (CLOTH_H - y)          # 主图：y 上为正
def FX(x): return MAIN_OX + x                     # 平铺：x 同主图
def FY(d): return FTOP + d                        # 平铺：d = 距顶边向下的深度

# ── 标题 ───────────────────────────────────────────────────────────
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600">深衣型矩领 · ① 材料与 ② 制作（V2）</text>' % (MARGIN, 100))
s.append('  <text x="%.1f" y="%.1f" font-size="32" fill="%s">4 匹拼幅 × 3 段 · 中段对折＝上衣（衣长 %d）· 上下两段折过来＝下裳（各 %d 高）· 前中剪开 %d、两襟各折 %d · 上领条</text>'
         % (MARGIN, 158, GRAY, round(L_BODY), round(SHANG_H), round(SLIT_HALF * 2), round(LAPEL_FOLD)))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">通袖 %d ＝ %d 幅 × %.0f ｜ 布片高 %d ＝ %d 段 × %d ｜ 腰线（衣身接缝）＝ 中段上下边 = 齐胸高腰 ｜ 腋点 ±%d</text>'
         % (MARGIN, 210, GRAY, round(S), N_PANEL, FAB_W, round(CLOTH_H), N_SEG, round(SEG_H), round(ARMPIT)))
s.append('</g>')

# ── ① 布片外框 ────────────────────────────────────────────────────
s.append('<g id="CLOTH" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-HALF_S), Y(CLOTH_H), X(HALF_S), Y(CLOTH_H), X(HALF_S), Y(0), X(-HALF_S), Y(0)))
s.append('</g>')

# ── 拼幅缝（4 匹）─────────────────────────────────────────────────
s.append('<g id="SEAM" stroke="%s" stroke-width="2" fill="none" stroke-dasharray="26 10">' % BLUE)
for k in range(1, N_PANEL):
    xx = -HALF_S + FAB_W * k
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(xx), Y(CLOTH_H), X(xx), Y(0)))
s.append('</g>')

# ── 段的分界（折后即腰线）─────────────────────────────────────────
s.append('<g id="SEGBD" stroke="%s" stroke-width="1.8" fill="none" stroke-dasharray="34 12" opacity="0.45">' % PURPLE)
for yy in (Y_SEG1, Y_SEG2):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 30), Y(yy), X(HALF_S + 30), Y(yy)))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="28" fill="%s" text-anchor="end">' % PURPLE)
s.append('  <text x="%.1f" y="%.1f">上段（折下来＝裳·后）</text>' % (X(-HALF_S - 45), Y(CLOTH_H * 0.9)))
s.append('  <text x="%.1f" y="%.1f">中段（对折＝上衣前后）</text>' % (X(-HALF_S - 45), Y(Y_SEG2 - 110)))
s.append('  <text x="%.1f" y="%.1f">下段（折上去＝裳·前）</text>' % (X(-HALF_S - 45), Y(Y_SEG1 - 110)))
s.append('</g>')

# ── 对折线（中段正中 = 肩线）──────────────────────────────────────
s.append('<g id="FOLD" stroke="%s" stroke-width="3" fill="none" stroke-dasharray="46 16 10 16">' % ORANGE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 55), Y(Y_FOLD), X(HALF_S + 55), Y(Y_FOLD)))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="28" fill="%s" text-anchor="end">对折线（中段正中）→ 折后即肩线，衣长 %d</text>'
         % (X(-HALF_S - 45), Y(Y_FOLD) + 34, ORANGE, round(L_BODY)))

# ── 折叠箭头（上段向下、下段向上，都折到中段）─────────────────────
def fold_arrow(xx, sx, y_from, y_to):
    """竖直弯箭头：自 y_from 折向 y_to，向 sx 侧弓出"""
    ym = (Y(y_from) + Y(y_to)) / 2.0
    s.append('<path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" stroke="%s" stroke-width="6" '
             'fill="none" marker-end="url(#arr)" opacity="0.5"/>'
             % (X(xx), Y(y_from), X(xx + sx * 85), ym, X(xx + sx * 85), ym, X(xx), Y(y_to), GRAY))
fold_arrow(-HALF_S - 130, -1, CLOTH_H - 30, Y_SEG2 + 50)
fold_arrow(-HALF_S - 130, -1, 30, Y_SEG1 - 50)
fold_arrow(HALF_S + 130, 1, CLOTH_H - 30, Y_SEG2 + 50)
fold_arrow(HALF_S + 130, 1, 30, Y_SEG1 - 50)

# ── 前中剪开线（两道，从折线剪到腰线）────────────────────────────
s.append('<g id="SLIT" stroke="%s" stroke-width="3.6" fill="none">' % RED)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * SLIT_HALF), Y(Y_FOLD), X(sx * SLIT_HALF), Y(0)))
s.append('</g>')
for sx in (-1, 1):
    cx, cy = X(sx * SLIT_HALF), Y(Y_FOLD)
    s.append('<g stroke="%s" stroke-width="2.4" fill="none">'
             '<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
             '<circle cx="%.1f" cy="%.1f" r="6"/><circle cx="%.1f" cy="%.1f" r="6"/></g>'
             % (RED, cx - 14, cy - 30, cx + 4, cy - 10, cx + 14, cy - 30, cx - 4, cy - 10,
                cx - 17, cy - 35, cx + 17, cy - 35))

# ── 折边线（各向里折 40）──────────────────────────────────────────
s.append('<g id="LAPELFOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="18 12">' % GREEN)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * LAPEL_FOLD), Y(Y_FOLD), X(sx * LAPEL_FOLD), Y(0)))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
        X(sx * SLIT_HALF), Y(Y_FOLD - 130), X(sx * LAPEL_FOLD), Y(Y_FOLD - 130)))
s.append('</g>')

# ── 腋下：垂线（躯干衣身边缘）＋ 在腰线上向外弯出的转向（袖底缝）──────────
#   垂线：自腰线竖直向上 ARMPIT_H 到腋点。弯：自垂线下段向外弯 HOOK_OUT 落到腰线上。
#   两条线在腋点（腰线上那个转向点）共顶点 → 不加缝合＝袖到衣身全敞口（侧视倒 U），
#   加了＝侧视闭成 0。腰线上没有别的横线。
def armpit_hook(sx, y_w, d, draw):
    """y_w＝腰线的布面坐标；d=+1 腋点在该腰线上方（前片），-1 下方（后片）"""
    y0 = Y(y_w)                                   # 腰线（画布 y）
    yv = Y(y_w + d * ARMPIT_H)                    # 腋点（垂线另一端）
    yb = Y(y_w + d * HOOK_H)                      # 转向的起点
    xf, xa = X(sx * (ARMPIT + HOOK_OUT)), X(sx * ARMPIT)   # 脚 / 垂线
    # ① 垂线（实线，自腰线到腋点）
    draw.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (xa, y0, xa, yv))
    # ② 转向：自垂线下段向外弯，落到腰线上
    draw.append('  <path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f"/>' % (
        xa, yb, xa, yb + 0.45 * (y0 - yb), xa + 0.55 * (xf - xa), y0, xf, y0))
s.append('<g id="ARMPIT" stroke="%s" stroke-width="3" fill="none">' % GREEN)
for sx in (-1, 1):
    armpit_hook(sx, Y_SEG1, +1, s)
    armpit_hook(sx, Y_SEG2, -1, s)
s.append('</g>')
# 袖底缝（腰线上 ±(ARMPIT+HOOK_OUT) 以外到袖口，前后片缝合；与腋点同顶点）
s.append('<g id="SLEEVESEAM" stroke="%s" stroke-width="4" fill="none" opacity="0.8">' % GREEN)
for yy in (Y_SEG1, Y_SEG2):
    for sx in (-1, 1):
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
            X(sx * (ARMPIT + HOOK_OUT)), Y(yy), X(sx * HALF_S), Y(yy)))
s.append('</g>')

# ── 经向布纹（每幅一个，只在中段里画）────────────────────────────
s.append('<g id="GRAIN" stroke="%s" stroke-width="2.2" fill="none" opacity="0.9">' % GRAY)
def darrow(xc, y0, y1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-start="url(#arr)" marker-end="url(#arr)"/>'
             % (X(xc), Y(y0), X(xc), Y(y1)))
for k in range(N_PANEL):
    cx = -HALF_S + FAB_W * (k + 0.5)
    if abs(cx) < SLIT_HALF + 90:
        continue
    darrow(cx, Y_SEG1 + 120, Y_SEG2 - 120)
s.append('</g>')

# ── 图例 ───────────────────────────────────────────────────────────
ly = CLOTH_BOT + 150
s.append('<g font-family="sans-serif" font-size="30" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" fill="%s">┄ 拼幅缝（4 匹横拼，通袖 %d）</text>' % (MARGIN, ly, BLUE, round(S)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">┄ 段的分界（折过来即成腰线：衣身接缝 ＝ 齐胸高腰）</text>' % (MARGIN, ly + 44, PURPLE))
s.append('  <text x="%.1f" y="%.1f" fill="%s">┈ 对折线（中段正中；折后即肩线，衣长 %d）</text>' % (MARGIN, ly + 88, ORANGE, round(L_BODY)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">— 前中剪开线（两道，间距 %d；从折线剪到腰线）</text>' % (MARGIN, ly + 132, RED, round(SLIT_HALF * 2)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">┈ 折边线（两襟各向里折 %d，中间露出后片 %d）</text>' % (MARGIN, ly + 176, GREEN, round(LAPEL_FOLD), round(SLIT_HALF * 2 - LAPEL_FOLD * 2)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">— 躯干衣身边缘（竖段）：自腰线往上 %d，另一端即腋点（与裳无关）</text>' % (MARGIN, ly + 220, GREEN, round(ARMPIT_H)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">— 袖底缝（腰线 ±%d 以外到袖口，前后片缝合）：与竖段在腋点共顶点 → 不加＝敞口(侧视倒U)，加了＝闭成 0</text>' % (MARGIN, ly + 264, GREEN, round(ARMPIT + HOOK_OUT)))
s.append('</g>')

# ── ③ 平铺 ────────────────────────────────────────────────────────
s.append('<g id="FLAT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
# 袖带（衣身连袖）：左右两端 = 袖口，上边 = 肩线（折线），下边 = 腰线
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f"/>' % (
    FX(-HALF_S), FY(0), FX(-HALF_S), FY(L_BODY), FX(HALF_S), FY(L_BODY)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (FX(HALF_S), FY(L_BODY), FX(HALF_S), FY(0)))
# 肩线（折边）：领条折转段两侧断开
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (FX(-HALF_S), FY(0), FX(-SLIT_HALF), FY(0)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (FX(-LAPEL_FOLD), FY(0), FX(LAPEL_FOLD), FY(0)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (FX(SLIT_HALF), FY(0), FX(HALF_S), FY(0)))
# 拼幅缝
for k in range(1, N_PANEL):
    xx = -HALF_S + FAB_W * k
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8"/>' % (FX(xx), FY(0), FX(xx), FY(L_BODY)))
# 裳（正面轮廓）：腰 ±ARMPIT → 摆 ±HEM_HALF
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f"/>' % (
    FX(-ARMPIT), FY(L_BODY), FX(-HEM_HALF), FY(L_BODY + SHANG_H),
    FX(HEM_HALF), FY(L_BODY + SHANG_H), FX(ARMPIT), FY(L_BODY)))
s.append('</g>')

# 中心五条线（同 V1 ③ 的画法）：|领条|后片80|领条|，自领口贯通到摆
s.append('<g id="CENTER" stroke="%s" fill="none">' % BLACK)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="3"/>' % (
        FX(sx * SLIT_HALF), FY(0), FX(sx * SLIT_HALF), FY(L_BODY + SHANG_H)))
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8"/>' % (
        FX(sx * LAPEL_FOLD), FY(-NECK_H), FX(sx * LAPEL_FOLD), FY(L_BODY + SHANG_H)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8" stroke-dasharray="26 14"/>' % (
    FX(0), FY(0), FX(0), FY(L_BODY + SHANG_H)))
s.append('</g>')

# 顶部：领条在领口向上折转的那一段（梯形，同 V1）
s.append('<g id="COLLAR" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    FX(-SLIT_HALF), FY(0), FX(-NECK_TOP_HALF), FY(-NECK_H),
    FX(NECK_TOP_HALF), FY(-NECK_H), FX(SLIT_HALF), FY(0)))
s.append('</g>')

# 腋下（平铺）：垂线（躯干衣身边缘，自腰线竖直向上 ARMPIT_H）＋ 转向（自垂线下段
# 向外弯出 HOOK_OUT 落到腰线上，接袖底缝）。两条线在腋点共顶点；腰线上不再画别的横线。
s.append('<g id="ARMPIT_FLAT" stroke="%s" stroke-width="3" fill="none">' % GREEN)
for sx in (-1, 1):
    y0 = FY(L_BODY)
    yv = FY(L_BODY - ARMPIT_H)
    yb = FY(L_BODY - HOOK_H)
    xf, xa = FX(sx * (ARMPIT + HOOK_OUT)), FX(sx * ARMPIT)
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (xa, y0, xa, yv))
    s.append('  <path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f"/>' % (
        xa, yb, xa, yb + 0.45 * (y0 - yb), xa + 0.55 * (xf - xa), y0, xf, y0))
s.append('</g>')
# 注：平铺腰线上不另涂色 —— 袖底缝就是那条腰线本身（原图也只画这一条）。

# 尺寸标注
s.append('<g stroke="%s" stroke-width="2" fill="none">' % GRAY)
s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>' % (
    FX(-HALF_S), FY(0) - 120, FX(HALF_S), FY(0) - 120,
    FX(-HALF_S), FY(0) - 132, FX(-HALF_S), FY(0) - 108,
    FX(HALF_S), FY(0) - 132, FX(HALF_S), FY(0) - 108))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="28" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" text-anchor="middle">通袖 %d</text>' % (FX(0), FY(0) - 136, round(S)))
s.append('  <text x="%.1f" y="%.1f">衣长 %d</text>' % (FX(HALF_S + 40), FY(L_BODY * 0.55), round(L_BODY)))
s.append('  <text x="%.1f" y="%.1f">裳 %d</text>' % (FX(HALF_S + 40), FY(L_BODY + SHANG_H * 0.5), round(SHANG_H)))
s.append('  <text x="%.1f" y="%.1f" text-anchor="end">腰宽 %d</text>' % (FX(-HALF_S - 30), FY(L_BODY) + 10, round(ARMPIT * 2)))
s.append('  <text x="%.1f" y="%.1f" text-anchor="end">摆宽 %d</text>' % (FX(-HALF_S - 30), FY(L_BODY + SHANG_H) - 6, round(HEM_HALF * 2)))
s.append('  <text x="%.1f" y="%.1f" font-size="24" fill="%s" text-anchor="end">腋点 ±%d ｜ 垂线 %d ｜ 外弯 %d</text>' % (
    FX(-HALF_S - 40), FY(L_BODY - ARMPIT_H) + 8, GREEN, round(ARMPIT), round(ARMPIT_H), round(HOOK_OUT)))
s.append('</g>')

s.append('<g font-family="sans-serif">')
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600" fill="%s">③ 平铺：矩领对襟 · 上衣连袖 + 下裳</text>'
         % (MARGIN, FY(L_BODY + SHANG_H) + 108, BLACK))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">袖带高 %d（＝衣长）｜裳高 %d｜腰线即衣身接缝（齐胸高腰）｜前中 | 领条 %d | 后片 %d（后中缝居中）| 领条 %d | 贯通到摆｜裳为正面轮廓，本体是 4 幅 × %d</text>'
         % (MARGIN, FY(L_BODY + SHANG_H) + 158, GRAY, round(L_BODY), round(SHANG_H),
            round(LAPEL_FOLD), round(SLIT_HALF * 2 - LAPEL_FOLD * 2), round(LAPEL_FOLD), round(SHANG_H)))
s.append('</g>')

# ── ④ 领条裁片 ────────────────────────────────────────────────────
s.append('<g id="CUT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    MARGIN, COLLAR_OY, MARGIN + COLLAR_L, COLLAR_OY,
    MARGIN + COLLAR_L, COLLAR_OY + COLLAR_W, MARGIN, COLLAR_OY + COLLAR_W))
s.append('</g>')
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="34" font-weight="600">④ 领条 ×1 ｜ %d × %d ｜ 一条直的，成型后呈倒 U：左襟 → 绕颈 → 右襟（长度待核）</text>'
         % (MARGIN, COLLAR_OY - 26, round(COLLAR_L), round(COLLAR_W)))
s.append('</g>')

# ── 100mm 标尺 ────────────────────────────────────────────────────
bx0, by0 = MARGIN, TOTAL_H - 100
s.append('<g id="SCALE" stroke="%s" stroke-width="2.4" fill="none">' % BLACK)
for k in range(11):
    hh = 30 if k % 5 == 0 else 16
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0, by0, bx0 + 1000, by0))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="%s">100mm 校验标尺（打印后实测，误差应 ≤0.5mm）</text>'
         % (bx0, by0 + 46, BLACK))

s.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" '
         'orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.6"/></marker></defs>' % GRAY)
s.append('</svg>')

HERE = os.path.dirname(os.path.abspath(__file__))
fp = os.environ.get("HANFU_OUT") or os.path.join(HERE, "深衣型矩领_V2.svg")
open(fp, "w", encoding="utf-8").write("\n".join(s))

json.dump({
    "params": P,
    "resolved": {"S": S, "HALF_S": HALF_S, "CLOTH_H": CLOTH_H, "SEG_H": SEG_H,
                 "Y_SEG1": Y_SEG1, "Y_FOLD": Y_FOLD, "Y_SEG2": Y_SEG2,
                 "L_BODY": L_BODY, "SHANG_H": SHANG_H, "ARMPIT": ARMPIT,
                 "HEM_HALF": HEM_HALF, "COLLAR_L": COLLAR_L},
    "canvas": [CANVAS_W, TOTAL_H],
}, open(fp.rsplit(".", 1)[0] + ".pieces.json", "w", encoding="utf-8"),
   ensure_ascii=False, indent=1)

print(json.dumps({"file": fp, "canvas": [CANVAS_W, round(TOTAL_H, 1)],
                  "S": S, "CLOTH_H": CLOTH_H, "L_BODY": L_BODY, "SHANG_H": SHANG_H,
                  "ARMPIT": ARMPIT, "COLLAR_L": COLLAR_L}, ensure_ascii=False))
