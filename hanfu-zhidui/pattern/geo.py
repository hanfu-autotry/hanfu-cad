# -*- coding: utf-8 -*-
"""直领对襟 · 几何（逐步绘图）

底：沿用 `hanfu-cad`（对穿交半臂）的裁片
`hanfu-cad/pattern/对穿交_右衽_裁片图.pieces.json` —— **只读**，不改它一行。
开领/装领条的口径：**完全参照 `hanfu-shenyi` 的「原始直领交襟衣」V1**
（`hanfu-shenyi/pattern/build.py` 的 `_DEF`，本模块用 ast 直接读它，不抄数字）。

第 1 步（用户 2026-11-09）：在现有模板上移除所有，只留**领条**与**后片**；
  再把后片**复制一份命名为前片**。几何全部照抄模板。
第 2 步（用户 2026-11-09）：**完全参照 通裁·原始直领 的处理 开领宽、装领条**：
  · 开领宽 160（＝V1 `SLIT_HALF` 80 ×2）→ 前片沿中缝侧全高切掉 80；
  · 装领条：领条宽 40 压在剪口线上（每边可见 40 ＝V1 `LAPEL_FOLD`），中间露出后片 80；
  · 后领：领条在领口向上折转成梯形，底 160 → 顶 89（`NECK_TOP_HALF` 44.5×2），
    露出 77（`NECK_H`）。
  领条本身沿用模板 1850×40（notch 825 / 1025 → 后领段 200），未改；见 OPEN_ITEM。

模板里被移除的：前片、三角拼接 A/B、系带、下摆绢衬条。
"""
import ast
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))

TPL_PATH = os.path.join(WS, "hanfu-cad", "pattern", "对穿交_右衽_裁片图.pieces.json")
TPL = json.load(open(TPL_PATH, encoding="utf-8"))
PARAMS = dict(TPL["params"])          # 模板参数原样，本步不动任何量

# 保留 / 丢弃的口径：只按名字挑，不按位置猜
KEEP = ("领缘条", "后片半")            # 模板里的原名
DROP = ("前片", "三角拼接 A", "三角拼接 B", "系带", "下摆绢衬条")


# ── 口径来源：原始直领交襟衣 V1 的程序参数 ─────────────────────────
V1_SRC = os.path.join(WS, "hanfu-shenyi", "pattern", "build.py")


