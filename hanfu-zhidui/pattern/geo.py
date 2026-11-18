# -*- coding: utf-8 -*-
"""直领对襟 · 几何（逐步绘图）

底：沿用 `hanfu-cad`（对穿交半臂）的裁片
`hanfu-cad/pattern/对穿交_右衽_裁片图.pieces.json` —— **只读**，不改它一行。
开领/装领条的口径：**完全参照 `hanfu-shenyi` 的「原始直领交襟衣」V1**
（`hanfu-shenyi/pattern/build.py` 的 `_DEF`，本模块用 ast 直接读它，不抄数字）。

第 1 步（用户 2026-11-09）：在现有模板上移除所有，只留**领条**与**后片**；
  再把后片**复制一份命名为前片**。几何全部照抄模板。
第 2 步（用户 2026-11-09）：**完全参照 通裁·原始直领 的处理 开领宽、装领条**：
  · 开领宽 160（＝V1 `SLIT_HALF` 80 ×2）⇒ 前片内边＝弦 P→Q，
    P＝领口点 (80, L)、Q＝下摆曲线∩中缝 (0, 0)（用户 2026-11-18 改「开领法」，
    此前是沿 x=80 全高直切、下摆在 x=80 处截断）；
  · 装领条：领条宽 30（用户 2026-11-18 定）压在前襟边上，中间露出后片 160−2×30＝100；
  · 后领：领条在领口向上折转成梯形，底 NECK_W → 顶 2·M.x（由带宽 miter 得出），
    立起高 NECK_H ≡ 带宽 COLLAR_W（用户 2026-11-18；V1 的 77/89 作废）。
  领条本身沿用模板 1850×40（notch 825 / 1025 → 后领段 200），未改；见 OPEN_ITEM。

模板里被移除的：前片、三角拼接 A/B、系带、下摆绢衬条。
"""
import ast
import copy
import json
import math
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

# 可调量（＝studio 上的旋钮）。除 COLLAR_W 外默认值来自 V1 的 _DEF。
DEFAULTS = dict(
    NECK_W=float(V1["NECK_W"]),             # 160 开领宽（＝两条前襟边在肩线处的间距）
    COLLAR_W=30.0,                         # 30 领条宽（用户 2026-11-18 定 =3cm；V1 的 95 作废）
)
# 派生量（不挂旋钮）：
#   NECK_H ≡ COLLAR_W   立起高就是带宽（用户 2026-11-18 定）
#   顶半宽 M.x           由带宽在转角处的 miter 决定，见 trap_top_half()
#   LAPEL_FOLD           随 V1 的 95 一并取消（领条就是一条 3cm 带子）


def params(overrides=None):
    """本版型的参数表：DEFAULTS 上叠 overrides，再补派生量 NECK_H ≡ COLLAR_W。"""
    q = dict(DEFAULTS)
    q.update({k: float(v) for k, v in (overrides or {}).items()})
    q["NECK_H"] = q["COLLAR_W"]                 # 立起高 ≡ 带宽（用户 2026-11-18）
    lim = collar_w_limit(q)
    if not (0.0 < q["COLLAR_W"] < lim):
        raise ValueError(
            "领条宽 %.1f 超出开领宽 %.0f 下的可用范围 (0, %.1f)：再宽，后领带顶边会反折"
            % (q["COLLAR_W"], q["NECK_W"], lim))
    return q


def slit_half(q):
    """前襟边到中缝的距离 ＝ 开领宽的一半。"""
    return q["NECK_W"] / 2.0


def _neck(q):
    """(x_cut, L, n)：领口点半间距、肩线 y、襟缘长 √(x_cut²+L²)。"""
    x_cut = slit_half(q)
    y_top = float(tpl_piece("后片半")["cmds"][-2][1][1])      # 肩线（顶边）y
    return x_cut, y_top, math.hypot(x_cut, y_top)


def _k_miter(q):
    """顶半宽随带宽的衰减系数 k：M.x ＝ x_cut − k·COLLAR_W。

    M ＝ (P + COAR_W·n̂) 沿 û 走到 y ＝ L+COLLAR_W：
        M.x ＝ x_cut − LB·(L/n) + LB·(1 − x_cut/n)·(x_cut/L)
    """
    x_cut, L, n = _neck(q)
    return L / n - (1.0 - x_cut / n) * (x_cut / L)


def trap_top_half(q=None):
    """后领带顶边半宽 M.x（梯形上底的一半）。"""
    q = q or params()
    x_cut, _L, _n = _neck(q)
    return x_cut - _k_miter(q) * q["COLLAR_W"]


def collar_w_limit(q=None):
    """带宽上限：顶边半宽 > 0 ⇒ COLLAR_W < x_cut / k（本案开领宽 160 时 ≈88.1）。"""
    q = q or params()
    x_cut, _L, _n = _neck(q)
    return x_cut / _k_miter(q)


