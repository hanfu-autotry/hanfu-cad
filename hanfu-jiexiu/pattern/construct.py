# -*- coding: utf-8 -*-
"""对穿交（接袖版）· 版型构造（纯函数）

**这个模块只有几何**：给参数字典 → 返回裁片，没有 IO、没有模块级状态。
出图（排版 / SVG / 侧车）留在 build.py，谁要几何就 import 这里。

── 两类参数，别混 ─────────────────────────────────────────────
输入（图上 / 尺表给的数）：L W_HEM EASE X_ARM Y_ARM X_SHLD SLEEVE_LEN JS
                          CUFF WRIST NECK OV HEM_RISE COL_W
派生（由约束解出，只能在本模块 derive() 里算）：HALF X_CUFF X_JS S LAP_DX
                          Y_CUFF_TOP Y_SEAM_BOT SEAM_H UND_ANG U_ARM …
片函数只读 derive 的结果，不在片里现算 —— 否则两片容易算岔。

── 整体数学约束（constraints() 可逐条量残差）──────────────────
① **袖底直线共线**：腋点 → 接袖根下缘 → 腕口下角 三点共线；
   接袖缝只是这条线上的一道垂直切口，所以接缝处天然零折角。
② **袖根自洽**：`Y_SEAM_BOT` 必须落在那条直线上（残差 0）。
   `seam_mode="seam"` 时反过来——给定 SEAM_H，解出腕口高（明制高交领用这条）；
   `seam_mode="wrist"` 时给定腕口高，解出 SEAM_H（接袖版用这条）。
③ **通袖**：S = 2×(X_SHLD + SLEEVE_LEN + JS)，即肩点到腕口的两倍。
④ **摆宽**：HALF = W_HEM/2×EASE，摆弧从 (0,0) 到 (HALF, HEM_RISE)。
⑤ **门襟**：斜边从 (NECK/2, L) 到 (LAP_DX, 0)，grain 由这条边的方向派生，
   不写死 9.3°。
⑥ **摆弧形状与摆宽无关**：控制点按 HALF/HEM_RISE 相对参考尺寸等比缩放，
   换码时弧型不变形。
"""

import math

# 摆弧控制点的参考尺寸：接袖版默认摆半宽 399 / 起翘 60。
# 控制点按 (HALF/399, RISE/60) 等比缩放 → 任意摆宽都保持同一弧型；
# 参考值下缩放系数正好 1.0，所以既有产物一个字节都不动。
HEM_REF = (399.0, 60.0)
HEM_CTRL = ((200, 5), (400, 30))   # 整数常量：参考尺寸下原样用，保持既有产物字节不变
R_ARM_F = 45.0          # 腋下 G1 过渡半径（版型上等价于腋下小圆角）
R_SIDE = 70.0           # 侧缝与腋点的圆角
TILT_DEG = 0.8          # 袖上缘自肩点起的下垂角


# ── 几何小工具 ────────────────────────────────────────────────
def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n)


def _off(p, d, r):
    return (p[0] + d[0] * r, p[1] + d[1] * r)


def _bez(p0, p1, p2, p3, t):
    mt = 1 - t
    return (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])


def _tan(seg, t0=0.0, t1=1.0, h=0.002):
    a = _bez(seg[0], seg[1], seg[2], seg[3], max(0.0, t0 - h))
    b = _bez(seg[0], seg[1], seg[2], seg[3], min(1.0, t1 + h))
    return _unit(a, b)


def blend(A, tA, B, tB, k=0.92):
    """G1 三次混合：两端切线分别与相邻段一致 → 无折角"""
    d = math.hypot(B[0] - A[0], B[1] - A[1]) / 3.0 * k
    c1 = (A[0] + tA[0] * d, A[1] + tA[1] * d)
    c2 = (B[0] - tB[0] * d, B[1] - tB[1] * d)
    return ("C", c1, c2, B)


def sleeve_y(d, x):
    """袖上缘：自肩点起按 TILT 微下垂"""
    return d["Y_TOP"] - (abs(x) - d["X_SHLD"]) * math.tan(d["TILT"])


