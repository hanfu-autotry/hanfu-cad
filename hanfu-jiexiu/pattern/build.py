# -*- coding: utf-8 -*-
"""
对穿交（钱氏墓/钱樟夫妇墓 鸟衔花枝纹缎夹袄）裁片图生成器
右衽 · 单层 · 净版 · 单位 mm

量纲锚点：中国丝绸博物馆修复报告实测
  衣长 825 / 摆宽 1150（放量 0.92）/ 单边 710 / 交叠 270 / 领宽 190

本版（v7.0）相对 v6 的唯一改动 = **加接袖**（其余主体不动）：
  · 衣身袖长 / 袖口 / 腋深 / 腋下圆角 全部沿用 v6 数据（"袖口袖根数据不变"）
  · 袖底缘改为**一条连续曲线**：腋点 → 接袖根(G1) → 腕口下角，接缝处零转折
      - 衣身段：三次贝塞尔，起端切 40°、末端切矢 = 接袖直线方向（5.668°）
      - 接袖段：直线（袖口→腕口 一条平滑直线）
  · 接袖根边 = 衣身袖口边 → 两侧垂直、直角，无圆角
  · 预开领：前片门襟内端让开 NECK/2，两片合成 100 通口
"""
import math, os, json

# ---- 尺寸参数：可由环境变量 HANFU_PARAMS(JSON) 覆盖，供 sizing.py 一键换码 ----
# 默认值 = 厂商实物表 男 M（接袖版），单独运行本文件即可出这一码
_DEF = dict(L=800.0, W_HEM=798.0, EASE=1.0, X_ARM=285.0, Y_ARM=522.8,
            X_SHLD=285.0, SLEEVE_LEN=265.0, CUFF=160.0, NECK=100.0,
            OV=270.0, HEM_RISE=60.0, TILT_DEG=0.8, COL_W=70.0,
            JS=265.0, WRIST=130.0)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

L          = P["L"]
W_HEM      = P["W_HEM"]
EASE       = P["EASE"]
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
WRIST      = P["WRIST"]          # 掩腕袖口宽

HALF     = W_HEM / 2.0 * EASE    # 侧缝
X_CUFF   = X_SHLD + SLEEVE_LEN   # 接袖根（= 衣身袖口）
X_JS     = X_CUFF + JS           # 腕口
S        = 2 * X_JS              # 通袖
TILT     = math.radians(P["TILT_DEG"])
LAP_DX   = OV / 2.0              # 门襟边越中量
_MENJIN_ANG = math.atan2(LAP_DX - NECK / 2.0, L)   # 门襟斜边与竖直线的夹角（grain 由它派生）
NECK_DIP = 0.0
P_HEM    = 760.0                 # 兼容旧字段

Y_TOP = L + NECK_DIP


def sleeve_y(x):
    """袖上缘：自肩点起微下垂 0.8°"""
    return Y_TOP - (abs(x) - X_SHLD) * math.tan(TILT)


Y_CUFF_TOP = sleeve_y(X_CUFF)
Y_CUFF_BOT = Y_CUFF_TOP - CUFF
Y_JS_TOP   = sleeve_y(X_JS)
Y_JS_BOT   = Y_JS_TOP - WRIST


# ---------- 袖底缘 ----------
# 汉服直裁：腋点 → 腕口下角 **一条直线**（不是深凹弧）
# 接袖缝只是这条直线上的一道垂直切口 → 接缝处天然零转折
_UND_A = (X_ARM, Y_ARM)
_UND_Z = (X_JS, Y_JS_BOT)
_UND_ANG = math.atan2(_UND_Z[1] - _UND_A[1], _UND_Z[0] - _UND_A[0])
_UND_U = (math.cos(_UND_ANG), math.sin(_UND_ANG))
Y_SEAM_BOT = _UND_A[1] + (X_CUFF - X_ARM) * math.tan(_UND_ANG)   # 接袖根下缘
SEAM_H = Y_CUFF_TOP - Y_SEAM_BOT                                  # 袖根（派生值）
R_ARM_F = 45.0                                                    # 腋下圆角
U_ARM = (_UND_A[0] + R_ARM_F * _UND_U[0], _UND_A[1] + R_ARM_F * _UND_U[1])
Z_PT = _UND_Z


