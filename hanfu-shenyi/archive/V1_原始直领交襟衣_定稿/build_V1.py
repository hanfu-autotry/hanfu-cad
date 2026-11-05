# -*- coding: utf-8 -*-
"""
原始直领交襟衣（V1）· 裁片/排料图
────────────────────────────────────────────────────────────────
形制（孙韬《拒绝碰瓷，一篇文章说清楚西周矩领》过程图 ①②③）
  A = 直领对襟的剪裁 + 交襟的穿法
  ① 材料：4 匹拼幅成一块长方布 —— 横为通袖，竖为衣长 ×2
  ② 制作：**上下对折**（肩线折出，不另裁前片后片）→ **前中剪开两道、各向里折 80 当贴边** → 上领条
  ③ 成衣：领襟一体、连肩接袖 —— 平铺是一条横带 + 中央竖起的领襟带

已确认口径（2026-10-29）
  · 对折对称：折线上下各 624
  · 前中剪开线 ±80（间距 160），剪开后各自向里折 80 → 中央形成 160 宽双层贴边带
  · 领条 1700 × 95，缝在中央带子上 = 领襟一体

像素标定（sources/fig_原始直领交襟衣_三步.png）
  1 幅 = 234.8 px ＝ 500 mm（汉代整幅 2尺2寸≈506）→ 2.129 mm/px
  布片 939×587 px → 2000×1248 mm；剪口间距 75 px → 160 mm；领条 44 px → 95 mm

坐标系：服饰坐标 x 右为正、y 上为正，原点 = 布片下边中点
"""
import math, os, json

_DEF = dict(
    FAB_W=500.0,        # 单幅宽
    N_PANEL=4,          # 拼幅数
    HALF_L=624.0,       # 对折线上下各一段（对称对折）
    SLIT_HALF=80.0,     # 前中剪开线半间距（两道剪口 → 间距 160）
    LAPEL_FOLD=40.0,    # 剪开后各向里折的宽度（折后布边落在 ±40，中间露出后片 80）
    COLLAR_L=1700.0,    # 领条长
    COLLAR_W=95.0,      # 领条宽
    NECK_TOP_HALF=44.5, # 领条向上折转段顶半宽
    NECK_H=77.0,        # 领条折转露出高度
)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

FAB_W = P["FAB_W"]; N_PANEL = int(P["N_PANEL"])
HALF_L = P["HALF_L"]; SLIT_HALF = P["SLIT_HALF"]; LAPEL_FOLD = P["LAPEL_FOLD"]
COLLAR_L = P["COLLAR_L"]; COLLAR_W = P["COLLAR_W"]
NECK_TOP_HALF = P["NECK_TOP_HALF"]   # 后领梯形顶半宽
NECK_H = P["NECK_H"]                 # 后领露出高度

CLOTH_H = HALF_L * 2
Y_FOLD = HALF_L                 # 对折线 = 肩线
HALF_S = FAB_W * N_PANEL / 2.0
S = HALF_S * 2

# ── 裁片 ───────────────────────────────────────────────────────────
def body_blank():
    """衣身连袖片 ×1：4 匹横拼，整块不裁肩，上下对折成前后"""
    cmds = [("M", (-HALF_S, 0)), ("L", (HALF_S, 0)),
            ("L", (HALF_S, CLOTH_H)), ("L", (-HALF_S, CLOTH_H)), ("Z",)]
    return {
        "name": "衣身连袖片", "qty": 1, "grain": (0, 1), "cmds": cmds,
        "seams": [],
        "notches": [(-SLIT_HALF, 0), (SLIT_HALF, 0),
                    (-HALF_S, Y_FOLD), (0, Y_FOLD), (HALF_S, Y_FOLD)],
        "dims": [("L", (-HALF_S, 0), (HALF_S, 0), "通袖 %d（%d 幅 × %.0f）" % (round(S), N_PANEL, FAB_W)),
                 ("L", (HALF_S + 45, 0), (HALF_S + 45, CLOTH_H), "布片高 %d" % round(CLOTH_H)),
                 ("L", (HALF_S + 120, 0), (HALF_S + 120, Y_FOLD), "对折后衣长 %d" % round(HALF_L))],
    }


