# -*- coding: utf-8 -*-
"""
对穿交（钱氏墓/钱樟夫妇墓 鸟衔花枝纹缎夹袄）裁片图生成器
右衽 · 单层 · 净版 · 单位 mm

本文件只做三件事：**读参数 → 调 construct 出几何 → 排版出图**。
几何与数学约束都在 `pattern/construct.py`（纯函数，无 IO）；
这里不再有坐标计算，改版型请改 construct。

量纲锚点：中国丝绸博物馆修复报告实测
  衣长 825 / 摆宽 1150（放量 0.92）/ 单边 710 / 交叠 270 / 领宽 190

本版（v7.0）相对 v6 的唯一改动 = **加接袖**（其余主体不动）：
  · 衣身袖长 / 袖口 / 腋深 / 腋下圆角 全部沿用 v6 数据（"袖口袖根数据不变"）
  · 袖底缘改为**一条连续曲线**：腋点 → 接袖根(G1) → 腕口下角，接缝处零转折
  · 接袖根边 = 衣身袖口边 → 两侧垂直、直角，无圆角
  · 预开领：前片门襟内端让开 NECK/2，两片合成 100 通口

用法：
  python build.py                              # 默认参数（厂商表 男 M）出到 pattern/
  HANFU_PARAMS='{"L":860}' python build.py     # 覆写任意参数
  HANFU_OUT=/tmp/a.svg python build.py         # 指定输出
"""
import math, os, json, sys

# 随包运行时（嵌入式 python）不会把脚本目录放进 sys.path，这里显式加一次
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import construct

# ---- 尺寸参数：可由环境变量 HANFU_PARAMS(JSON) 覆盖，供 sizing.py 一键换码 ----
# 默认值 = 厂商实物表 男 M（接袖版），单独运行本文件即可出这一码
# 2026-11-09：衣身袖长砍半（265 → 132.5），砍掉的半段挪给接袖（265 → 397.5），总袖长 530 不变
_DEF = dict(L=800.0, W_HEM=798.0, EASE=1.0, X_ARM=285.0, Y_ARM=522.8,
            X_SHLD=285.0, SLEEVE_LEN=132.5, CUFF=160.0, NECK=100.0,
            OV=270.0, HEM_RISE=60.0, TILT_DEG=0.8, COL_W=70.0,
            JS=397.5, WRIST=130.0)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

# ---- 参数 → 派生量（唯一入口；verify.py 等外部脚本仍按老名字读这些模块级变量）----
_d = construct.derive(P, "wrist")

L          = P["L"]
W_HEM      = P["W_HEM"]
EASE       = _d["EASE"]
X_ARM      = P["X_ARM"]
Y_ARM      = P["Y_ARM"]
X_SHLD     = P["X_SHLD"]
SLEEVE_LEN = P["SLEEVE_LEN"]     # 衣身袖长（肩点 → 接袖根）
CUFF       = P["CUFF"]           # 衣身袖口宽 = 接袖根宽（数据不变）
NECK       = P["NECK"]           # 预开领总宽（前片各让 NECK/2）
OV         = P["OV"]
HEM_RISE   = P["HEM_RISE"]
COL_W      = P["COL_W"]
JS         = P["JS"]             # 接袖长
WRIST      = _d["WRIST"]         # 掩腕袖口宽（= 直线袖底推到腕口处的高度）

HALF       = _d["HALF"]          # 侧缝
X_CUFF     = _d["X_CUFF"]        # 接袖根（= 衣身袖口）
X_JS       = _d["X_JS"]          # 腕口
S          = _d["S"]             # 通袖
TILT       = _d["TILT"]
LAP_DX     = _d["LAP_DX"]        # 门襟边越中量
_MENJIN_ANG = _d["MENJIN_ANG"]   # 门襟斜边与竖直线的夹角（grain 由它派生）
NECK_DIP   = 0.0
P_HEM      = 760.0               # 兼容旧字段

