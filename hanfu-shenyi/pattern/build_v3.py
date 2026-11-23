# -*- coding: utf-8 -*-
"""
窄袖深衣 V3 · 裁片与制作 ①材料 ②对折 ③平铺（**V3 独立程序**，2026-11-18 与 V2 分开）
────────────────────────────────────────────────────────────────
依据：深衣三步图 / 剪裁与平铺图（hanfu-studio/kit/sources/02-深衣_古制/）
      孙韬《拒绝碰瓷，一篇文章说清楚西周矩领》"窄袖深衣的腰线，实为高腰甚至齐胸位置"
  · 材料 = 4 幅 × 2 段（上衣段 = 2×衣长，裳段 = 裳高）——两段同宽，无台阶
  · 上衣段水平对折 → 上衣前后；**衣长 = 袖肥 = 袖口**（同一个数！）
  · 裳段 = 一条 4 幅 × 裳高 的带子，**左右折**：两侧（±1 幅）折、中缝缝合（用户 2026-11-18）
  · 前中直接剪开两道（间距 160，不折）；领条＝**与襟缘平行的等宽带**（宽＝领宽 30），
    颈口转折为「前片两三角 ＋ 后片梯形」（底 160 → 顶 160−2×30＝100，高 30）；
    立起高 ≡ 带宽；中间露出后片 160−2×30＝100 —— 与 `hanfu-zhidui` 的领条算法完全一致（2026-11-18）
  · 腰线（衣身接缝）= 上衣段下边 = 裳段上边

★ V3 的两个旋钮（仍可调，但版型已是 V3 自己的一套）：
  L_BODY    衣长（＝袖肥＝袖口）默认 195（窄袖，腰线抬到齐胸）
  GARMENT_L 成衣总长（肩线→摆）默认 770（厂商实测男 M）
  裳高 = GARMENT_L − L_BODY，布片高 = 上衣段 + 裳段。
  V2（宽袖礼服）不在此文件里 —— 见 `build_shenyi.py`。

像素反测（1 幅 = 87.75 px 剪裁图 / 84 px 平铺 → 5.698 / 5.952 mm/px）
  段高 218.5 px → 1248 ｜ 衣长 109 px → 624 ｜ 裳高 215 px → 1248
  剪开间距 27 px → 160 ｜ 腰宽 125 px → 744 ｜ 摆宽 181 px → 1077
  腋点 ±68 px → ±388 ≈ ±372（= 腰宽/2）
坐标系：x 右为正、y 上为正，原点 = 布片下边中点
"""
import os, json
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collar

_DEF = dict(
    FAB_W=500.0,        # 单幅宽
    N_PANEL=4,          # 拼幅数（= 通袖 4 匹）
    L_BODY=195.0,       # ★衣长（＝袖肥＝袖口，三者同值）：窄袖 195；V2 宽袖版填 624
    GARMENT_L=770.0,    # ★成衣总长（肩线到摆）：便服外套 770（厂商实测男 M 衣长）；礼服去掉这行用 1872
    NECK_W=160.0,       # ★领口宽（旋钮）＝前中开口宽（两剪开线间距）
    COLLAR_W=30.0,      # ★领宽（3cm）= 领条宽 = 立起高（与 hanfu-zhidui 同一口径）
    # 派生：NECK_H ≡ COLLAR_W；后领带顶半宽 = SLIT_HALF − COLLAR_W；压边可见 = COLLAR_W
    ARMPIT=370.0,       # 躯干衣身边缘到中线的距离（钩形记号竖段；高分辨率图量得 ±368；**与裳无关**）
    ARMPIT_H=200.0,     # V2 时腋点距腰线高度（剪裁图量 195，平铺量 205）；V3 按 L_BODY 比例缩
    HOOK_OUT=60.0,      # 钩形记号：竖线在腰线上再向外弯出的水平量（量得 56~88）
    HOOK_H=70.0,        # V2 时弯折段高度（量得 68）；V3 按 L_BODY 比例缩
    N_SHANG=4,          # 裳幅数（左右折：4 幅＝一条带，与上衣同宽）
    HEM_HALF=540.0,     # 摆半宽（裳正面轮廓，≈ 半周长 2000/2 再收）
)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