def collar():
    """领条 ×1：领襟一体，直丝，整条不断开"""
    return {
        "name": "领条", "qty": 1, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (COLLAR_L, 0)),
                 ("L", (COLLAR_L, COLLAR_W)), ("L", (0, COLLAR_W)), ("Z",)],
        "seams": [], "notches": [(COLLAR_L / 2 - 80, 0), (COLLAR_L / 2 + 80, 0)],
        "dims": [("L", (0, 0), (COLLAR_L, 0), "领条 %d × %d" % (round(COLLAR_L), round(COLLAR_W)))],
    }


PIECES = [body_blank(), collar()]

# ── 工具 ───────────────────────────────────────────────────────────
def flat(cmds):
    pts = []
    for c in cmds:
        if c[0] in ("M", "L"):
            pts.append((c[1][0], -c[1][1]))
        elif c[0] in ("C", "Q"):
            for p in c[1:]:
                pts.append((p[0], -p[1]))
    return pts

def bbox(cmds):
    pts = flat(cmds)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def path_d(cmds, ox, oy):
    out = []
    for c in cmds:
        if c[0] == "M":
            out.append("M %.1f %.1f" % (c[1][0] + ox, -c[1][1] + oy))
        elif c[0] == "L":
            out.append("L %.1f %.1f" % (c[1][0] + ox, -c[1][1] + oy))
        elif c[0] == "C":
            a, b, e = c[1], c[2], c[3]
            out.append("C %.1f %.1f %.1f %.1f %.1f %.1f" % (
                a[0] + ox, -a[1] + oy, b[0] + ox, -b[1] + oy, e[0] + ox, -e[1] + oy))
        elif c[0] == "Z":
            out.append("Z")
    return " ".join(out)

# ── 布局 ───────────────────────────────────────────────────────────
MARGIN = 150.0
CANVAS_W = 2400.0
MAIN_OX = CANVAS_W / 2.0
MAIN_OY = 330.0                       # 主图顶（画布 y）
LEG_H = 430.0                         # 图例区高
FLAT_OY = MAIN_OY + CLOTH_H + LEG_H + 190
FLAT_H = HALF_L
COLLAR_OY = FLAT_OY + FLAT_H + 520
TOTAL_H = COLLAR_OY + COLLAR_W + 260

placed = []
for p in PIECES:
    x0, y0, x1, y1 = bbox(p["cmds"])
    if p["name"] == "衣身连袖片":
        ox, oy = MAIN_OX, MAIN_OY
    else:
        ox, oy = MARGIN - x0, COLLAR_OY
    p["_ox"], p["_oy"] = ox, oy
    p["_box"] = (x0 + ox, y0 + oy, x1 + ox, y1 + oy)
    placed.append(p)

# ── SVG ────────────────────────────────────────────────────────────
BLACK, RED, BLUE, GRAY, GREEN, ORANGE = "#1a1a1a", "#b3241c", "#1a4d8f", "#6f6f6f", "#1d6b3a", "#b85400"
s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (CANVAS_W, TOTAL_H, CANVAS_W, TOTAL_H))
s.append('<title>原始直领交襟衣 · 裁片与制作（V1）</title>')
s.append('<rect width="100%" height="100%" fill="#ffffff"/>')

def X(x): return x + MAIN_OX
def Y(y): return MAIN_OY + (CLOTH_H - y)

# ---- 主图：布片 ----
s.append('<g id="CLOTH" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-HALF_S), Y(CLOTH_H), X(HALF_S), Y(CLOTH_H), X(HALF_S), Y(0), X(-HALF_S), Y(0)))
s.append('</g>')

# 拼幅缝
s.append('<g id="SEAM" stroke="%s" stroke-width="2" fill="none" stroke-dasharray="26 10">' % BLUE)
for k in range(1, N_PANEL):
    xx = -HALF_S + FAB_W * k
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(xx), Y(CLOTH_H), X(xx), Y(0)))
s.append('</g>')

# 上下对折线（肩线）
s.append('<g id="FOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="46 16 10 16">' % ORANGE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 25), Y(Y_FOLD), X(HALF_S + 25), Y(Y_FOLD)))
s.append('</g>')

# 前中剪开线（两道，红色实线 + 剪刀标记）
s.append('<g id="SLIT" stroke="%s" stroke-width="3.4" fill="none">' % RED)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * SLIT_HALF), Y(Y_FOLD), X(sx * SLIT_HALF), Y(0)))
s.append('</g>')
# 剪刀符号（剪开线顶端）
for sx in (-1, 1):
    cx, cy = X(sx * SLIT_HALF), Y(Y_FOLD)
    s.append('<g stroke="%s" stroke-width="2.4" fill="none">'
             '<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
             '<circle cx="%.1f" cy="%.1f" r="6"/><circle cx="%.1f" cy="%.1f" r="6"/></g>'
             % (RED, cx - 14, cy - 30, cx + 4, cy - 10, cx + 14, cy - 30, cx - 4, cy - 10,
                cx - 17, cy - 35, cx + 17, cy - 35))