Y_TOP      = _d["Y_TOP"]
Y_CUFF_TOP = _d["Y_CUFF_TOP"]
Y_CUFF_BOT = _d["Y_CUFF_BOT"]
Y_JS_TOP   = _d["Y_JS_TOP"]
Y_JS_BOT   = _d["Y_JS_BOT"]
Y_SEAM_BOT = _d["Y_SEAM_BOT"]
SEAM_H     = _d["SEAM_H"]        # 袖根（派生值）
UND_ANG    = _d["UND_ANG"]
UND_U      = _d["UND_U"]
U_ARM      = _d["U_ARM"]
Z_PT       = _d["Z"]
_UND_A     = (X_ARM, Y_ARM)
_UND_Z     = (X_JS, Y_JS_BOT)
_UND_ANG   = UND_ANG
R_ARM_F    = construct.R_ARM_F
X_SEAM     = X_CUFF              # 接袖缝位置（参考线）
U_SEAM     = (X_CUFF, Y_SEAM_BOT)


def sleeve_y(x):
    """袖上缘：自肩点起微下垂 0.8°"""
    return construct.sleeve_y(_d, x)


# ---- 裁片：一层薄包装，几何全在 construct ----
def back_half():
    return construct.back_half(_d)


def front_panel():
    return construct.front_panel(_d)


def sleeve_ext():
    return construct.sleeve_ext(_d)


def collar_band(width=None):
    return construct.collar_band(_d, width)


def triangle(h, w=95.0, name="三角拼接"):
    return construct.triangle(name, h, w)


def tie(length=200.0, width=20.0):
    return construct.tie(length, width)


def hem_facing(length=None, width=30.0):
    return construct.hem_facing(length or (2 * HALF), width)


PIECES = [
    back_half(),
    front_panel(),
    sleeve_ext(),
    collar_band(COL_W),
    triangle(170, name="三角拼接 A"),
    triangle(140, name="三角拼接 B"),
    tie(),
    hem_facing(),
]


# ---------- 几何工具（排版用；只跟 cmds 结构有关，跟服饰无关）----------
def flat(cmds):
    """把 cmds 展开成带控制点的点列表（y 取反，转 SVG 坐标）"""
    pts = []
    for c in cmds:
        if c[0] == "M":
            pts.append((c[1][0], -c[1][1]))
        elif c[0] == "L":
            pts.append((c[1][0], -c[1][1]))
        elif c[0] == "C":
            for p in c[1:]:
                pts.append((p[0], -p[1]))
        elif c[0] == "Q":
            for p in c[1:]:
                pts.append((p[0], -p[1]))
    return pts


def bbox(cmds):
    pts = flat(cmds)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
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
        elif c[0] == "Q":
            a, e = c[1], c[2]
            out.append("Q %.1f %.1f %.1f %.1f" % (a[0] + ox, -a[1] + oy, e[0] + ox, -e[1] + oy))
        elif c[0] == "Z":
            out.append("Z")
    return " ".join(out)


# ---------- 排版 ----------
GAP = 160.0
MARGIN = 120.0
MIN_SLOT = 340.0
MAXW = 2100.0

placed = []
cur_x = MARGIN
cur_y = MARGIN
row_h = 0.0

for p in PIECES:
    x0, y0, x1, y1 = bbox(p["cmds"])
    w, h = x1 - x0, y1 - y0
    slot = max(w, MIN_SLOT)
    if cur_x + slot > MAXW + MARGIN and cur_x > MARGIN:
        cur_x = MARGIN
        cur_y += row_h + GAP
        row_h = 0.0
    ox = cur_x - x0
    oy = cur_y - y0
    p["_ox"], p["_oy"] = ox, oy
    p["_box"] = (cur_x, cur_y, cur_x + w, cur_y + h)
    p["_slot"] = (cur_x, cur_x + slot)
    placed.append(p)
    cur_x += slot + GAP
    row_h = max(row_h, h)

BODY_H = cur_y + row_h
TITLE_H = 440.0
TOTAL_W = MAXW + MARGIN
TOTAL_H = BODY_H + MARGIN + TITLE_H

# ---------- SVG ----------
BLACK = "#1a1a1a"
RED = "#c0392b"
BLUE = "#1f5fa8"
GRAY = "#8a8a8a"

s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">' % (TOTAL_W, TOTAL_H, TOTAL_W, TOTAL_H))
s.append('<title>对穿交 · 钱氏墓 鸟衔花枝纹缎夹袄 · 裁片图（右衽·单层·净版·mm·接袖）</title>')
s.append('<rect width="100%" height="100%" fill="#ffffff"/>')
s.append('<g id="OUTLINE" stroke="%s" stroke-width="2" fill="none" stroke-linejoin="round">' % BLACK)
for p in placed:
    s.append('  <path id="%s_ot" data-qty="%d" d="%s"/>' % (p["name"], p["qty"], path_d(p["cmds"], p["_ox"], p["_oy"])))