FAB_W = P["FAB_W"]; N_PANEL = int(P["N_PANEL"])
N_SHANG = int(P.get("N_SHANG", 4))      # 裳幅数：4 幅一条带（2026-11-18 左右折）
NECK_W = P["NECK_W"]
SLIT_HALF = NECK_W / 2.0            # 前中开口半宽
COLLAR_W = P["COLLAR_W"]                       # 30 领宽
LAPEL_FOLD = COLLAR_W                          # 压边可见 = 整条带宽（不再单列）
NECK_H = COLLAR_W                              # 立起高 ≡ 带宽

ARMPIT = P["ARMPIT"]
HEM_HALF_ASK = P["HEM_HALF"]        # 标准衣长下的摆半宽（只用来定斜率，不再直接当输出）
HOOK_OUT = P["HOOK_OUT"]
L_BODY = P["L_BODY"]                    # 衣长 = 袖肥 = 袖口

# 腋下记号的竖向尺寸随衣长等比缩（原图是 624 衣长下量的）
_K = L_BODY / 624.0
ARMPIT_H = P["ARMPIT_H"] * _K
HOOK_H = P["HOOK_H"] * _K

HALF_S = FAB_W * N_PANEL / 2.0          # 1000（中段＝上衣，4 幅）
HALF_SH = FAB_W * N_SHANG / 2.0         # 1000（裳段 4 幅，与上衣同宽）
S = HALF_S * 2                          # 通袖 2000
SEG_MID = 2.0 * L_BODY                  # 上衣段（水平对折成前后）
SHANG_H = P["GARMENT_L"] - L_BODY       # 裳高 = 成衣总长 − 衣长
# ★平行 x 轴截取裳（2026-11-18 用户定）：裳侧边斜率固定，改衣长＝沿平行 x 轴截线截取，
#   摆宽按同一斜率派生 → 斜率不随衣长变。标准（L_BODY=195, GARMENT_L=770）下摆宽夹到
#   FAB_W=500、斜率 130/575≈0.226087，与旧图一致。
_HEM_SLOPE = (min(_DEF["HEM_HALF"], _DEF["FAB_W"]) - ARMPIT) / (_DEF["GARMENT_L"] - _DEF["L_BODY"])
# 截线受「摆半宽 ≤ 布幅」约束：衣长再长也不能让摆超出 1 幅；到顶就截在物理上限处
_MAX_SHANG_H = (FAB_W - ARMPIT) / _HEM_SLOPE
HEM_CLIP = SHANG_H > _MAX_SHANG_H
if HEM_CLIP:
    SHANG_H = _MAX_SHANG_H
HEM_HALF = ARMPIT + _HEM_SLOPE * SHANG_H
CLOTH_H = SEG_MID + SHANG_H             # 布片高 = 上衣段 + 裳段（两段，同宽 4 幅，无台阶）
Y_WAIST = SHANG_H                       # 裳上边 = 腰线（衣裳接缝）
Y_FOLD = SHANG_H + L_BODY               # 上衣段正中 = 对折线 = 肩线

# 领条（古制统一算法，见 pattern/collar.py）：开领＝颈侧点→下摆中点的弦，领条＝平行襟缘等宽带
_CG = collar.geom(SLIT_HALF, Y_FOLD, COLLAR_W)
EDGE_LEN, N_X, N_Y = _CG["edge"], _CG["nx"], _CG["ny"]
NTH, COLLAR_L, NECK_H = _CG["top_half"], _CG["length"], _CG["stand"]
Y_SEG1 = Y_WAIST                        # （兼容旧名）腰线
Y_SEG2 = CLOTH_H                        # （兼容旧名）布片顶边
HALF_WAIST = ARMPIT                     # 裳腰半宽（平铺正面轮廓）

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