# 折边线（剪开后各向里折 80，折后布边落在中线）
s.append('<g id="LAPELFOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="18 12">' % GREEN)
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(sx * LAPEL_FOLD), Y(Y_FOLD), X(sx * LAPEL_FOLD), Y(0)))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
        X(sx * SLIT_HALF), Y(Y_FOLD - 120), X(sx * LAPEL_FOLD), Y(Y_FOLD - 120)))
s.append('</g>')

# 布纹（每幅一个，经向竖直，双向）
s.append('<g id="GRAIN" stroke="%s" stroke-width="2.2" fill="none">' % GRAY)
for k in range(N_PANEL):
    cx = -HALF_S + FAB_W * (k + 0.5)
    if abs(cx) < SLIT_HALF + 60:
        continue
    y0, y1 = CLOTH_H * 0.26, CLOTH_H * 0.74
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-start="url(#ar)" marker-end="url(#ar)"/>'
             % (X(cx), Y(y0), X(cx), Y(y1)))
s.append('</g>')

# 标题与说明
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600">原始直领交襟衣 · ① 材料与 ② 制作（V1）</text>' % (MARGIN, 96))
s.append('  <text x="%.1f" y="%.1f" font-size="32" fill="%s">4 匹拼幅 · 整块不裁肩 · 上下对折成前后 · 前中剪开 160 · 两襟各向里折 40（中间露出后片 80）· 上领条</text>'
         % (MARGIN, 150, GRAY))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">通袖 %d ＝ %d 幅 × %.0f ｜ 布片高 %d ＝ 对折线上下各 %d ｜ 成衣衣长 %d ｜ 剪口间距 %d</text>'
         % (MARGIN, 200, GRAY, round(S), N_PANEL, FAB_W, round(CLOTH_H), round(HALF_L), round(HALF_L), round(SLIT_HALF * 2)))
s.append('</g>')

# 图例
ly = Y(0) + 130
s.append('<g font-family="sans-serif" font-size="30" fill="%s"><text x="%.1f" y="%.1f">┄ 拼幅缝（4 匹横拼）</text></g>'
         % (BLUE, MARGIN, ly))
s.append('<g font-family="sans-serif" font-size="30" fill="%s"><text x="%.1f" y="%.1f">┈ 上下对折线（肩线折出，不另裁前片后片）</text></g>'
         % (ORANGE, MARGIN, ly + 46))
s.append('<g font-family="sans-serif" font-size="30" fill="%s"><text x="%.1f" y="%.1f">— 前中剪开线（从对折线剪到下摆，两道）</text></g>'
         % (RED, MARGIN, ly + 92))
s.append('<g font-family="sans-serif" font-size="30" fill="%s"><text x="%.1f" y="%.1f">┈ 折边线（各向里折 40，布边落在 ±40，折边即领条缝位）</text></g>'
         % (GREEN, MARGIN, ly + 138))

# ---- 副图：成衣平铺 ----
s.append('<g id="FLAT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
# 底边 + 两侧
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f"/>' % (
    X(-HALF_S), FLAT_OY, X(-HALF_S), FLAT_OY + FLAT_H, X(HALF_S), FLAT_OY + FLAT_H, X(HALF_S), FLAT_OY))
# 顶边：领条经过的两处（±80→±40）断开，只留中间后片露出的一段
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S), FLAT_OY, X(-SLIT_HALF), FLAT_OY))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-LAPEL_FOLD), FLAT_OY, X(LAPEL_FOLD), FLAT_OY))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(SLIT_HALF), FLAT_OY, X(HALF_S), FLAT_OY))
for k in range(1, N_PANEL):
    xx = -HALF_S + FAB_W * k
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8"/>' % (X(xx), FLAT_OY, X(xx), FLAT_OY + FLAT_H))
s.append('</g>')

# 中央五条线（照原图 ③ 的画法：纯黑，不填色）
s.append('<g id="CENTER" stroke="%s" fill="none">' % BLACK)
# 剪开线（开口两侧 = 领条外边）
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="3"/>' % (
        X(sx * SLIT_HALF), FLAT_OY, X(sx * SLIT_HALF), FLAT_OY + FLAT_H))