def _bez(x0, y0, x1, y1, x2, y2, x3, y3, t=0.5):
    mt = 1 - t
    x = mt**3*x0 + 3*mt*mt*t*x1 + 3*mt*t*t*x2 + t**3*x3
    y = mt**3*y0 + 3*mt*mt*t*y1 + 3*mt*t*t*y2 + t**3*y3
    return (x, y)


# ---------- 裁片定义（服饰坐标：x 向右，y 向上，原点=后中缝∩下摆中心） ----------
def _tan(seg, t0=0.0, t1=1.0, h=0.002):
    """三次贝塞尔在参数 t 处的单位切矢"""
    a = _bez(seg[0], seg[1], seg[2], seg[3], max(0.0, t0 - h))
    b = _bez(seg[0], seg[1], seg[2], seg[3], min(1.0, t1 + h))
    return _unit(a, b)


def blend(A, tA, B, tB, k=0.92):
    """G1 三次混合：两端切线分别与相邻段一致 → 无折角"""
    d = math.hypot(B[0] - A[0], B[1] - A[1]) / 3.0 * k
    c1 = (A[0] + tA[0] * d, A[1] + tA[1] * d)
    c2 = (B[0] - tB[0] * d, B[1] - tB[1] * d)
    return ("C", c1, c2, B)


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n)


def _off(p, d, r):
    return (p[0] + d[0] * r, p[1] + d[1] * r)


def _bez(p0, p1, p2, p3, t):
    mt = 1 - t
    return (mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0],
            mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1])


def split_cubic(p0, p1, p2, p3, t):
    """de Casteljau 精确分割：返回两段三次贝塞尔"""
    def lerp(a, b, u):
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    a = lerp(p0, p1, t); b = lerp(p1, p2, t); c = lerp(p2, p3, t)
    d = lerp(a, b, t); e = lerp(b, c, t)
    f = lerp(d, e, t)
    return (p0, a, d, f), (f, e, c, p3)


# 接袖缝位置（参考线）
X_SEAM = X_CUFF
U_SEAM = (X_CUFF, Y_SEAM_BOT)


def _under_cmds(sx):
    """衣身袖底：腋下圆角终点 → 接袖根，一条直线（与接袖段共线）"""
    return [("L", (sx * X_CUFF, Y_SEAM_BOT))]


def _cuff_top(sx):
    """袖口竖边（直角，无圆角）+ 袖上缘 → 肩点"""
    return [("L", (sx * X_CUFF, Y_CUFF_TOP)), ("L", (sx * X_SHLD, L))]


def back_half():
    """后片半（×2 镜像，后中缝对折）——衣身袖止于接袖根，袖底弧一条连续曲线"""
    hem = ((0, 0), (200, 5), (400, 30), (HALF, HEM_RISE))
    R = 70.0
    d_side = _unit((HALF, HEM_RISE), (X_ARM, Y_ARM))
    arm = (X_ARM, Y_ARM)
    A_a = _off(arm, d_side, -R)
    B_a = (U_ARM[0], U_ARM[1])
    tB_a = _UND_U
    cmds = [("M", (0, 0)), ("C", hem[1], hem[2], hem[3]),
            ("L", A_a), blend(A_a, d_side, B_a, tB_a)]
    cmds += _under_cmds(1.0)
    cmds += _cuff_top(1.0)
    cmds += [("L", (NECK / 2, L)), ("L", (0, L)), ("Z",)]
    return {
        "name": "后片半", "qty": 2, "grain": (0, 1), "cmds": cmds,
        "seams": [[(0, 0), (0, L)]],
        "notches": [arm, (0, 0)],
        "dims": [("L", (0, 0), (0, L), "后中长 %d" % round(L)),
                 ("L", (0, HEM_RISE), (HALF, HEM_RISE), "摆半宽 %d / 起翘 %d" % (round(HALF), round(HEM_RISE))),
                 ("L", (X_ARM, Y_ARM), (X_ARM, L), "腋深 %d" % round(L - Y_ARM)),
                 ("L", (X_CUFF + 44, Y_SEAM_BOT), (X_CUFF + 44, Y_CUFF_TOP), "袖根 %d" % round(SEAM_H)),
                 ("L", (X_SHLD, L), (X_CUFF, Y_CUFF_TOP), "衣身袖长 %d" % round(SLEEVE_LEN))],
    }