NAME = "V3 窄袖" if abs(L_BODY - 195) < 1 else "V3 窄袖（衣长 %d）" % round(L_BODY)

s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (CANVAS_W, TOTAL_H, CANVAS_W, TOTAL_H))
s.append('<title>深衣 · 裁片与制作（%s）</title>' % NAME)
s.append('<rect width="100%" height="100%" fill="#ffffff"/>')

def X(x): return MAIN_OX + x
def Y(y): return MAIN_OY + (CLOTH_H - y)          # 主图：y 上为正
def FX(x): return MAIN_OX + x                     # 平铺：x 同主图
def FY(d): return FTOP + d                        # 平铺：d = 距顶边向下的深度

# ── 标题 ───────────────────────────────────────────────────────────
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600">深衣 · ① 材料与 ② 制作（%s · 衣长＝袖口 %d · 总长 %d）</text>' % (MARGIN, 100, NAME, round(L_BODY), round(L_BODY + SHANG_H)))
s.append('  <text x="%.1f" y="%.1f" font-size="32" fill="%s">上衣段 %d 幅·水平对折＝上衣（衣长 %d ＝ 袖口宽）｜裳段 %d 幅·左右折＝下裳（裳高 %d，两侧折、中缝缝合）· 前中剪开 %d · 上领条</text>'
         % (MARGIN, 158, GRAY, N_PANEL, round(L_BODY), N_SHANG, round(SHANG_H), round(SLIT_HALF * 2)))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">通袖 %d ＝ %d 幅 × %.0f ｜ 总料长 %d ＝ 上衣段 %d（2×衣长）+ 裳段 %d ｜ 腰线（衣身接缝）＝ 两段交界 = 齐胸高腰 ｜ 腋点 ±%d</text>'
         % (MARGIN, 210, GRAY, round(S), N_PANEL, FAB_W, round(CLOTH_H),
            round(SEG_MID), round(SHANG_H), round(ARMPIT)))
s.append('</g>')

# ── ① 布片外框 ────────────────────────────────────────────────────
s.append('<g id="CLOTH" stroke="%s" stroke-width="3" fill="none">' % BLACK)
# 外框：整块 4 幅（裳段与上衣段同宽，不再是两段窄裳 → 没有台阶）
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-HALF_S), Y(0), X(HALF_S), Y(0), X(HALF_S), Y(CLOTH_H), X(-HALF_S), Y(CLOTH_H)))
s.append('</g>')

# ── 拼幅缝（中段 N_PANEL 匹；上/下段各 N_SHANG 匹）─────────────────────────────────────────────────
s.append('<g id="SEAM" stroke="%s" stroke-width="2" fill="none" stroke-dasharray="26 10">' % BLUE)
for k in range(1, N_PANEL):                      # 4 幅通缝（含 x=0 的背中/前中）
    xx = -HALF_S + FAB_W * k
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(xx), Y(CLOTH_H), X(xx), Y(0)))
s.append('</g>')

# ── 段的分界（折后即腰线）─────────────────────────────────────────
s.append('<g id="SEGBD" stroke="%s" stroke-width="1.8" fill="none" stroke-dasharray="34 12" opacity="0.45">' % PURPLE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 30), Y(Y_WAIST), X(HALF_S + 30), Y(Y_WAIST)))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="28" fill="%s" text-anchor="end">' % PURPLE)
s.append('  <text x="%.1f" y="%.1f">上衣段（水平对折＝前后；折线＝肩线）</text>' % (X(-HALF_S - 45), Y(Y_FOLD + 150)))
s.append('  <text x="%.1f" y="%.1f">裳段（左右折：两侧折、中缝缝合）</text>' % (X(-HALF_S - 45), Y(Y_WAIST - 140)))
s.append('</g>')

