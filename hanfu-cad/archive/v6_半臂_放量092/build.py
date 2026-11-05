# -*- coding: utf-8 -*-
"""
对穿交（钱氏墓/钱樟夫妇墓 鸟衔花枝纹缎夹袄）裁片图生成器
右衽 · 单层 · 净版 · 单位 mm

量纲锚点：中国丝绸博物馆修复报告实测
  半臂：袖长 265 / 袖口 195 / 衣长 825 / 摆宽 1150（放量 0.92）/ 单边 710 / 交叠 270
推定（图上标注但几何不自洽，已单列待确认）：
  腋深 395（=衣长-袖根）· 袖根高 395 · 接袖位 600 · 门襟偏角 9.3° · 袖中线偏 5°
"""
import math, os, json

L      = 825.0    # 衣长（肩线→下摆，等于衣长标注）
S      = 2180.0   # 通袖
W_HEM  = 1250.0   # 平铺摆宽
HEM_RISE = 60.0              # 下摆弧：侧缝处比中缝抬高（官图实测 ≈58）
P_HEM  = 760.0    # 前片单边下摆宽（侧缝→门襟边）
OV     = 270.0    # 前襟交叠（=2×135）
CUFF   = 195.0    # 袖口净平开口（围 390）
NECK   = 190.0    # 后领宽
EASE   = 0.92               # 放量系数（1.0 = 文物原大）
HALF   = W_HEM / 2 * EASE   # 侧缝（放量后）
X_ARM  = 447.0 * EASE       # 腋点（× 放量）
Y_ARM  = 512.0              # 腋点高（像素拟合，腋深 313）
X_SHLD = 560.0              # 肩点
X_SEAM = 600.0              # 接袖线
SLEEVE_LEN = 265.0             # 半臂：肩点→袖口
X_CUFF = X_SHLD + SLEEVE_LEN   # 袖口外端
TILT   = math.radians(0.8)  # 袖中线偏角（图测：袖端仅微下垂）
LAP_DX = OV / 2             # 135 门襟边越中量
NECK_DIP = 0.0              # 后领不起凹（立领由领缘条竖起，见装配）


Y_TOP = L + NECK_DIP


def sleeve_y(x):
    """袖上缘：自肩点起微下垂 0.8°"""
    return Y_TOP - (abs(x) - X_SHLD) * math.tan(TILT)


Y_CUFF_TOP = sleeve_y(X_CUFF)
Y_CUFF_BOT = Y_CUFF_TOP - CUFF

# 袖底弧：腋点 → 下垂低点 → 袖口下缘（官图实测为深凹弧，非常见直线）
U_P0 = (X_ARM, Y_ARM)
U_P1 = (560.0, 536.0)
U_P2 = (740.0, 592.0)
U_P3 = (X_CUFF, Y_CUFF_BOT)


def under_y(x, n=400):
    """袖底弧在给定 |x| 处的高度"""
    x = abs(x)
    pts = [_bez(*U_P0, *U_P1, *U_P2, *U_P3, t=i / n) for i in range(n + 1)]
    for (px_, py_) in pts:
        if px_ >= x:
            return py_
    return pts[-1][1]


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


def _cut_at(seg, target, from_end=True, r=40.0, n=4000):
    """在距端点 r 处切分，返回 (保留段, 切点, 切点切矢)"""
    t = 0.0 if not from_end else 1.0
    for i in range(1, n):
        tt = (1 - i / n) if from_end else (i / n)
        q = _bez(seg[0], seg[1], seg[2], seg[3], tt)
        if math.hypot(q[0] - target[0], q[1] - target[1]) >= r:
            t = tt
            break
    if from_end:
        head, _ = split_cubic(seg[0], seg[1], seg[2], seg[3], t)
        return head, head[3], _tan((head[0], head[1], head[2], head[3]), 1.0, 1.0)
    head, _ = split_cubic(seg[0], seg[1], seg[2], seg[3], t)
    return head, head[3], _tan((head[0], head[1], head[2], head[3]), 1.0, 1.0)


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


# 袖底弧：先按 接袖线 精确切分，两片共用同一段曲线 → 无缝、无折线
_T_ = None
for _i in range(1, 4001):
    if _bez(U_P0, U_P1, U_P2, U_P3, _i / 4000)[0] >= X_SEAM:
        _T_ = _i / 4000
        break
U_SEAM = _bez(U_P0, U_P1, U_P2, U_P3, _T_) if _T_ else U_P3
_IN_A, _IN_B = split_cubic(U_P0, U_P1, U_P2, U_P3, _T_)

# 腋点 G1 过渡半径（消除尖角，版型上等价于腋下小圆角）
R_ARM_F = 45.0


# 腋下圆角：在袖底弧上取距腋点 R 的点 B，弧本身从 B 起算，保证 C1 无缝
_T_ARM = 1.0
for _i in range(1, 4001):
    _p = _bez(U_P0, U_P1, U_P2, U_P3, _i / 4000)
    if math.hypot(_p[0] - U_P0[0], _p[1] - U_P0[1]) >= R_ARM_F:
        _T_ARM = _i / 4000
        break