# ── 派生量（唯一入口）──────────────────────────────────────────
def derive(p, seam_mode="wrist"):
    """把输入参数解成一套自洽的派生量。

    seam_mode:
      "wrist" —— 给腕口高 WRIST，解出 SEAM_H（接袖版：腕口是硬指标）
      "seam"  —— 给接袖根高 SEAM_H，解出腕口高 WRIST（明制：袖根是实测指标）
    """
    d = dict(p)
    d["EASE"] = p.get("EASE", 1.0)
    d["TILT_DEG"] = p.get("TILT_DEG", TILT_DEG)
    d["TILT"] = math.radians(d["TILT_DEG"])

    d["HALF"] = p["W_HEM"] / 2.0 * d["EASE"]
    d["X_CUFF"] = p["X_SHLD"] + p["SLEEVE_LEN"]
    d["X_JS"] = d["X_CUFF"] + p["JS"]
    d["S"] = 2 * d["X_JS"]                       # 通袖
    d["LAP_DX"] = p["OV"] / 2.0                  # 门襟边越中量
    d["MENJIN_ANG"] = math.atan2(d["LAP_DX"] - p["NECK"] / 2.0, p["L"])
    d["Y_TOP"] = p["L"]
    d["Y_CUFF_TOP"] = sleeve_y(d, d["X_CUFF"])
    d["Y_CUFF_BOT"] = d["Y_CUFF_TOP"] - p["CUFF"]
    d["Y_JS_TOP"] = sleeve_y(d, d["X_JS"])

    if seam_mode == "seam" and p.get("SEAM_H"):
        # ① 给定袖根 → 袖底直线过 (X_CUFF, Y_CUFF_TOP-SEAM_H)，延长到腕口
        d["SEAM_H"] = float(p["SEAM_H"])
        y_seam_bot = d["Y_CUFF_TOP"] - d["SEAM_H"]
        ang = math.atan2(y_seam_bot - p["Y_ARM"], d["X_CUFF"] - p["X_ARM"])
        d["Y_JS_BOT"] = p["Y_ARM"] + (d["X_JS"] - p["X_ARM"]) * math.tan(ang)
        d["WRIST"] = d["Y_JS_TOP"] - d["Y_JS_BOT"]
    else:
        # ①' 给定腕口 → 直线通到腕口下角，袖根是派生值
        d["WRIST"] = float(p.get("WRIST", p["CUFF"]))
        d["Y_JS_BOT"] = d["Y_JS_TOP"] - d["WRIST"]
        ang = math.atan2(d["Y_JS_BOT"] - p["Y_ARM"], d["X_JS"] - p["X_ARM"])
        y_seam_bot = p["Y_ARM"] + (d["X_CUFF"] - p["X_ARM"]) * math.tan(ang)
        d["SEAM_H"] = d["Y_CUFF_TOP"] - y_seam_bot

    d["Y_SEAM_BOT"] = y_seam_bot
    d["UND_ANG"] = ang
    d["UND_U"] = (math.cos(ang), math.sin(ang))
    d["Z"] = (d["X_JS"], d["Y_JS_BOT"])
    d["U_ARM"] = (p["X_ARM"] + R_ARM_F * d["UND_U"][0],
                  p["Y_ARM"] + R_ARM_F * d["UND_U"][1])
    return d


# ── 裁片 ─────────────────────────────────────────────────────
def hem_ctrl(half, rise):
    """摆弧控制点：按参考尺寸等比缩放，换码不变形。

    参考尺寸下原样返回常量（连 int/float 都不变），保证既有产物零改动。
    """
    kx, ky = half / HEM_REF[0], rise / HEM_REF[1]
    if kx == 1.0 and ky == 1.0:
        return HEM_CTRL
    return ((HEM_CTRL[0][0] * kx, HEM_CTRL[0][1] * ky),
            (HEM_CTRL[1][0] * kx, HEM_CTRL[1][1] * ky))


def back_half(d):
    """后片半（×2 镜像，后中缝对折）——衣身袖止于接袖根，袖底一条直线"""
    L, HALF, RISE = d["L"], d["HALF"], d["HEM_RISE"]
    c1, c2 = hem_ctrl(HALF, RISE)
    arm = (d["X_ARM"], d["Y_ARM"])
    d_side = _unit((HALF, RISE), arm)
    A_a = _off(arm, d_side, -R_SIDE)
    B_a = (d["U_ARM"][0], d["U_ARM"][1])
    cmds = [("M", (0, 0)), ("C", c1, c2, (HALF, RISE)),
            ("L", A_a), blend(A_a, d_side, B_a, d["UND_U"]),
            ("L", (d["X_CUFF"], d["Y_SEAM_BOT"])),
            ("L", (d["X_CUFF"], d["Y_CUFF_TOP"])),
            ("L", (d["X_SHLD"], L)),
            ("L", (d["NECK"] / 2, L)), ("L", (0, L)), ("Z",)]
    return {
        "name": "后片半", "qty": 2, "grain": (0, 1), "cmds": cmds,
        "seams": [[(0, 0), (0, L)]],
        "notches": [arm, (0, 0)],
        "dims": [("L", (0, 0), (0, L), "后中长 %d" % round(L)),
                 ("L", (0, RISE), (HALF, RISE), "摆半宽 %d / 起翘 %d" % (round(HALF), round(RISE))),
                 ("L", (d["X_ARM"], d["Y_ARM"]), (d["X_ARM"], L), "腋深 %d" % round(L - d["Y_ARM"])),
                 ("L", (d["X_CUFF"] + 44, d["Y_SEAM_BOT"]), (d["X_CUFF"] + 44, d["Y_CUFF_TOP"]),
                  "袖根 %d" % round(d["SEAM_H"])),
                 ("L", (d["X_SHLD"], L), (d["X_CUFF"], d["Y_CUFF_TOP"]),
                  "衣身袖长 %d" % round(d["SLEEVE_LEN"]))],
    }