# ── 对折线（中段正中 = 肩线）──────────────────────────────────────
s.append('<g id="FOLD" stroke="%s" stroke-width="3" fill="none" stroke-dasharray="46 16 10 16">' % ORANGE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 55), Y(Y_FOLD), X(HALF_S + 55), Y(Y_FOLD)))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="28" fill="%s" text-anchor="end">对折线（中段正中）→ 折后即肩线，衣长 %d</text>'
         % (X(-HALF_S - 45), Y(Y_FOLD) + 34, ORANGE, round(L_BODY)))

# ── 折叠箭头（上衣段水平对折；裳段左右折）─────────────────────────
def fold_arrow(xx, sx, y_from, y_to):
    """竖直弯箭头：自 y_from 折向 y_to，向 sx 侧弓出"""
    ym = (Y(y_from) + Y(y_to)) / 2.0
    s.append('<path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" stroke="%s" stroke-width="6" '
             'fill="none" marker-end="url(#arr)" opacity="0.5"/>'
             % (X(xx), Y(y_from), X(xx + sx * 85), ym, X(xx + sx * 85), ym, X(xx), Y(y_to), GRAY))
def fold_arrow_h(yy, sx, x_from, x_to):
    """水平弯箭头：自 x_from 折向 x_to，向 sx 侧（上/下）弓出"""
    xm = (X(x_from) + X(x_to)) / 2.0
    s.append('<path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" stroke="%s" stroke-width="6" '
             'fill="none" marker-end="url(#arr)" opacity="0.5"/>'
             % (X(x_from), Y(yy), xm, Y(yy + sx * 95), xm, Y(yy + sx * 95), X(x_to), Y(yy), GRAY))
s.append('<g id="FOLDARROW">')
# 上衣段：上半段水平向下对折到 Y_FOLD（折线＝肩线）
fold_arrow(-HALF_S - 130, -1, CLOTH_H - 30, Y_FOLD + 40)
fold_arrow(HALF_S + 130, 1, CLOTH_H - 30, Y_FOLD + 40)
# 裳段：左右折 —— 两侧各 1 幅向中缝折过去（折线在 ±FAB_W，与幅缝同位）
fold_arrow_h(Y_WAIST * 0.52, -1, FAB_W * 2 - 40, FAB_W + 90)
fold_arrow_h(Y_WAIST * 0.52, -1, -FAB_W * 2 + 40, -FAB_W - 90)
s.append('</g>')

# ── 裳段：折线（两侧＝±FAB_W，与幅缝同位）＋ 中缝（缝合）标注 ─────────────
s.append('<g id="SHANGFOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="26 12">' % PURPLE)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
        X(sx * FAB_W - 70), Y(Y_WAIST * 0.30), X(sx * FAB_W + 70), Y(Y_WAIST * 0.30)))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="26" fill="%s">' % PURPLE)
for sx in (-1, 1):
    s.append('  <text x="%.1f" y="%.1f" text-anchor="middle">折（两侧）</text>'
             % (X(sx * FAB_W), Y(Y_WAIST * 0.30) - 22))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="26" fill="%s">' % BLUE)
s.append('  <text x="%.1f" y="%.1f" text-anchor="end">布边 → 与另一端相接＝后中缝（缝合）</text>'
         % (X(-HALF_S - 12), Y(0) + 46))
s.append('  <text x="%.1f" y="%.1f">布边 → 与另一端相接＝后中缝（缝合）</text>'
         % (X(HALF_S + 12), Y(0) + 46))
s.append('</g>')
s.append('<g font-family="sans-serif" font-size="26" fill="%s" text-anchor="middle">' % RED)
s.append('  <text x="%.1f" y="%.1f">前中：撕开成两襟（不合）</text>' % (X(0), Y(0) + 46))
s.append('</g>')