def v1_def():
    """直接读 V1 程序里的 `_DEF` 字面量（不执行它，避免写出图文件）。

    这样「完全参照原始直领」就是**跟着那份程序走**：它改口径，这里跟着变。
    `_DEF = dict(A=1.0, ...)` 就按关键字参数取，纯字面量字典则直接 literal_eval。
    """
    src = open(V1_SRC, encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_DEF" for t in node.targets):
            v = node.value
            if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "dict":
                return {kw.arg: ast.literal_eval(kw.value) for kw in v.keywords}
            return ast.literal_eval(v)
    raise RuntimeError("在 %s 里找不到 _DEF" % V1_SRC)


V1 = v1_def()

# 可调量（＝studio 上的旋钮）；默认值全部来自 V1 的 _DEF，没有一个是自己拍的。
DEFAULTS = dict(
    NECK_W=float(V1["SLIT_HALF"]) * 2.0,   # 160 开领宽（＝两条剪口线的间距）
    COLLAR_W=float(V1["COLLAR_W"]),        # 95  领条宽（可见 40，其余折在里面）
    LAPEL_FOLD=float(V1["LAPEL_FOLD"]),    # 40  领条压边（每边可见宽）
    NECK_H=float(V1["NECK_H"]),            # 77  领条在领口立起的露出高
)
# 不挂旋钮、照 V1 固定：折转段顶半宽（顶边 89）
NECK_TOP_HALF = float(V1["NECK_TOP_HALF"])


def params(overrides=None):
    """本版型的参数表：DEFAULTS 上叠 overrides。"""
    q = dict(DEFAULTS)
    q.update({k: float(v) for k, v in (overrides or {}).items()})
    return q


def slit_half(q):
    """剪口线半间距 ＝ 开领宽的一半。"""
    return q["NECK_W"] / 2.0


# 领子的几何关系（用户 2026-11-09「领子几何关系错误，重看直领交襟」后重推）：
#   V1 的领条是一条**直的整带**，成型后呈倒 U：左前襟 → 绕后颈 → 右前襟。
#   · 前襟那两段的长度 ＝ 前片剪口边长（沿 x = 剪口线那条直边，摆→肩线）；
#   · 绕后颈那一段的长度 ＝ 开领宽（＝两条剪口线在肩线处的间距），
#     折起来立起的那个梯形是**带子的宽度**立起来，不额外吃长度：
#     可见高 NECK_H 77 ≤ 带宽 95，顶边 89 比底边 160 短是因为内侧转弯短。
#   ⇒ 领条长 ＝ 2 × 剪口边长 ＋ 开领宽。
#   模板那条 1850×40（notch 825/1025 → 后领段 200）是**对穿交半臂**的口径，
#   与开领宽 160 对不上、宽度也不够压边，故本版按上式重算（见 collar_piece）。


# ── 模板片 ─────────────────────────────────────────────────────────
def tpl_piece(name):
    """取模板的一片（深拷贝，改它不会污染模板）。"""
    for p in TPL["pieces"]:
        if p["name"] == name:
            return copy.deepcopy(p)
    raise KeyError("模板里没有这一片：%s（现有：%s）"
                   % (name, "、".join(p["name"] for p in TPL["pieces"])))


def base_pieces():
    """第 1 步的三种片：领条 / 后片 / 前片（＝后片复制）。"""
    collar = tpl_piece("领缘条")
    collar["name"] = "领条"

    back = tpl_piece("后片半")
    back["name"] = "后片"

    front = copy.deepcopy(back)        # 复制后片
    front["name"] = "前片"             # 命名为前片

    return [collar, back, front]


# ── 第 2 步：开领（沿 x=x_cut 全高切掉中缝侧窄条）──────────────────
def _cubic_x_at(p0, p1, p2, p3, t):
    mt = 1.0 - t
    return (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
            + 3 * mt * t * t * p2[0] + t ** 3 * p3[0])


def _cubic_y_at(p0, p1, p2, p3, t):
    mt = 1.0 - t
    return (mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
            + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])


def _cubic_t_at_x(p0, p1, p2, p3, x, n=80):
    """三次贝塞尔上 x(t)=x 的 t（用二分；这一段 x 单调，适用）。"""
    lo, hi = 0.0, 1.0
    for _ in range(n):
        mid = (lo + hi) / 2.0
        if _cubic_x_at(p0, p1, p2, p3, mid) < x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _split_cubic(p0, p1, p2, p3, t):
    """de Casteljau 在 t 处切开，返回 (左半 4 点, 右半 4 点)。"""
    def lerp(a, b, s):
        return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s)

    a = lerp(p0, p1, t)
    b = lerp(p1, p2, t)
    c = lerp(p2, p3, t)
    d = lerp(a, b, t)
    e = lerp(b, c, t)
    f = lerp(d, e, t)
    return ((p0, a, d, f), (f, e, c, p3))


def open_neck_cmds(cmds, x_cut):
    """把「后片半」的闭合 cmds 沿 x = x_cut 全高切掉中缝侧那一条。

    只动两处、其余原样（曲线仍是曲线，不退化成折线）：
      · 第一段（下摆三次曲线）在 x=x_cut 处 de Casteljau 截断，起点改到截点；
      · 顶边最后一点 (0, L) 改成 (x_cut, L)。
    `x_cut = SLIT_HALF` → 前中留出 2×80 = 160 的开口（开领宽）。

    依赖后片半的 cmds 次序：M (0,0) / C 下摆 / L / C / C / C / L / C / L / L / L (0,L) / Z。
    """
    assert cmds[0][0] == "M" and cmds[1][0] == "C", "后片半的 cmds 结构与预期不符"

    p0 = tuple(cmds[0][1])
    p1, p2, p3 = [tuple(q) for q in cmds[1][1:4]]
    t = _cubic_t_at_x(p0, p1, p2, p3, x_cut)
    left, right = _split_cubic(p0, p1, p2, p3, t)

    out = [["M", [round(right[0][0], 4), round(right[0][1], 4)]]]
    out.append(["C"] + [[round(q[0], 4), round(q[1], 4)] for q in right[1:4]])
    for seg in cmds[2:-2]:                      # 腋圆角 → 袖口 → 肩点 → (95, L)
        out.append([seg[0]] + [list(q) for q in seg[1:]])
    y_top = cmds[-2][1][1]                      # 顶边高度（＝肩线 y）
    out.append(["L", [x_cut, y_top]])
    out.append(["Z"])
    return out, dict(low=right[0], top=(x_cut, y_top))