s.append('</g>')

s.append('<g id="SEAM" stroke="%s" stroke-width="1.2" fill="none" stroke-dasharray="18 8">' % BLUE)
for p in placed:
    for seg in p["seams"]:
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (seg[0][0] + p["_ox"], -seg[0][1] + p["_oy"],
                                                             seg[1][0] + p["_ox"], -seg[1][1] + p["_oy"]))
s.append('</g>')

s.append('<g id="GRAIN" stroke="%s" stroke-width="1.4" fill="none">' % BLACK)
for p in placed:
    x0, y0, x1, y1 = p["_box"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ln = min(max(x1 - x0, 120.0), max(y1 - y0, 120.0)) * 0.6
    gx, gy = p["grain"]
    n = math.hypot(gx, gy)
    gx, gy = gx / n, gy / n
    gy = -gy
    ax, ay = cx - gx * ln / 2, cy - gy * ln / 2
    bx, by = cx + gx * ln / 2, cy + gy * ln / 2
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (ax, ay, bx, by))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>' % (
        bx - 14, by - 6, bx, by, bx, by, bx + 14, by - 6))
s.append('</g>')

s.append('<g id="NOTCH" stroke="%s" stroke-width="2.4">' % RED)
for p in placed:
    for n in p["notches"]:
        nx, ny = n[0] + p["_ox"], -n[1] + p["_oy"]
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (nx - 9, ny - 9, nx + 9, ny + 9))
s.append('</g>')

s.append('<g id="DIM" stroke="%s" stroke-width="0.9" fill="%s" font-family="sans-serif" font-size="26">' % (GRAY, GRAY))
for p in placed:
    for d in p["dims"]:
        a, b, txt = d[1], d[2], d[3]
        ax, ay = a[0] + p["_ox"], -a[1] + p["_oy"]
        bx, by = b[0] + p["_ox"], -b[1] + p["_oy"]
        if d[0] == "L":
            s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-start="url(#a)" marker-end="url(#a)"/>' % (ax, ay, bx, by))
            mx, my = (ax + bx) / 2, (ay + by) / 2
            rot = math.degrees(math.atan2(by - ay, bx - ax))
            vert = abs(rot) > 45
            if vert:
                rot += 180 if rot > 0 else 0
            tx = mx + (20 if vert else 0)
            ty2 = my + (0 if vert else 30)
            s.append('  <text x="%.1f" y="%.1f" text-anchor="middle" transform="rotate(%.1f %.1f %.1f)">%s</text>' % (tx, ty2, rot, mx, my, txt))
        else:
            s.append('  <text x="%.1f" y="%.1f" text-anchor="middle" fill="%s">%s</text>' % ((ax + bx) / 2 + 30, (ay + by) / 2, RED, txt))
s.append('</g>')

s.append('<g id="LABEL" fill="%s" font-family="sans-serif">' % BLACK)
for i, p in enumerate(placed):
    x0, y0 = p["_box"][0], p["_box"][1]
    s.append('  <text x="%.1f" y="%.1f" font-size="30" font-weight="500">%02d %s ×%d</text>' % (x0, y0 - 30, i + 1, p["name"], p["qty"]))
s.append('</g>')