# ── 前中剪开线（两道弦：颈侧点 P → 下摆中点 Q）──────────────────
s.append('<g id="SLIT" stroke="%s" stroke-width="3.6" fill="none">' % RED)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * SLIT_HALF), Y(Y_FOLD), X(0.0), Y(0)))
s.append('</g>')
for sx in (-1, 1):
    cx, cy = X(sx * SLIT_HALF), Y(Y_FOLD)
    s.append('<g stroke="%s" stroke-width="2.4" fill="none">'
             '<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
             '<circle cx="%.1f" cy="%.1f" r="6"/><circle cx="%.1f" cy="%.1f" r="6"/></g>'
             % (RED, cx - 14, cy - 30, cx + 4, cy - 10, cx + 14, cy - 30, cx - 4, cy - 10,
                cx - 17, cy - 35, cx + 17, cy - 35))

# ── 领条内缘（＝与襟缘平行的等宽带外沿 ±COLLAR_W；压边可见＝带宽）────────────
s.append('<g id="LAPELFOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="18 12">' % GREEN)
for sx in (-1, 1):
    ox, oy = sx * SLIT_HALF + sx * N_X * COLLAR_W, Y_FOLD + N_Y * COLLAR_W   # 颈侧点内移
    qx, qy = sx * 0.0 + sx * N_X * COLLAR_W, 0.0 + N_Y * COLLAR_W            # 下摆中点内移
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(ox), Y(oy), X(qx), Y(qy)))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
        X(sx * SLIT_HALF), Y(Y_FOLD - 130), X(ox), Y(oy)))
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
s.append('  <text x="%.1f" y="%.1f" fill="%s">┄ 拼幅缝（通高 %d 匹＝通袖 %d；x=0 那条兼作背中缝/中缝）</text>' % (MARGIN, ly, BLUE, N_PANEL, round(S)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">┄ 段的分界＝腰线（衣身接缝）：上衣段在上、裳段在下</text>' % (MARGIN, ly + 44, PURPLE))
s.append('  <text x="%.1f" y="%.1f" fill="%s">┈ 对折线（上衣段正中；折后即肩线，衣长 %d）</text>' % (MARGIN, ly + 88, ORANGE, round(L_BODY)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">— 开领线（两道弦：颈侧点 ±%d → 下摆中点，贯通到摆；间距 %d 只在颈口）</text>' % (MARGIN, ly + 132, RED, round(SLIT_HALF), round(SLIT_HALF * 2)))
s.append('  <text x="%.1f" y="%.1f" fill="%s">┈ 领条内缘（平行于襟缘弦、内让 %d；颈口处露出后片 %d）</text>' % (MARGIN, ly + 176, GREEN, round(COLLAR_W), round(SLIT_HALF * 2 - COLLAR_W * 2)))
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
for sx in (-1, 1):                      # 襟缘＝弦：颈侧点 → 下摆中点
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="3"/>' % (
        FX(sx * SLIT_HALF), FY(0), FX(0.0), FY(L_BODY + SHANG_H)))
for sx in (-1, 1):                      # 领条内缘：平行于弦，向内侧让 COLLAR_W
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8"/>' % (
        FX(sx * SLIT_HALF + sx * N_X * COLLAR_W), FY(-N_Y * COLLAR_W),
        FX(sx * N_X * COLLAR_W), FY(L_BODY + SHANG_H + N_Y * COLLAR_W)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8" stroke-dasharray="26 14"/>' % (
    FX(0), FY(0), FX(0), FY(L_BODY + SHANG_H)))
s.append('</g>')