# 领子的几何关系（用户 2026-11-09「领子几何关系错误，重看直领交襟」后重推）：
#   V1 的领条是一条**直的整带**，成型后呈倒 U：左前襟 → 绕后颈 → 右前襟。
#   · 前襟那两段的长度 ＝ 前片内边长 ＝ 弦 |PQ| ＝ √(x_cut² + L²)；
#   · 绕后颈那一段的长度 ＝ 开领宽（＝两条前襟边在肩线处的间距），
#     折起来立起的那个梯形是**带子的宽度**立起来，不额外吃长度：
#     立起高 NECK_H ≡ 带宽 COLLAR_W；顶边由 miter 得出（trap_top_half），不再是 V1 的 89。
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


# ── 第 2 步：开领（内边 ＝ 弦 P→Q）──────────────────────────────────
def open_neck_cmds(cmds, x_cut):
    """开领（用户 2026-11-18 令）：前片内边 ＝ **弦 P→Q**。

        P ＝ 领口点 (x_cut, L)：开领边与前片顶边（肩线 y=L）的交点
        Q ＝ 下摆曲线 ∩ 中缝：模板下摆曲线的起点 (0, 0)
        |PQ| ＝ √(x_cut² + L²)  ＝ 前襟边长

    等价说法：前片 ＝ 后片半 − △(Q, (0,L), P)；面积差 ＝ x_cut·L/2（本案 80×825/2 ＝ 33000）。
    下摆曲线**整条保留**（不再在 x=x_cut 处截断），cmds 仍只有 M/C/L/Z；
    收边用 Z 画弦 P→Q，不另加折线。

    依赖后片半的 cmds 次序：M (0,0) / C 下摆 / L / C / C / C / L / C / L / L / L (0,L) / Z。
    """
    assert cmds[0][0] == "M" and cmds[1][0] == "C", "后片半的 cmds 结构与预期不符"

    y_top = float(cmds[-2][1][1])
    P = (float(x_cut), y_top)
    Q = (float(cmds[0][1][0]), float(cmds[0][1][1]))

    out = [["M", [Q[0], Q[1]]], ["C"] + [list(q) for q in cmds[1][1:]]]   # 下摆曲线整条
    for seg in cmds[2:-2]:                      # 腋圆角 → 袖口 → 肩点 → (95, L)
        out.append([seg[0]] + [list(q) for q in seg[1:]])
    out.append(["L", [P[0], P[1]]])
    out.append(["Z"])                           # 收边 ＝ 弦 P→Q
    return out, dict(P=P, Q=Q, low=Q, top=P)


def neck_pts(q=None):
    """(P, Q)：P＝领口点 (x_cut, L)，Q＝下摆曲线∩中缝 (0, 0)。"""
    q = q or params()
    _cmds, pts = open_neck_cmds(tpl_piece("后片半")["cmds"], slit_half(q))
    return pts["P"], pts["Q"]


def neck_cut_len(q=None):
    """前襟边长 ＝ |PQ|（P＝领口点 (x_cut, L)，Q＝下摆 ∩ 中缝 (0, 0)）。"""
    q = q or params()
    cmds, pts = open_neck_cmds(tpl_piece("后片半")["cmds"], slit_half(q))
    return math.hypot(pts["P"][0] - pts["Q"][0], pts["P"][1] - pts["Q"][1])


def collar_length(q=None):
    """领条长 ＝ 2 × 前襟（剪口边长） ＋ 后领段（＝开领宽）。见文件头那段推导。"""
    q = q or params()
    return 2.0 * neck_cut_len(q) + q["NECK_W"]


def collar_piece(q=None):
    """领条 ×1：长＝2×前襟＋开领宽，宽＝COLLAR_W；直丝沿长。

    两条 notch 标出后领段的两端（＝两条前襟边落在带子上的位置）。
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
    # 模板原刀口全留：中缝 (0,0) 正是 Q＝弦的下端（片子的一个角），不是被切掉的边
    front["notches"] = [list(n) for n in (front.get("notches") or [])]
    front["notches"].append([x_cut, neck_pts["P"][1]])          # P ＝ 领口点

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
            if step == 2:
                Qp = tuple(p["cmds"][0][1])                 # Q ＝ 下摆 ∩ 中缝
                Pp = tuple(p["cmds"][-2][1])                # P ＝ 领口点
                dims = [("L", [Qp[0], Qp[1]], [Pp[0], Pp[1]],
                         "前襟 %.0f" % neck_cut_len(q))]
                note = "内边＝弦 P→Q（P 领口点 x=%.0f，Q 下摆∩中缝），开领宽 %.0f" % (
                    x_cut, q["NECK_W"])
            else:
                dims = [("L", [x0, y0], [x0, y1], "前襟 %.0f" % h)]
                note = "＝后片复制，几何相同"
        else:
            dims = [("L", [x0, y0], [x0, y1], "后中长 %.0f" % h)]
            note = "模板后片半原样"
        out.append(dict(name=nm, qty=p["qty"], cmds=p["cmds"],
                        grain=list(p.get("grain") or [0, 1]),
                        notches=[list(n) for n in (p.get("notches") or [])],
                        marks=[], dims=dims, note=note))
    return out