U_ARM = _bez(U_P0, U_P1, U_P2, U_P3, _T_ARM)
_SP1, _SP2 = split_cubic(U_P0, U_P1, U_P2, U_P3, _T_ARM)


def _arm_junction(sx):
    """返回 (A=侧缝终点, 腋点, B=袖底弧起点)"""
    arm = (sx * X_ARM, Y_ARM)
    din = _unit(arm, (sx * HALF, 20))
    return _off(arm, din, R_ARM_F), arm, (sx * U_ARM[0], U_ARM[1])


def _under_cmds(sx, x_to):
    """袖底弧：从腋下圆角终点 B 走到 x_to，输出精确贝塞尔命令"""
    p0, p1, p2, p3 = _SP2
    if abs(abs(p3[0]) - abs(x_to)) > 0.5:
        tt = None
        for i in range(1, 4000):
            if abs(_bez(p0, p1, p2, p3, i / 4000)[0]) >= abs(x_to):
                tt = i / 4000
                break
        if tt:
            head, _ = split_cubic(p0, p1, p2, p3, tt)
            p0, p1, p2, p3 = head
    return [("C", (sx * p1[0], p1[1]), (sx * p2[0], p2[1]), (sx * p3[0], p3[1]))]


def _sleeve_end(sx):
    """袖底弧（腋下圆角终点 → 袖口下缘前 R 处）"""
    R = 20.0
    head, A_c, tA_c = _cut_at(_SP2, (X_CUFF, Y_CUFF_BOT), True, R)
    p0, p1, p2, p3 = head
    return ([("C", (sx * p1[0], p1[1]), (sx * p2[0], p2[1]), (sx * A_c[0], A_c[1]))],
            (sx * A_c[0], A_c[1]), (sx * tA_c[0], tA_c[1]))


def _cuff_top(sx):
    """袖口竖边 + 上角圆角 + 袖上缘 → 肩点"""
    R = 20.0
    B_c = (sx * X_CUFF, Y_CUFF_BOT + R)
    Ctop = (sx * X_CUFF, Y_CUFF_TOP - R)
    d_top = _unit((sx * X_CUFF, Y_CUFF_TOP), (sx * X_SHLD, L))
    D = _off((sx * X_CUFF, Y_CUFF_TOP), d_top, R)
    return [("L", Ctop), blend(Ctop, (0.0, 1.0), D, d_top), ("L", (sx * X_SHLD, L))]


def back_half():
    """后片半（×2 镜像，后中缝对折）——半臂短袖，袖底斜下并入侧缝"""
    hem = ((0, 0), (200, 5), (400, 30), (HALF, HEM_RISE))
    R = 70.0
    d_side = _unit((HALF, HEM_RISE), (X_ARM, Y_ARM))
    arm = (X_ARM, Y_ARM)
    A_a = _off(arm, d_side, -R)
    B_a = (U_ARM[0], U_ARM[1])
    tB_a = _tan(_SP2, 0.0, 0.0)
    tail, A_c, tA_c = _sleeve_end(1.0)
    cmds = [("M", (0, 0)), ("C", hem[1], hem[2], hem[3]),
            ("L", A_a), blend(A_a, d_side, B_a, tB_a)]
    cmds += tail
    cmds += [blend(A_c, tA_c, (X_CUFF, Y_CUFF_BOT + 20.0), (0.0, 1.0))]
    cmds += _cuff_top(1.0)
    cmds += [("L", (NECK / 2, L)), ("L", (0, L)), ("Z",)]
    return {
        "name": "后片半", "qty": 2, "grain": (0, 1), "cmds": cmds,
        "seams": [[(0, 0), (0, L)]],
        "notches": [arm, (0, 0)],
        "dims": [("L", (0, 0), (0, L), "后中长 825"),
                 ("L", (0, HEM_RISE), (HALF, HEM_RISE), "摆半宽 %d / 起翘 %d" % (round(HALF), round(HEM_RISE))),
                 ("L", (X_ARM, Y_ARM), (X_ARM, L), "腋深 %d" % round(L - Y_ARM)),
                 ("L", (X_CUFF + 45, Y_CUFF_BOT), (X_CUFF + 45, Y_CUFF_TOP), "袖口 %d" % round(CUFF))],
    }