# ---------- 图框 + 100mm 校验标尺 ----------
ty = BODY_H + MARGIN * 0.4
s.append('<g id="BLOCK" stroke="%s" stroke-width="1.6" fill="none">' % BLACK)
s.append('  <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (MARGIN, ty, TOTAL_W - 2 * MARGIN, TITLE_H - 80))
s.append('</g>')
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="38" font-weight="500">对穿交 · 明制 鸟衔花枝纹缎夹袄（右衽）裁片图 · 接袖版</text>' % (MARGIN + 30, ty + 60))
s.append('  <text x="%.1f" y="%.1f" font-size="26">依据：无锡七房桥钱樟夫妇墓出土实物 · 中国丝绸博物馆修复报告   ｜   单位 mm   ｜   净版（未含缝份）   ｜   单层   ｜   掩腕长窄袖·加接袖   ｜   v7.0</text>' % (MARGIN + 30, ty + 105))
s.append('  <text x="%.1f" y="%.1f" font-size="26">衣长 %d   ｜   平铺摆宽 %d（放量 %.2f）   ｜   单边摆宽 %d   ｜   交叠 %d   ｜   通袖 %d ＝ 肩点 %d ＋ 衣身袖 %d ＋ 接袖 %d（×2）</text>' % (
    MARGIN + 30, ty + 145, round(L), round(2 * HALF), EASE,
    round(HALF + LAP_DX), round(2 * LAP_DX), round(S), round(X_SHLD), round(SLEEVE_LEN), round(JS)))
s.append('  <text x="%.1f" y="%.1f" font-size="26">袖根 %d（接袖根＝衣身袖口）   ｜   腕口 %d   ｜   预开领 %d   ｜   领缘宽 %d   ｜   腋深 %d   ｜   袖底缘为一条直线（%.2f°）</text>' % (
    MARGIN + 30, ty + 185, round(SEAM_H), round(WRIST), round(NECK), round(COL_W), round(L - Y_ARM),
    math.degrees(_UND_ANG)))
s.append('</g>')
bx0 = MARGIN + 30
by0 = ty + 275
s.append('<g id="SCALE" stroke="%s" stroke-width="2" fill="none">' % BLACK)
for k in range(11):
    hh = 26 if k % 5 == 0 else 14
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0, by0, bx0 + 1000, by0))
s.append('</g>')
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="24" fill="%s">100mm 校验标尺（打印后实测，误差应 ≤0.5mm）</text>' % (bx0, by0 + 42, BLACK))

s.append('<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.2"/></marker></defs>' % GRAY)
s.append('</svg>')

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pattern")
os.makedirs(out_dir, exist_ok=True)
fp = os.environ.get("HANFU_OUT") or os.path.join(out_dir, "对穿交_右衽_裁片图.svg")
os.makedirs(os.path.dirname(fp), exist_ok=True)
open(fp, "w", encoding="utf-8").write("\n".join(s))

# ---- 供 CAD 出图使用的几何侧车（JSON） ----
_side = fp.rsplit(".", 1)[0] + ".pieces.json"
json.dump({
    "params": P,
    "resolved": {"L": L, "HALF": HALF, "X_ARM": X_ARM, "Y_ARM": Y_ARM, "X_SHLD": X_SHLD,
                 "X_CUFF": X_CUFF, "X_JS": X_JS, "SLEEVE_LEN": SLEEVE_LEN, "JS": JS,
                 "CUFF": CUFF, "WRIST": WRIST,
                 "Y_CUFF_TOP": Y_CUFF_TOP, "Y_CUFF_BOT": Y_CUFF_BOT,
                 "Y_JS_TOP": Y_JS_TOP, "Y_JS_BOT": Y_JS_BOT,
                 "Y_SEAM_BOT": Y_SEAM_BOT, "SEAM_H": SEAM_H,
                 "UND_A": list(_UND_A), "UND_Z": list(_UND_Z),
                 "UND_ANG": math.degrees(_UND_ANG), "R_ARM_F": R_ARM_F,
                 "U_ARM": list(U_ARM),
                 "NECK": NECK, "OV": OV, "LAP_DX": LAP_DX, "HEM_RISE": HEM_RISE},
    "canvas": [TOTAL_W, TOTAL_H],
    "pieces": [{"name": p["name"], "qty": p["qty"], "ox": p["_ox"], "oy": p["_oy"],
                "box": list(p["_box"]), "cmds": p["cmds"],
                "grain": list(p["grain"]),
                "notches": [list(n) for n in p["notches"]]} for p in placed],
}, open(_side, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

info = {
    "file": fp, "size": [round(TOTAL_W, 1), round(TOTAL_H, 1)],
    "params": {"L": L, "S": S, "W_HEM": W_HEM, "P_HEM": P_HEM, "OV": OV, "CUFF": CUFF,
               "NECK": NECK, "X_ARM": X_ARM, "Y_ARM": Y_ARM, "X_SEAM": X_SEAM,
               "X_CUFF": X_CUFF, "X_JS": X_JS, "JS": JS, "WRIST": WRIST,
               "LAPEL_ANGLE": round(math.degrees(math.atan2(LAP_DX - NECK / 2, L)), 2), "TILT": 5.0},
    "pieces": [{"name": p["name"], "qty": p["qty"], "w": round(p["_box"][2] - p["_box"][0], 1),
                "h": round(p["_box"][3] - p["_box"][1], 1)} for p in placed],
}
print(json.dumps(info, ensure_ascii=False, indent=1))