# 顶部领口：前襟带（弦 P→O ＋ 领条内缘）已由 CENTER 组画出；此处补颈口五块中的
#   「前片三角×2 ＋ 后片梯形」。★全部由弦几何派生，不用 V1 写死的等宽矩形/三角：
#     P  ＝ 颈侧点 (±SLIT_HALF, 肩线 FY(0))
#     PB ＝ 领条内缘在颈口的起点 ＝ P + 带宽·法向 (N_X, −N_Y 在 FY)
#     M  ＝ 转角点 (miter 顶半宽 NTH, 肩线上方 NECK_H)
_PBX, _PBY = SLIT_HALF + N_X * COLLAR_W, -N_Y * COLLAR_W
s.append('<g id="COLLAR" stroke="%s" stroke-width="3" fill="none">' % BLACK)
for sx in (-1, 1):                      # 前片三角：{P, PB, M}
    s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
        FX(sx * SLIT_HALF), FY(0), FX(sx * _PBX), FY(_PBY), FX(sx * NTH), FY(-NECK_H)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (  # 后片梯形：底 ±SLIT_HALF → 顶 ±NTH
    FX(-SLIT_HALF), FY(0), FX(-NTH), FY(-NECK_H), FX(NTH), FY(-NECK_H), FX(SLIT_HALF), FY(0)))
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
_CLIP_NOTE = "｜⚠裳高已截到布幅上限（衣长按可容纳范围输出）" if HEM_CLIP else ""
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600" fill="%s">③ 平铺：直领交襟 · 上衣连袖 + 下裳</text>'
         % (MARGIN, FY(L_BODY + SHANG_H) + 108, BLACK))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">袖带高 %d（＝衣长）｜裳高 %d｜腰线即衣身接缝｜前中 | 领条 %d | 后片 %d（后中缝居中）| 领条 %d | 贯通到摆｜裳本体 4 幅 × %d｜领条宽＝立起高＝%d%s</text>'
         % (MARGIN, FY(L_BODY + SHANG_H) + 158, GRAY, round(L_BODY), round(SHANG_H),
            round(COLLAR_W), round(SLIT_HALF * 2 - COLLAR_W * 2), round(COLLAR_W), round(SHANG_H),
            round(COLLAR_W), _CLIP_NOTE))
s.append('</g>')

# ── ④ 领条裁片 ────────────────────────────────────────────────────
s.append('<g id="CUT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    MARGIN, COLLAR_OY, MARGIN + COLLAR_L, COLLAR_OY,
    MARGIN + COLLAR_L, COLLAR_OY + COLLAR_W, MARGIN, COLLAR_OY + COLLAR_W))
s.append('</g>')
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="34" font-weight="600">④ 领条 ×1 ｜ %d × %d ｜ 一条直的，成型后呈倒 U：左襟 → 绕颈 → 右襟</text>'
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
if os.environ.get("HANFU_OUT"):
    fp = os.environ["HANFU_OUT"]
else:
    fp = os.path.join(HERE, "深衣_V3_窄袖.svg")
open(fp, "w", encoding="utf-8").write("\n".join(s))

json.dump({
    "params": P,
    "resolved": {"S": S, "HALF_S": HALF_S, "CLOTH_H": CLOTH_H,
                 "SEG_MID": SEG_MID, "SEG_OUT": SHANG_H, "Y_WAIST": Y_WAIST, "GARMENT_L": L_BODY + SHANG_H,
                 "Y_SEG1": Y_SEG1, "Y_FOLD": Y_FOLD, "Y_SEG2": Y_SEG2,
                 "L_BODY": L_BODY, "SHANG_H": SHANG_H, "ARMPIT": ARMPIT,
                 "ARMPIT_H": ARMPIT_H, "HOOK_H": HOOK_H, "HOOK_OUT": HOOK_OUT,
                 "HEM_HALF": HEM_HALF, "HEM_CLIP": HEM_CLIP, "COLLAR_L": COLLAR_L},
    "canvas": [CANVAS_W, TOTAL_H],
}, open(fp.rsplit(".", 1)[0] + ".pieces.json", "w", encoding="utf-8"),
   ensure_ascii=False, indent=1)

print(json.dumps({"file": fp, "canvas": [CANVAS_W, round(TOTAL_H, 1)],
                  "S": S, "CLOTH_H": CLOTH_H, "SEG_MID": SEG_MID, "SEG_OUT": round(SHANG_H, 1),
                  "L_BODY": L_BODY, "SHANG_H": round(SHANG_H, 1),
                  "ARMPIT": ARMPIT, "ARMPIT_H": round(ARMPIT_H, 1), "COLLAR_L": COLLAR_L},
                 ensure_ascii=False))