def front_panel(d):
    """前片（×2 镜像；右衽时穿着者左片为外襟）——门襟内端让开 NECK/2 形成预开领"""
    L, HALF, RISE, LAP = d["L"], d["HALF"], d["HEM_RISE"], d["LAP_DX"]
    c1, c2 = hem_ctrl(HALF, RISE)
    arm = (-d["X_ARM"], d["Y_ARM"])
    d_side = _unit((-HALF, RISE), arm)
    A_a = _off(arm, d_side, -R_SIDE)
    B_a = (-d["U_ARM"][0], d["U_ARM"][1])
    tb = d["UND_U"]
    cmds = [("M", (d["NECK"] / 2, L)), ("L", (LAP, 0)),
            ("C", (-c1[0], c1[1]), (-c2[0], c2[1]), (-HALF, RISE)),
            ("L", A_a), blend(A_a, d_side, B_a, (-tb[0], tb[1])),
            ("L", (-d["X_CUFF"], d["Y_SEAM_BOT"])),
            ("L", (-d["X_CUFF"], d["Y_CUFF_TOP"])),
            ("L", (-d["X_SHLD"], L)),
            ("L", (d["NECK"] / 2, L)), ("Z",)]
    return {
        "name": "前片", "qty": 2,
        "grain": (math.sin(d["MENJIN_ANG"]), -math.cos(d["MENJIN_ANG"])),
        "cmds": cmds,
        "seams": [],
        "notches": [arm, (d["NECK"] / 2, L)],
        "dims": [("L", (-HALF, -60), (LAP, -60), "单边摆宽 %d" % round(HALF + LAP)),
                 ("L", (LAP, -130), (0, -130), "越中 %d" % round(LAP)),
                 ("L", (d["NECK"] / 2, L), (LAP, 0), "门襟斜 %.1f°" % math.degrees(d["MENJIN_ANG"])),
                 ("L", (d["NECK"] / 2, L), (0, L), "预开领半 %d" % round(d["NECK"] / 2))],
    }


def sleeve_ext(d):
    """接袖（×4，前后片各一）：根边=衣身袖口（垂直），袖底为袖底线的延续，腕口垂直"""
    cmds = [("M", (d["X_CUFF"], d["Y_SEAM_BOT"])), ("L", d["Z"]),
            ("L", (d["X_JS"], d["Y_JS_TOP"])), ("L", (d["X_CUFF"], d["Y_CUFF_TOP"])), ("Z",)]
    return {
        "name": "接袖", "qty": 4, "grain": (1, 0), "cmds": cmds,
        "seams": [],
        "notches": [(d["X_CUFF"], d["Y_SEAM_BOT"]), (d["X_CUFF"], d["Y_CUFF_TOP"])],
        "dims": [("L", (d["X_CUFF"], d["Y_SEAM_BOT"]), (d["X_CUFF"], d["Y_CUFF_TOP"]),
                  "袖根 %d" % round(d["SEAM_H"])),
                 ("L", (d["X_JS"], d["Y_JS_BOT"]), (d["X_JS"], d["Y_JS_TOP"]),
                  "腕口 %d" % round(d["WRIST"])),
                 ("L", (d["X_CUFF"], d["Y_SEAM_BOT"]), (d["X_JS"], d["Y_JS_BOT"]),
                  "接袖长 %d" % round(d["JS"]))],
    }


def collar_band(d, width=None):
    """领缘条（领襟一体，直丝）：沿门襟斜边 → 后领 → 另一侧门襟，整条不断开"""
    width = width or d.get("COL_W") or 40.0
    lapel = math.hypot(d["L"], d["LAP_DX"] - d["NECK"] / 2.0)
    total = 2 * lapel + d["NECK"] + 20.0
    return {
        "name": "领缘条", "qty": 1, "grain": (1, 0),
        "cmds": [("M", (0, 0)), ("L", (total, 0)), ("L", (total, width)), ("L", (0, width)), ("Z",)],
        "seams": [],
        "notches": [(lapel, 0), (lapel + d["NECK"], 0)],
        "dims": [("L", (0, 0), (total, 0), "总长 %d × 宽 %d" % (round(total), round(width)))],
    }