def front_panel():
    """前片（×2 镜像；右衽时穿着者左片为外襟）——半臂短袖"""
    hem = ((LAP_DX, 0), (-200, 5), (-400, 30), (-HALF, HEM_RISE))
    R = 70.0
    d_side = _unit((-HALF, HEM_RISE), (-X_ARM, Y_ARM))
    arm = (-X_ARM, Y_ARM)
    A_a = _off(arm, d_side, -R)
    B_a = (-U_ARM[0], U_ARM[1])
    tb = _tan(_SP2, 0.0, 0.0)
    tail, A_c, tA_c = _sleeve_end(-1.0)
    cmds = [("M", (0, L)), ("L", (LAP_DX, 0)), ("C", hem[1], hem[2], hem[3]),
            ("L", A_a), blend(A_a, d_side, B_a, (-tb[0], tb[1]))]
    cmds += tail
    cmds += [blend(A_c, tA_c, (-X_CUFF, Y_CUFF_BOT + 20.0), (0.0, 1.0))]
    cmds += _cuff_top(-1.0)
    cmds += [("L", (0, L)), ("Z",)]
    return {
        "name": "前片", "qty": 2, "grain": (math.sin(math.radians(9.3)), -math.cos(math.radians(9.3))),
        "cmds": cmds,
        "seams": [],
        "notches": [arm],
        "dims": [("L", (-HALF, -60), (LAP_DX, -60), "单边摆宽 %d" % round(HALF + LAP_DX)),
                 ("L", (LAP_DX, -130), (0, -130), "越中 %d" % round(LAP_DX)),
                 ("A", (0, L), (LAP_DX, 0), "门襟偏 9.3°")],
    }


def collar_band(width=40.0):
    """领缘条（领襟一体，直丝）：前门襟 825×2 + 后领弧 ≈200，整条不断开"""
    total = 2 * L + 200.0
    return {
        "name": "领缘条", "qty": 1, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (total, 0)), ("L", (total, width)), ("L", (0, width)), ("Z",)],
        "seams": [],
        "notches": [(L, 0), (L + 200, 0)],
        "dims": [("L", (0, 0), (total, 0), "总长 1850 × 宽 40")],
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
    collar_band(),
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
TITLE_H = 380.0
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
s.append('<title>对穿交 · 钱氏墓 鸟衔花枝纹缎夹袄 · 裁片图（右衽·单层·净版·mm）</title>')
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
            ty2 = my - (0 if vert else 20)
            s.append('  <text x="%.1f" y="%.1f" text-anchor="middle" transform="rotate(%.1f %.1f %.1f)">%s</text>' % (tx, ty2, rot, mx, my, txt))
        else:
            s.append('  <text x="%.1f" y="%.1f" text-anchor="middle" fill="%s">%s</text>' % ((ax + bx) / 2 + 30, (ay + by) / 2, RED, txt))
s.append('</g>')

s.append('<g id="LABEL" fill="%s" font-family="sans-serif">' % BLACK)
for i, p in enumerate(placed):
    sx0, sx1 = p["_slot"]
    x0, y0 = p["_box"][0], p["_box"][1]
    s.append('  <text x="%.1f" y="%.1f" font-size="30" font-weight="500">%02d %s ×%d</text>' % (x0, y0 - 30, i + 1, p["name"], p["qty"]))
s.append('</g>')

# ---------- 图框 + 100mm 校验标尺 ----------
ty = BODY_H + MARGIN * 0.4
s.append('<g id="BLOCK" stroke="%s" stroke-width="1.6" fill="none">' % BLACK)
s.append('  <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (MARGIN, ty, TOTAL_W - 2 * MARGIN, TITLE_H - 80))
s.append('</g>')
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('  <text x="%.1f" y="%.1f" font-size="38" font-weight="500">对穿交 · 明制 鸟衔花枝纹缎夹袄（右衽）裁片图</text>' % (MARGIN + 30, ty + 60))
s.append('  <text x="%.1f" y="%.1f" font-size="26">依据：无锡七房桥钱樟夫妇墓出土实物 · 中国丝绸博物馆修复报告   ｜   单位 mm   ｜   净版（未含缝份）   ｜   单层   ｜   半臂短袖   ｜   v6.0</text>' % (MARGIN + 30, ty + 105))
s.append('  <text x="%.1f" y="%.1f" font-size="26">衣长 %d   ｜   平铺摆宽 %d（放量 %.2f）   ｜   单边摆宽 %d   ｜   交叠 %d   ｜   袖口 %d</text>' % (
    MARGIN + 30, ty + 145, round(L), round(2 * HALF), EASE,
    round(HALF + LAP_DX), round(2 * LAP_DX), round(CUFF)))
s.append('</g>')
bx0 = MARGIN + 30
by0 = ty + 235
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
fp = os.path.join(out_dir, "对穿交_右衽_裁片图.svg")
open(fp, "w", encoding="utf-8").write("\n".join(s))

info = {
    "file": fp, "size": [round(TOTAL_W, 1), round(TOTAL_H, 1)],
    "params": {"L": L, "S": S, "W_HEM": W_HEM, "P_HEM": P_HEM, "OV": OV, "CUFF": CUFF,
               "NECK": NECK, "X_ARM": X_ARM, "Y_ARM": Y_ARM, "X_SEAM": X_SEAM,
               "X_CUFF": X_CUFF, "LAPEL_ANGLE": 9.3, "TILT": 5.0},
    "pieces": [{"name": p["name"], "qty": p["qty"], "w": round(p["_box"][2] - p["_box"][0], 1),
                "h": round(p["_box"][3] - p["_box"][1], 1)} for p in placed],
}
print(json.dumps(info, ensure_ascii=False, indent=1))