def front_panel():
    """前片（×2 镜像；右衽时穿着者左片为外襟）——门襟内端让开 NECK/2 形成预开领"""
    hem = ((LAP_DX, 0), (-200, 5), (-400, 30), (-HALF, HEM_RISE))
    R = 70.0
    d_side = _unit((-HALF, HEM_RISE), (-X_ARM, Y_ARM))
    arm = (-X_ARM, Y_ARM)
    A_a = _off(arm, d_side, -R)
    B_a = (-U_ARM[0], U_ARM[1])
    tb = _UND_U
    cmds = [("M", (NECK / 2, L)), ("L", (LAP_DX, 0)), ("C", hem[1], hem[2], hem[3]),
            ("L", A_a), blend(A_a, d_side, B_a, (-tb[0], tb[1]))]
    cmds += _under_cmds(-1.0)
    cmds += _cuff_top(-1.0)
    cmds += [("L", (NECK / 2, L)), ("Z",)]
    return {
        "name": "前片", "qty": 2,
        "grain": (math.sin(_MENJIN_ANG), -math.cos(_MENJIN_ANG)),
        "cmds": cmds,
        "seams": [],
        "notches": [arm, (NECK / 2, L)],
        "dims": [("L", (-HALF, -60), (LAP_DX, -60), "单边摆宽 %d" % round(HALF + LAP_DX)),
                 ("L", (LAP_DX, -130), (0, -130), "越中 %d" % round(LAP_DX)),
                 ("L", (NECK / 2, L), (LAP_DX, 0), "门襟斜 %.1f°" % math.degrees(
                     math.atan2(LAP_DX - NECK / 2, L))),
                 ("L", (NECK / 2, L), (0, L), "预开领半 %d" % round(NECK / 2))],
    }


def sleeve_ext():
    """接袖（×4，前后片各一）：根边=衣身袖口（垂直），袖底为袖底线的延续，腕口垂直"""
    cmds = [("M", (X_CUFF, Y_SEAM_BOT)), ("L", Z_PT),
            ("L", (X_JS, Y_JS_TOP)), ("L", (X_CUFF, Y_CUFF_TOP)), ("Z",)]
    return {
        "name": "接袖", "qty": 4, "grain": (1, 0), "cmds": cmds,
        "seams": [],
        "notches": [(X_CUFF, Y_SEAM_BOT), (X_CUFF, Y_CUFF_TOP)],
        "dims": [("L", (X_CUFF, Y_SEAM_BOT), (X_CUFF, Y_CUFF_TOP), "袖根 %d" % round(SEAM_H)),
                 ("L", (X_JS, Y_JS_BOT), (X_JS, Y_JS_TOP), "腕口 %d" % round(WRIST)),
                 ("L", (X_CUFF, Y_SEAM_BOT), (X_JS, Y_JS_BOT), "接袖长 %d" % round(JS))],
    }


def collar_band(width=None):
    """领缘条（领襟一体，直丝）：沿门襟斜边 → 后领 → 另一侧门襟，整条不断开"""
    width = width or 40.0
    lapel = math.hypot(L, LAP_DX - NECK / 2.0)
    total = 2 * lapel + NECK + 20.0
    return {
        "name": "领缘条", "qty": 1, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (total, 0)), ("L", (total, width)), ("L", (0, width)), ("Z",)],
        "seams": [],
        "notches": [(lapel, 0), (lapel + NECK, 0)],
        "dims": [("L", (0, 0), (total, 0), "总长 %d × 宽 %d" % (round(total), round(width)))],
    }


def triangle(h, w=95.0, name="三角拼接"):
    return {
        "name": name, "qty": 1, "grain": (0, 1),
        "cmds": [("M", (0, 0)), ("L", (w, 0)), ("L", (0, h)), ("Z",)],
        "seams": [], "notches": [], "dims": [("L", (0, 0), (0, h), "高 %d" % h)],
    }


def tie(length=200.0, width=20.0):
    return {
        "name": "系带", "qty": 2, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (length, 0)), ("L", (length, width)), ("L", (0, width)), ("Z",)],
        "seams": [], "notches": [], "dims": [("L", (0, 0), (length, 0), "长 200")],
    }


def hem_facing(length=None, width=30.0):
    length = length or (2 * HALF)
    return {
        "name": "下摆绢衬条", "qty": 1, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (length, 0)), ("L", (length, width)), ("L", (0, width)), ("Z",)],
        "seams": [], "notches": [], "dims": [("L", (0, 0), (length, 0), "长 %d × 宽 30" % round(length))],
    }


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


# ---------- 几何工具 ----------
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