def rect_piece(name, w, h, qty=1, grain=(1, 0), extra_dims=None):
    """矩形附件（系带 / 下摆绢衬条 / 三角拼接的直角边都走它）"""
    return {
        "name": name, "qty": qty, "grain": grain,
        "cmds": [("M", (0, 0)), ("L", (w, 0)), ("L", (w, h)), ("L", (0, h)), ("Z",)],
        "seams": [], "notches": [],
        "dims": extra_dims or [("L", (0, 0), (w, 0), "长 %d × 宽 %d" % (round(w), round(h)))],
    }


def triangle(name, h, w=95.0):
    return {
        "name": name, "qty": 1, "grain": (0, 1),
        "cmds": [("M", (0, 0)), ("L", (w, 0)), ("L", (0, h)), ("Z",)],
        "seams": [], "notches": [], "dims": [("L", (0, 0), (0, h), "高 %d" % h)],
    }


def tie(length=200.0, width=20.0):
    return rect_piece("系带", length, width, qty=2,
                      extra_dims=[("L", (0, 0), (length, 0), "长 200")])


def hem_facing(length, width=30.0):
    return rect_piece("下摆绢衬条", length, width,
                      extra_dims=[("L", (0, 0), (length, 0), "长 %d × 宽 30" % round(length))])


def pieces(p, seam_mode="wrist", with_extras=True):
    """一套参数 → (派生量, 裁片表)。with_extras=False 只出衣身四片（给派生版型取片用）"""
    d = derive(p, seam_mode)
    out = [back_half(d), front_panel(d), sleeve_ext(d), collar_band(d, p.get("COL_W"))]
    if with_extras:
        out += [triangle("三角拼接 A", 170),
                triangle("三角拼接 B", 140),
                tie(),
                hem_facing(2 * d["HALF"])]
    return d, out


# ── 约束自检 ─────────────────────────────────────────────────
def constraints(d):
    """整体数学约束的残差表：(名称, 实算, 期望, 容差, 说明)。

    全部为 0 才叫「整体自洽」。改成别的参数后跑一遍，就知道哪条被破坏了。
    """
    rows = []

    def add(name, got, want, tol, note=""):
        rows.append((name, got, want, tol, note))

    # ① 袖底直线共线：接袖根下缘必须在「腋点 → 腕口下角」的连线上
    ax, ay = d["X_ARM"], d["Y_ARM"]
    zx, zy = d["Z"]
    x = d["X_CUFF"]
    y_line = ay + (x - ax) * (zy - ay) / (zx - ax)
    add("袖底共线（接袖根下缘落在直线上）", d["Y_SEAM_BOT"], y_line, 0.05,
        "腋点→腕口 一条直线，接缝处零折角")

    # ② 袖根自洽：袖根高 = 袖口上缘 − 袖底在该处的高度
    add("袖根 = 袖口上缘 − 袖底（X_CUFF 处）", d["SEAM_H"],
        d["Y_CUFF_TOP"] - d["Y_SEAM_BOT"], 0.05)

    # ③ 通袖
    add("通袖 = 2×(肩点 + 衣身袖 + 接袖)", d["S"],
        2 * (d["X_SHLD"] + d["SLEEVE_LEN"] + d["JS"]), 0.05)

    # ④ 摆宽
    add("摆半宽 = 摆宽/2×放量", d["HALF"], d["W_HEM"] / 2.0 * d["EASE"], 0.05)

    # ⑤ 门襟 grain 与斜边同向
    ang = math.atan2(d["LAP_DX"] - d["NECK"] / 2.0, d["L"])
    add("门襟斜角（grain 派生）", d["MENJIN_ANG"], ang, 1e-9)

    # ⑥ 接袖腕口边与袖口竖边平行（都是竖直线）→ 只查宽度为正
    add("腕口宽 > 0", d["WRIST"], max(d["WRIST"], 1e-6), 1e-6)
    return rows


def report(d, only_bad=False):
    """约束表 → 可打印的行"""
    lines = []
    for name, got, want, tol, note in constraints(d):
        ok = abs(got - want) <= tol
        if ok and only_bad:
            continue
        lines.append("%-4s %-34s %10.3f %10.3f  Δ%+.3f%s"
                     % ("PASS" if ok else "FAIL", name, got, want, got - want,
                        ("  ｜" + note) if note else ""))
    return lines