# 领条内边：从下摆一直通到梯形顶边（原图 723 / 760 贯通于此）
for sx in (-1, 1):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8"/>' % (
        X(sx * LAPEL_FOLD), FLAT_OY - NECK_H, X(sx * LAPEL_FOLD), FLAT_OY + FLAT_H))
# 后中缝：只在横带内，不进领口
s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8" stroke-dasharray="26 14"/>' % (
    X(0), FLAT_OY, X(0), FLAT_OY + FLAT_H))
s.append('</g>')

# 顶部：领条在领口向上折转的那一段（实心，内部不再画线）
s.append('<g id="COLLAR" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    X(-SLIT_HALF), FLAT_OY, X(-NECK_TOP_HALF), FLAT_OY - NECK_H,
    X(NECK_TOP_HALF), FLAT_OY - NECK_H, X(SLIT_HALF), FLAT_OY))
s.append('</g>')

s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="52" font-weight="600">③ 成衣平铺：领襟一体，连肩接袖</text>' % (MARGIN, FLAT_OY + FLAT_H + 105))
s.append('  <text x="%.1f" y="%.1f" font-size="30" fill="%s">平铺高 %d ｜ 通袖 %d ｜ 前中：| 领条 40 | 露出后片 80（后中缝居中）| 领条 40 | ｜ 顶部 = 领条在领口向上折转（底 %d → 顶 %.0f，露出 %.0f）</text>'
         % (MARGIN, FLAT_OY + FLAT_H + 155, GRAY, round(FLAT_H), round(S), round(SLIT_HALF * 2), round(NECK_TOP_HALF * 2), round(NECK_H)))
s.append('</g>')

# ---- 领条裁片 ----
cp = [p for p in placed if p["name"] == "领条"][0]
s.append('<g id="CUT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="%s"/>' % path_d(cp["cmds"], cp["_ox"], cp["_oy"]))
s.append('</g>')
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="34" font-weight="600">④ 领条 ×1 ｜ %d × %d ｜ 一条直的，成型后呈倒 U：左襟 → 绕颈 → 右襟</text>'
         % (MARGIN, cp["_box"][1] - 30, round(COLLAR_L), round(COLLAR_W)))
s.append('</g>')

# 100mm 标尺
bx0, by0 = MARGIN, TOTAL_H - 100
s.append('<g id="SCALE" stroke="%s" stroke-width="2.4" fill="none">' % BLACK)
for k in range(11):
    hh = 30 if k % 5 == 0 else 16
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0, by0, bx0 + 1000, by0))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="26" fill="%s">100mm 校验标尺（打印后实测，误差应 ≤0.5mm）</text>'
         % (bx0, by0 + 46, BLACK))
s.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.4"/></marker></defs>' % GRAY)
s.append('</svg>')

HERE = os.path.dirname(os.path.abspath(__file__))
fp = os.environ.get("HANFU_OUT") or os.path.join(HERE, "原始直领交襟衣_V1.svg")
open(fp, "w", encoding="utf-8").write("\n".join(s))

_side = fp.rsplit(".", 1)[0] + ".pieces.json"
json.dump({
    "params": P,
    "resolved": {"S": S, "HALF_S": HALF_S, "CLOTH_H": CLOTH_H, "HALF_L": HALF_L,
                 "Y_FOLD": Y_FOLD, "FAB_W": FAB_W, "SLIT_HALF": SLIT_HALF,
                 "LAPEL_FOLD": LAPEL_FOLD, "COLLAR_L": COLLAR_L, "COLLAR_W": COLLAR_W},
    "canvas": [CANVAS_W, TOTAL_H],
    "pieces": [{"name": p["name"], "qty": p["qty"], "ox": p["_ox"], "oy": p["_oy"],
                "box": list(p["_box"]), "cmds": p["cmds"], "grain": list(p["grain"]),
                "notches": [list(n) for n in p["notches"]]} for p in placed],
}, open(_side, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(json.dumps({"file": fp, "canvas": [CANVAS_W, round(TOTAL_H, 1)],
                  "S": S, "CLOTH_H": CLOTH_H, "HALF_L": HALF_L,
                  "SLIT": [SLIT_HALF, LAPEL_FOLD]}, ensure_ascii=False))