def neck_cut_len(q=None):
    """前片剪口边长：沿剪口线那条直边，从摆到肩线。

    ＝ 肩线 y − 下摆弧在 x=剪口线 处的 y（用切开时算出来的那两个端点，不另量）。
    """
    q = q or params()
    cmds, pts = open_neck_cmds(tpl_piece("后片半")["cmds"], slit_half(q))
    return pts["top"][1] - pts["low"][1]


def collar_length(q=None):
    """领条长 ＝ 2 × 前襟（剪口边长） ＋ 后领段（＝开领宽）。见文件头那段推导。"""
    q = q or params()
    return 2.0 * neck_cut_len(q) + q["NECK_W"]


def collar_piece(q=None):
    """领条 ×1：长＝2×前襟＋开领宽，宽＝COLLAR_W；直丝沿长。

    两条 notch 标出后领段的两端（＝两条剪口线落在带子上的位置）。
    """
    q = q or params()
    CL = collar_length(q)
    FL = neck_cut_len(q)
    return dict(
        name="领条", qty=1,
        cmds=[["M", [0.0, 0.0]], ["L", [CL, 0.0]],
              ["L", [CL, q["COLLAR_W"]]], ["L", [0.0, q["COLLAR_W"]]], ["Z"]],
        grain=[1, 0],
        notches=[[round(FL, 4), 0.0], [round(FL + q["NECK_W"], 4), 0.0]],
        cmds_note="长 %.2f ＝ 2×%.2f ＋ %.0f" % (CL, FL, q["NECK_W"]),
    )


def step2_pieces(q=None):
    """第 2 步的三种片：领条（按开领重算）/ 后片（原样）/ 前片（开领）。"""
    q = q or params()
    x_cut = slit_half(q)

    collar = collar_piece(q)

    back = tpl_piece("后片半")
    back["name"] = "后片"

    front = tpl_piece("后片半")
    front["name"] = "前片"
    front["cmds"], neck_pts = open_neck_cmds(front["cmds"], x_cut)
    # 中缝侧原来的刀口 (0,0) 落在切掉的那条里，去掉；补一个剪口点 (x_cut, L)
    front["notches"] = [n for n in (front.get("notches") or []) if n[0] >= x_cut]
    front["notches"].append([x_cut, neck_pts["top"][1]])

    return [collar, back, front]


# ── 片表（给 sheet.write_sheet）─────────────────────────────────────
def collar_size(q=None):
    """领条的长 × 宽（本版按开领重算的那一条）。"""
    q = q or params()
    return collar_length(q), q["COLLAR_W"]


def sheet_pieces(pieces=None, step=1, q=None):
    """裁片图片表（字段对齐 sheet.write_sheet）。

    尺寸标注只用几何里现成的端点，不新造量。
    """
    import sheet as _sh

    q = q or params()
    x_cut = slit_half(q)
    out = []
    for p in (pieces or base_pieces()):
        nm = p["name"]
        x0, y0, x1, y1 = _sh.real_bbox(p["cmds"])
        w, h = x1 - x0, y1 - y0
        if nm == "领条":
            dims = [("L", [x0, y0], [x1, y0], "领条长 %.0f" % w),
                    ("L", [x1, y0], [x1, y1], "宽 %.0f" % h)]
            note = "后领段 %.0f＝开领宽" % q["NECK_W"]
        elif nm == "前片":
            dims = [("L", [x0, y0], [x0, y1], "前襟 %.0f" % h)]
            note = ("中缝侧切 %.0f（开领宽 %.0f）" % (x_cut, q["NECK_W"])
                    if step == 2 else "＝后片复制，几何相同")
        else:
            dims = [("L", [x0, y0], [x0, y1], "后中长 %.0f" % h)]
            note = "模板后片半原样"
        out.append(dict(name=nm, qty=p["qty"], cmds=p["cmds"],
                        grain=list(p.get("grain") or [0, 1]),
                        notches=[list(n) for n in (p.get("notches") or [])],
                        marks=[], dims=dims, note=note))
    return out
