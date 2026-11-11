# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 前片几何（逐步构建）

底：**厂商基准**（hanfu-cad 的 vendor profile，男 M）**模板原衣长 L=770**。
    「衣长缩短 5cm」的改动已撤销，L 不再覆盖。由 `hanfu-cad/pattern/build.py`
    按 sizing.params(男, M, vendor) 原参数生成，结果冻结在本目录
    `_base_vendor_L770.pieces.json`，**只读**。
    **不再使用文物基准**（artifact：衣长 825 / 肩点 560 / 领缘 40 / 门襟偏 9.3°）。

坐标：服饰坐标，x 向右、y 向上，原点 = 后中缝 ∩ 下摆中心。单位 mm。

第 1 步：解析构造 P1、P2（a、b 待定，不从截图量）。
第 2 步：赋值 VP1 = VP2 = 5cm = 50mm ⇒ a = b = 50。
第 3 步：连接 P1P2 作为「新领口」；前片左右镜像同步，按前片 + 后片出平铺线稿（为第 4 步备图）。
         **2026-11-11 11:48 修正**：P1P2 改为**圆心角 60°** 的解析圆弧（P₁/P₂ 端点不动、
         弦长不变 ⇒ R = 弦长 = 76.5732mm，圆心由弦解析确定、取凹向下摆一支）。
第 4 步：上领子；领子＝等高 30mm 连续竖起，A 在 P₁ 右上方；
         **2026-11-11 11:48 修正**：上领缘采用**直线折线** B→A→A′→B′（撤销三段圆弧），
         下缘＝第 3 步 60° 弧。
第 5 步：领子按衣片分三块（①左襟 / ②后片 / ③右襟＝左襟镜像），
         边缘曲线用出图脚本的三次贝塞尔 C，面积＝格林线积分。
第 6 步：根据共边把领条做成**一条带状**——三段沿共边 P₁A / P₁′A′ 翻折展开相接，
         两端 P₂B / P₂′B′ 分开、**首尾不接**，展开后不自交。
         定稿落成模板 `pattern/_tpl.pieces.json`（由 `pattern/save_template.py` 生成）。

注意（模板本身的不平行，未自行修正）：build.py 的 grain 硬编码 9.3° 方向
（那是文物基准 L=825 的门襟偏角），而门襟边方向由 (LAP_DX, L) 决定；
厂商基准 L=770 时 θ=9.9443°，两者仍不平行，见 GRAIN_CROSS。
"""
import json
import math
import os

import sheet   # 出图脚本：复用 sample() 的贝塞尔采样做面积数值交叉验证（不修改它）

HERE = os.path.dirname(os.path.abspath(__file__))
TPL_PATH = os.path.join(HERE, "_base_vendor_L770.pieces.json")
TPL = json.load(open(TPL_PATH, encoding="utf-8"))

# ---- 口径 ----
PROFILE = "vendor"      # 厂商基准（不是 artifact 文物基准）
SIZE = "M"              # 厂商表为男装，默认中码
L_VENDOR = 770.0        # 厂商基准 M 模板原衣长（衣长改动已撤销）


def front_piece():
    """只读地取模板前片（深拷贝，绝不写回模板）"""
    for p in TPL["pieces"]:
        if p["name"] == "前片":
            return json.loads(json.dumps(p))
    raise KeyError("模板里没有「前片」")


def back_piece():
    """只读地取模板「后片半」（深拷贝，绝不写回模板）"""
    for p in TPL["pieces"]:
        if p["name"] == "后片半":
            return json.loads(json.dumps(p))
    raise KeyError("模板里没有「后片半」")


_FRONT = front_piece()
_BACK = back_piece()
_P = TPL["params"]

# ---- 已知量（全部来自模板参数，没有一个是量图量来的） ----
L        = _P["L"]            # 770  衣长（模板原值）= 顶边 y
LAP_DX   = _P["OV"] / 2.0    # 135  门襟边越中量
X_SHLD   = _P["X_SHLD"]      # 285  肩点（顶边左端 |x|）
NECK     = _P["NECK"]        # 190  本步不用，留档
OV       = _P["OV"]          # 270  交叠


def _unit(v):
    n = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / n, v[1] / n)


# ---- 三个顶点：顶边（肩线）两端 + 门襟边下端 ----
V = (0.0, L)                  # 顶边右端 = 门襟边上端 = 前中缝顶点
S = (-X_SHLD, L)              # 肩点，顶边左端
H = (LAP_DX, 0.0)            # 门襟边下端（越中 LAP_DX）

# ---- 两条边的方程（P1、P2 各自所在的直线） ----
E_TOP = (-1.0, 0.0)                          # 顶边单位方向：V → S
U_LAP = _unit((H[0] - V[0], H[1] - V[1]))   # 门襟边单位方向：V → H
LEN_TOP = math.dist(V, S)                     # 285
LEN_LAP = math.dist(V, H)                     # √(770²+135²) = 781.74…
THETA   = math.degrees(math.atan2(LAP_DX, L))    # 9.9443°
ANGLE_V = 90.0 + THETA                       # 顶边与门襟边在 V 处夹角 = 99.9443°

# 模板布纹：build.py 硬编码的 9.3° 方向，与厂商基准门襟边不平行。
GRAIN = tuple(_FRONT["grain"])
GRAIN_CROSS = GRAIN[0] * U_LAP[1] - GRAIN[1] * U_LAP[0]


# ---- 第 1 步：P1、P2 的解析构造 ----
#   P1(a) = V + a·E_TOP ,  a ∈ [0, LEN_TOP] ,  a 待定
#   P2(b) = V + b·U_LAP ,  b ∈ [0, LEN_LAP] ,  b 待定
def P1(a):
    return (V[0] + a * E_TOP[0], V[1] + a * E_TOP[1])


def P2(b):
    return (V[0] + b * U_LAP[0], V[1] + b * U_LAP[1])


def _cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def line_param(p0, d0, p1, d1):
    """解析求交：直线 p0+s·d0 与 p1+t·d1 → (s, t)；平行/重合返回 None。
    纯 2×2 线性方程组（克拉默法则），不做数值搜索、不量图。"""
    den = _cross(d0, d1)
    if abs(den) < 1e-12:
        return None
    w = (p1[0] - p0[0], p1[1] - p0[1])
    return (_cross(w, d1) / den, _cross(w, d0) / den)


def construct_from_neckline(Q, d):
    """构造法则（第 1 步只定义，不调用）：
    后续一旦给定领口线 ℓ（过 Q、方向 d），
        P1 = ℓ ∩ 顶边   → a
        P2 = ℓ ∩ 门襟边 → b
    两点随即由解析求交唯一确定，不需要任何量图。"""
    r1 = line_param(V, E_TOP, Q, d)
    r2 = line_param(V, U_LAP, Q, d)
    if r1 is None or r2 is None:
        return None
    return dict(a=r1[0], b=r2[0], P1=P1(r1[0]), P2=P2(r2[0]))


# ---- 第 1 步数据：符号点，value 一律 null ----
def step1_data():
    return {
        "step": 1,
        "scope": "02 前片 ×2（只做前片）",
        "basis": {
            "profile": PROFILE, "size": SIZE,
            "L_vendor": L_VENDOR, "L": L,
            "template": os.path.basename(TPL_PATH),
            "note": "厂商基准男 M 模板原衣长 770；衣长缩短 5cm 的改动已撤销，L 未覆盖；由 build.py 生成",
            "readonly": True, "geometry_changed": False,
        },
        "vertices": {
            "V": {"xy": list(V), "meaning": "顶边右端 = 门襟边上端 = 前中缝顶点"},
            "S": {"xy": list(S), "meaning": "肩点，顶边左端"},
            "H": {"xy": list(H), "meaning": "门襟边下端（越中 LAP_DX）"},
        },
        "edges": {
            "top": {"from": list(V), "to": list(S), "unit_dir": list(E_TOP),
                    "length": LEN_TOP,
                    "equation": "y = L = %.0f, x ∈ [%.0f, 0]" % (L, -LEN_TOP)},
            "lap": {"from": list(V), "to": list(H), "unit_dir": list(U_LAP),
                    "length": LEN_LAP,
                    "equation": "P = V + b·(%.0f,−%.0f)/%.4f, b ∈ [0, %.2f]"
                                % (LAP_DX, L, LEN_LAP, LEN_LAP)},
        },
        "derived": {
            "theta_deg": THETA,
            "theta_note": "atan(LAP_DX/L)；标称 9.3° 是文物基准 L=825 的门襟偏角，也是 build.py 硬编码的 grain 方向",
            "angle_at_V_deg": ANGLE_V,
            "grain": list(GRAIN),
            "grain_cross_with_lap": GRAIN_CROSS,
            "grain_parallel_to_lap": abs(GRAIN_CROSS) < 1e-3,
            "grain_note": "布纹仍是 build.py 硬编码的 9.3° 方向，与厂商基准 L=770 的门襟边不平行；未自行修正",
        },
        "points": {
            "P1": {"on": "顶边（肩线）", "expr": "V + a·(-1, 0)",
                   "param": "a", "range": [0.0, LEN_TOP],
                   "value": None, "status": "待定：本步不赋值"},
            "P2": {"on": "门襟边", "expr": "V + b·u_lap",
                   "param": "b", "range": [0.0, LEN_LAP],
                   "value": None, "status": "待定：本步不赋值"},
        },
        "construction": {
            "rule": "给定领口线 ℓ: X = Q + s·d，"
                    "P1 = ℓ∩顶边、P2 = ℓ∩门襟边，由 2×2 线性方程组解析求交",
            "function": "geo.construct_from_neckline(Q, d)",
            "optional_constraint": "若后续要求 |VP1| = |VP2| = r，则 a = b = r（单参数），本步不预设",
        },
        "note": "位置不从截图量；a、b 未赋值。图上的空心点是示意占位，非定量。",
    }


# ---- 片表：前片几何原样，只加标记供出图 ----
def sheet_pieces():
    """给 sheet.write_sheet 的片表。cmds 直接搬模板，一处不改。"""
    p = front_piece()
    p["marks"] = [[list(V), list(S)], [list(V), list(H)]]
    p["aux"] = []
    for q in (V, S, H):
        p["aux"] += [[(q[0] - 12, q[1]), (q[0] + 12, q[1])],
                     [(q[0], q[1] - 12), (q[0], q[1] + 12)]]
    demo_a = LEN_TOP * 0.5
    demo_b = LEN_LAP * 0.5
    p["points"] = [
        (P1(demo_a)[0], P1(demo_a)[1], "P₁ (a 待定)"),
        (P2(demo_b)[0], P2(demo_b)[1], "P₂ (b 待定)"),
        (V[0], V[1], "V"),
        (S[0], S[1], "S"),
        (H[0], H[1], "H"),
    ]
    p["dims"] = [
        ("top", list(V), list(S), "a ∈ [0, %.0f]" % LEN_TOP),
        ("lap", list(V), list(H), "b ∈ [0, %.0f]" % LEN_LAP),
    ]
    p["note"] = ""
    return [p], dict(demo_a=demo_a, demo_b=demo_b)


# ---- 第 2 步（用户 2026-11-10 20:33 令）：VP1 = VP2 = 5cm，给 a、b 赋值 ----
# 5cm = 50mm。E_TOP 与 U_LAP 都是单位向量，所以参数 a、b 本身就是 V→P 的距离：
#   |VP1| = a, |VP2| = b  ⇒  等距约束直接给出 a = b = 50，不需要解方程。
# 第 1 步的参数化定义与「待定」状态保持不变，本步只是代入取值。
R_EQUAL = 50.0   # mm = 5cm


def points_resolved(r=R_EQUAL):
    """把等距约束代入第 1 步的参数化定义，得到两点的确定坐标。
    这是第 2 步唯一的新事实；P1(a)/P2(b) 的定义本身一个字都没改。"""
    return dict(a=r, b=r, P1=P1(r), P2=P2(r),
                constraint="VP1 = VP2 = 5cm = 50mm",
                implies="a = b = 50")


def sheet_pieces_step2():
    """第 2 步片表：前片几何仍原样，只把 P1/P2 落在确定位置并标注 50mm。
    两点都在 V 附近（50mm 相对 685mm 片宽约 7%），标签用自定义偏移错开。"""
    p = front_piece()
    p["marks"] = [[list(V), list(S)], [list(V), list(H)]]
    p["aux"] = []
    for q in (V, S, H):
        p["aux"] += [[(q[0] - 12, q[1]), (q[0] + 12, q[1])],
                     [(q[0], q[1] - 12), (q[0], q[1] + 12)]]
    r = points_resolved()
    p["points"] = [
        (r["P1"][0], r["P1"][1], "P₁ · VP₁=50mm", -300, -36),
        (r["P2"][0], r["P2"][1], "P₂ · VP₂=50mm", 36, 70),
        (V[0], V[1], "V", 22, -44),
        (S[0], S[1], "S", 0, 44),      # 放到顶边下方，避开 P₁ 的长标签
        (H[0], H[1], "H", 20, -20),
    ]
    p["dims"] = []
    p["note"] = ""
    return [p]


# ---- 第 3 步（用户 2026-11-10 令）：连接 P1P2 作为「新领口」，前片左右镜像同步 ----
# **2026-11-11 11:48 修正**：P₁P₂ 改为**圆心角 60°** 的解析圆弧（用户令）。
#   端点 P₁/P₂ 不动（第 2 步 a=b=50 未改）⇒ 弦长 c=76.5732 不变；
#   c = 2R·sin30° = R ⇒ **R = c = 76.5732mm**（不再是 VP₁=50），弧长 = R·π/3 = 80.1873。
#   圆心在弦中垂线上，由弦心距 d=R·cos30° 解析确定；取「弧中点 y 较小」的一支
#   ＝**凹向下摆**（承 23:23 口径）。左片圆心 = 右片关于 x=0 镜像，两段**不共圆**、
#   在中缝 x=0 相交于 y≈722.8002（几何必然，非 bug）。
# 「前片左右镜像同步」：前片 ×2 是关于前中缝 x=0 的左右镜像两片，
# 新领口在两片上各有一条（P₁→P₂ 与 P₁′→P₂′）。左右镜像同步、旧边虚线标注均不变；
# 裁片 cmds 一处未改。采样折线只是出图离散化，不是新增控制点。
def mirror_x(p):
    """关于前中缝 x=0 镜像（左右片同步用）"""
    return (-p[0], p[1])


def mirror_cmds(cmds):
    """把整条 cmds 路径关于 x=0 镜像（M/L/C/Q 的 x 全取负，Z 保留）"""
    out = []
    for c in cmds:
        k = c[0]
        if k == "Z":
            out.append(["Z"])
        elif k in ("M", "L"):
            out.append([k, [-c[1][0], c[1][1]]])
        elif k == "C":
            out.append(["C", [-c[1][0], c[1][1]], [-c[2][0], c[2][1]],
                        [-c[3][0], c[3][1]]])
        elif k == "Q":
            out.append(["Q", [-c[1][0], c[1][1]], [-c[2][0], c[2][1]]])
    return out


# ---- 第 3 步修正（用户 2026-11-11 11:48 令）：P₁P₂ 改为「圆心角 60°」的圆弧 ----
# 「P1P2 为圆心角 60 度的弧」⇒ 端点 P₁/P₂ 不动（第 2 步 a=b=50 未改），弦长 c 不变；
#   由 c = 2R·sin(60°/2) = R（sin30°=1/2）⇒ **R = c = 76.5732mm**，不再是 VP₁=50。
#   弦心距 d = R·cos30° = 66.3143mm；矢高 = R−d = 10.2589mm；弧长 = R·π/3 = 80.1873mm。
#   两个候选圆心在弦中垂线上 M ± d·n；取「弧中点 y 较小」的一支 ⇒ **凹向下摆**
#   （承第 3 步 23:23 口径），圆心 C=(21.967982, 796.154590)。
#   左片圆心 = 右片关于 x=0 镜像 (-21.967982, 796.154590)，两段弧**不共圆**，
#   在中缝 x=0 处相交于 y≈722.8002（几何必然，非 bug）。
#   右片极角 −160.027853° → −100.027853°，扫角精确 60°；左片镜像、扫角 −60°。
#   采样折线只是出图离散化，不是新增控制点；裁片 cmds 一处未改。
ARC_SWEEP_DEG = 60.0
ARC_SAMPLES = 64


def _arc_geometry():
    """由「端点 P₁/P₂ + 圆心角 60°」解析出圆心/半径/极角。纯公式，不量图。"""
    r = points_resolved()
    p0, p1 = tuple(r["P1"]), tuple(r["P2"])
    c = math.dist(p0, p1)
    half = math.radians(ARC_SWEEP_DEG / 2.0)
    R = c / (2.0 * math.sin(half))          # 60° ⇒ R = c
    d = R * math.cos(half)                  # 弦心距
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    M = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    n = (-dy / c, dx / c)
    cands = [(M[0] + d * n[0], M[1] + d * n[1]),
             (M[0] - d * n[0], M[1] - d * n[1])]

    def apex(C):
        return (C[0] + (R / d) * (M[0] - C[0]),
                C[1] + (R / d) * (M[1] - C[1]))

    # 凹向下摆 ⇒ 弧中点在弦下方（y 较小）
    C = min(cands, key=lambda q: apex(q)[1])
    a0 = math.atan2(p0[1] - C[1], p0[0] - C[0])
    a1 = math.atan2(p1[1] - C[1], p1[0] - C[0])
    da = (a1 - a0 + math.pi) % (2.0 * math.pi) - math.pi   # 劣弧（60°）
    return dict(P1=list(p0), P2=list(p1), chord=c, R=R, chord_dist=d,
                center=list(C), apex=list(apex(C)),
                start_deg=math.degrees(a0), end_deg=math.degrees(a1),
                sweep_deg=math.degrees(da),
                arc_length=R * abs(da), sagitta=R - d,
                midpoint=list(M), normal=list(n))


_ARC = _arc_geometry()
ARC_R = _ARC["R"]
ARC_CENTER = tuple(_ARC["center"])
ARC_CHORD_DIST = _ARC["chord_dist"]
ARC_SAGITTA = _ARC["sagitta"]
ARC_LENGTH = _ARC["arc_length"]
ARC_START_DEG = _ARC["start_deg"]
ARC_END_DEG = _ARC["end_deg"]
ARC_SWEEP = _ARC["sweep_deg"]


def arc_polyline(n=ARC_SAMPLES):
    """右片新领口圆弧的解析采样点列 P₁ → P₂（圆心 ARC_CENTER、R=ARC_R、凹向下摆）。
    极角从 ARC_START_DEG 扫 60°；只是等角离散化供出图，不引入任何新控制点。
    首末点直接取解析端点 P₁/P₂，避免 cos/sin 的浮点尾差。"""
    a0 = math.radians(ARC_START_DEG)
    da = math.radians(ARC_SWEEP)
    pts = [[ARC_CENTER[0] + ARC_R * math.cos(a0 + da * i / n),
            ARC_CENTER[1] + ARC_R * math.sin(a0 + da * i / n)]
           for i in range(n + 1)]
    pts[0] = list(_ARC["P1"])
    pts[-1] = list(_ARC["P2"])
    return pts


def segment_p1p2():
    """右片新领口：圆心角 60° 的解析圆弧（P₁→P₂，凹向下摆）。
    length/chord = 两点直线距离（弦长）；samples 是出图采样折线，不是几何控制点。"""
    a, b = _ARC["P1"], _ARC["P2"]
    return dict(
        shape="圆弧（用户 2026-11-11 11:48 令：P1P2 为圆心角 60° 的弧；凹向下摆）",
        P1=list(a), P2=list(b),
        length=_ARC["chord"], chord=_ARC["chord"],
        radius=ARC_R, center=list(ARC_CENTER),
        sweep_deg=ARC_SWEEP, start_deg=ARC_START_DEG, end_deg=ARC_END_DEG,
        arc_length=ARC_LENGTH, sagitta=ARC_SAGITTA,
        chord_dist=ARC_CHORD_DIST, apex=list(_ARC["apex"]),
        sagitta_dir="向下摆（圆心在弦右上，弧向左下鼓）",
        unit_dir=list(_unit((b[0] - a[0], b[1] - a[1]))),
        midpoint=list(_ARC["midpoint"]),
        samples=arc_polyline(),
    )


def segment_p1p2_pair():
    """左右镜像同步的两条 60° 圆弧。左片 = 右片关于 x=0 的镜像：
    圆心也要镜像（不再共圆心），半径/弧长/矢高完全相同，没有独立新参数。"""
    right = segment_p1p2()
    left = dict(right)
    left["P1"] = list(mirror_x(tuple(right["P1"])))
    left["P2"] = list(mirror_x(tuple(right["P2"])))
    left["center"] = list(mirror_x(tuple(right["center"])))
    left["apex"] = list(mirror_x(tuple(right["apex"])))
    left["midpoint"] = list(mirror_x(tuple(right["midpoint"])))
    left["unit_dir"] = [-right["unit_dir"][0], right["unit_dir"][1]]
    left["start_deg"] = -right["start_deg"]
    left["end_deg"] = -right["end_deg"]
    left["sweep_deg"] = -right["sweep_deg"]
    left["samples"] = [list(mirror_x(tuple(q))) for q in right["samples"]]
    return dict(right=right, left=left)


def sheet_pieces_step3():
    """第 3 步片表：前片左右两片（镜像同步），各带一条新领口**圆弧**（采样折线）。
    左片只对右片做镜像变换，没有新增几何；两片 qty 各 1（合计模板的 ×2）。"""
    pair = segment_p1p2_pair()

    def one(side, seg, flip):
        p = front_piece()
        p["name"] = "前片（%s）" % side
        p["qty"] = 1
        if flip:
            p["cmds"] = mirror_cmds(p["cmds"])
            p["grain"] = [-p["grain"][0], p["grain"][1]]
            p["notches"] = [[-n[0], n[1]] for n in p["notches"]]
        marks = [[list(V), list(S)], [list(V), list(H)]]
        aux = []
        for q in (V, S, H):
            aux += [[(q[0] - 12, q[1]), (q[0] + 12, q[1])],
                    [(q[0], q[1] - 12), (q[0], q[1] + 12)]]
        if flip:
            marks = [[list(mirror_x(q)) for q in m] for m in marks]
            aux = [[list(mirror_x(q)) for q in m] for m in aux]
        p["marks"] = [[list(q) for q in m] for m in marks]
        p["aux"] = [[list(q) for q in m] for m in aux]
        # 新领口＝解析圆弧的采样折线（LINK 图层支持多点）。首末点仍是 P₁/P₂，不延长。
        p["links"] = [seg["samples"]]
        # 旧边 V→P₁ / V→P₂（镜像片 V→P₁′ / V→P₂′）改为虚线标注（用户 2026-11-10 令）。
        # 只声明画法：cmds 与模板逐项相同，几何未改；新领口仍是实线圆弧。
        vv = V if not flip else mirror_x(V)
        p["dashed"] = [[list(vv), list(seg["P2"])],      # 门襟边开头 50mm
                       [list(seg["P1"]), list(vv)]]      # 顶边末尾 50mm
        P1, P2 = seg["P1"], seg["P2"]
        vx, vy = V if not flip else mirror_x(V)
        sx, sy = S if not flip else mirror_x(S)
        hx, hy = H if not flip else mirror_x(H)
        # P₁/V 标签抬到顶边上方 100mm：片名（LABEL 图层）在点标签之后绘制，
        # 镜像片片名较长，若标签停在 −40 会被片名盖住。
        p["points"] = [
            (P1[0], P1[1], "P₁" if not flip else "P₁′", -96 if not flip else 24, -100),
            (P2[0], P2[1], "P₂" if not flip else "P₂′", 40 if not flip else -118, 62),
            (vx, vy, "V", 22, -104),
            (sx, sy, "S" if not flip else "S′", 0, 44),
            (hx, hy, "H" if not flip else "H′", 20, -20),
        ]
        p["dims"] = []
        p["note"] = ""
        return p

    return [one("右", pair["right"], False), one("左·镜像", pair["left"], True)]


# ---- 第 4 步（22:15–22:19 令；2026-11-11 11:48 修正）：上领子 ----
# 口径：
#   ① P₁A 为领高，暂取 3cm = 30mm（可调）；
#   ② B 在「直线」HP₂ 上，**不是线段** H→P₂；
#   ③ 领子带子：起点边 P₂B，经过 P₁A，终点边 P₂′B′；
#   ④ 左右镜像同步；
#   ⑤ **2026-11-11 11:48 用户修正**：「P1P2 为圆心角 60 度的弧，A 依然右上角，上领缘采用直线」
#        · 第 3 步新领口改为圆心角 60° 的解析圆弧（端点 P₁/P₂ 不动、R=弦长=76.5732mm）；
#        · A 仍在 P₁ 右上方，四个端点 A/B/A′/B′ 与四条 30mm 宽度边全部不动；
#        · **上领缘采用直线**（撤销 01:13 的三段圆弧）：B→A→A′→B′ 为三段直线折线；
#        · 领子下缘＝第 3 步 60° 弧（红线复用，不重复描）。
#   ⑥ 参考图（ref/ 三张实物照，11:42 归档）：领子为等宽、边缘以直线段为主的竖起带；
#      本步只按用户给的解析指令落地，**不从照片量取任何数值**。
# 解析推导（不量图）：
#   w = −U_LAP；mirror(w) 向上偏右 9.944294°；
#   B  = P₂ + h·w         = V + 20u = (3.453812, 750.300478)
#   A  = P₁ + h·mirror(w) = (−44.819281, 799.549284)   ← P₁ 右上方
#   A′ = mirror_x(A)、B′ = mirror_x(B)；A—A′ = 89.638562mm；A/A′ 在顶边之上 29.549284mm。
COLLAR_H = 30.0


def collar_dir():
    """领高方向 w = −U_LAP（沿门襟边直线指向 V，向上偏左 9.944294°）。
    由「B 在直线 HP₂ 上」唯一确定：P₂B ∥ w。"""
    return (-U_LAP[0], -U_LAP[1])


def collar_dir_A():
    """P₁A 的方向 = mirror_x(w)（向上偏右 9.944294°）＝用户「A 在 P₁ 右上方」。
    左右镜像同步下唯一不引入新参数的解析方向：A′ = mirror_x(A) ⇒ P₁′A′ ∥ w。"""
    return mirror_x(collar_dir())


def collar_points(h=COLLAR_H):
    """领子连续条带（左右镜像同步）——**上领缘直线折线 · A 在 P₁ 右上方**。

    第 3 步新领口（圆心角 60° 的解析圆弧、凹向下摆）＝领子下缘，出图复用红线、不重复描；
    11:48 令「上领缘采用直线」⇒ 上缘 B→A→A′→B′ 为三段直线折线（不是圆弧）；
    四个端点 A/B/A′/B′、四条 30mm 宽度边全部不动 ⇒ 竖起 29.55mm、
    A 在 P₁ 右上方、B 在直线 HP₂ 上全部保住。裁片 cmds 一字未改；未推断第 5 步。
    """
    r = points_resolved()
    P1, P2 = tuple(r["P1"]), tuple(r["P2"])
    P1p, P2p = mirror_x(P1), mirror_x(P2)
    w, wA = collar_dir(), collar_dir_A()

    def up(q, d):
        return (q[0] + h * d[0], q[1] + h * d[1])

    B = up(P2, w)               # 仍在直线 HP₂ 上，P₂ 之上
    A = up(P1, wA)              # P₁ 右上方（用户令）
    Ap, Bp = mirror_x(A), mirror_x(B)
    lower = [P2, P1, P1p, P2p]
    upper = [B, A, Ap, Bp]                 # 上领缘＝直线折线（4 端点）
    pair = segment_p1p2_pair()
    r_arc = [tuple(q) for q in pair["right"]["samples"]]
    l_arc = [tuple(q) for q in pair["left"]["samples"]]
    lower_path = list(reversed(r_arc)) + [P1p] + l_arc[1:]
    upper_path = [list(q) for q in upper]   # 直线折线（无中间采样点）

    return dict(
        h=h,
        mode="上领缘直线折线 · A 在 P₁ 右上方（P₁P₂ 圆心角 60° 弧）", concentric=False,
        dir=list(w), dir_A=list(wA), dir_left=list(mirror_x(w)),
        lower=[list(q) for q in lower],
        upper=[list(q) for q in upper],
        lower_path=[list(q) for q in lower_path],
        upper_path=upper_path,
        outline=[list(q) for q in (lower + list(reversed(upper)))],
        P1=list(P1), P2=list(P2), P1p=list(P1p), P2p=list(P2p),
        A=list(A), B=list(B), Ap=list(Ap), Bp=list(Bp),
        width_edges=[[list(a), list(b)] for a, b in
                     [(P2, B), (P1, A), (P1p, Ap), (P2p, Bp)]],
        width_edge_dirs=[list(w), list(wA), list(w), list(mirror_x(w))],
        inner_edges=[[list(P1), list(A)], [list(P1p), list(Ap)]],
        rise_above_top=A[1] - V[1],
        AA=Ap[0] - A[0],
        arc=dict(
            mode="第 3 步 P₁P₂＝圆心角 60° 的解析圆弧（凹向下摆）作为下缘；上领缘＝直线折线",
            neckline_sweep_deg=pair["right"]["sweep_deg"],
            neckline_radius=pair["right"]["radius"],
            neckline_center=pair["right"]["center"],
            neckline_arc_length=pair["right"]["arc_length"],
            neckline_chord=pair["right"]["chord"],
            neckline_sagitta=pair["right"]["sagitta"],
            lower="下缘 = 第 3 步两条 60° 圆弧（圆心互为镜像）+ 顶边中段直线；出图复用红线，不重复描",
            upper="上缘 = 直线折线 B→A→A′→B′（11:48 令「上领缘采用直线」）；四个端点全不动",
            width_edges="四条宽度边各 30mm：P₂B ∥ w、P₁A ∥ mirror(w)、P₁′A′ ∥ w、P₂′B′ ∥ mirror(w)",
            sync="左右镜像同步；四个端点与四条宽度边未改；裁片 cmds 未改",
        ),
    )


# ---- 第 5 步（用户 2026-11-11 14:24 / 14:35 修正令）：领子按衣片分三块，各自积分面积 ----
# 用户令（原文）：「算出前片左襟领子形状，边缘曲线，积分得到面积，
#                 算出后片领子形状，边缘曲线，积分得到面积，
#                 右襟前片由左襟镜像得到」
#            「用贝塞尔近似，出图用什么你就用什么」
# 明确否定：等宽直条领条（12:29 旧版）、立裁法向贴附（绿色对比图）、
#           前中交叠量 / 将军饮马反射展开（14:24 前一轮探查方向）、
#           把弧边退化成采样折线（14:35 纠正）。
# 硬口径：「这不是立裁，这是平裁」「上身立起，平铺平面」
#        ⇒ 领条是**平面区域**，没有三维曲面 / 法向偏移 / 可展性假设。
#
# 分块：第 4 步那条「一条连续竖起」领子，按 inner_edges（P₁A / P₁′A′）分成三块平面区域：
#   ① 前片左襟领子（基准，未镜像）：下缘＝右 60° 弧 P₂→P₁；上缘＝直线 A→B；
#      宽度边＝P₁A；端头＝B→P₂
#   ② 后片领子：下缘＝后颈直线 P₁→P₁′；上缘＝直线 A′→A；宽度边＝P₁′A′、A→P₁
#      ⇒ 梯形（上窄下宽）
#   ③ 前片右襟领子 ＝ ① 关于 x=0 镜像（mirror_cmds 已支持 C 的 x 取负）
#   三块沿 P₁A / P₁′A′ 共边拼接＝第 4 步一条连续竖起领子；穿着时左右襟在前中
#   交叠（空间遮挡折叠），平铺裁片各自独立，不扣减交叠（用户「关键不是交叠量」）。
#
# 边缘曲线的数学定义（用户 14:35 令）：
#   60° 圆弧 → **三次贝塞尔 C**（sheet.py 的 path_d / sample / mirror_cmds 原生支持 C；
#   模板前片、后片半各带 5 条 C）。控制点由解析式 k=4/3·tan(Δθ/4) + 旋转 θa 得到，
#   端点精确落在 P₁/P₂。裁片轮廓 cmds 只含 M / L / C / Z，**不用采样折线**。
#   直线边 → L。
#
# 面积＝½ ∮(x dy − y dx)（格林公式线积分），对**这套 cmds 曲线**精确解析积分：
#   直线段 ∫ = x_a·y_b − x_b·y_a
#   三次贝塞尔段：P(t)=Σ a_i t^i（幂基），
#     ∫₀¹(x y′ − y x′)dt = Σ_{i=0..3} Σ_{j=1..3} (a_xi·a_yj − a_yi·a_xj)·j/(i+j)
#   另用 sheet.sample(cmds, 4096) 的点列做鞋带公式独立数值交叉验证。
#   积分、出图、裁片三者统一到同一套贝塞尔曲线，不再各说各话。
COLLAR_STRIP_NAME = "领条"
COLLAR_REGION_NAMES = ("领条·左襟", "领条·后片", "领条·右襟·镜像")
BEZIER_SAMPLES = 4096          # 仅用于数值交叉验证 / 周长，不是几何控制点


def arc_to_cubic(ta, tb, nseg=1):
    """圆弧（圆心 ARC_CENTER、R=ARC_R、极角 ta→tb）→ nseg 段三次贝塞尔控制点。
    每段扫角 φ=(tb−ta)/nseg，标准系数 k=4/3·tan(φ/4)；端点精确落在解析圆弧上。
    返回 [[P0,P1,P2,P3], ...]（局部单位弧已旋转 θa + 平移圆心）。"""
    C = ARC_CENTER
    out = []
    for s in range(nseg):
        a0 = ta + (tb - ta) * s / nseg
        phi = (tb - ta) / nseg
        k = 4.0 / 3.0 * math.tan(phi / 4.0)
        cp_, sp_ = math.cos(phi), math.sin(phi)
        Q = [(1.0, 0.0), (1.0, k),
             (cp_ + k * sp_, sp_ - k * cp_), (cp_, sp_)]
        ca, sa = math.cos(a0), math.sin(a0)
        out.append([(C[0] + ARC_R * (q[0] * ca - q[1] * sa),
                     C[1] + ARC_R * (q[0] * sa + q[1] * ca)) for q in Q])
    return out


def _bezier_power(ctrl):
    """三次贝塞尔 → 幂基 P(t)=a0+a1·t+a2·t²+a3·t³（x、y 各 4 系数）。"""
    P0, P1, P2, P3 = ctrl
    return [(P0[d],
             3.0 * (P1[d] - P0[d]),
             3.0 * (P0[d] - 2.0 * P1[d] + P2[d]),
             -P0[d] + 3.0 * P1[d] - 3.0 * P2[d] + P3[d]) for d in (0, 1)]


def _bezier_green(ctrl):
    """三次贝塞尔段 ∫(x dy − y dx) 的**精确解析积分**（幂基多项式有限和）。
    x y′ − y x′ = Σ_{i,j}(a_xi·a_yj − a_yi·a_xj)·j·t^(i+j−1)，∫₀¹ = j/(i+j)。"""
    ax, ay = _bezier_power(ctrl)
    I = 0.0
    for i in range(4):
        for j in range(1, 4):
            I += (ax[i] * ay[j] - ay[i] * ax[j]) * j / (i + j)
    return I


def _line_green(a, b):
    """直线段 ∫(x dy − y dx) = x_a·y_b − x_b·y_a（解析精确）。"""
    return a[0] * b[1] - b[0] * a[1]


def _shoelace(pts):
    p = list(pts)
    if p[0] != p[-1]:
        p.append(p[0])
    return 0.5 * abs(sum(p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1]
                         for i in range(len(p) - 1)))


def _bezier_radial_error(ctrl, n=BEZIER_SAMPLES):
    """单段三次贝塞尔近似圆弧的最大径向偏差 | |P(t)−C| − R |（量化「近似」精度）。"""
    P0, P1, P2, P3 = ctrl
    C = ARC_CENTER
    mx = 0.0
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = mt ** 3 * P0[0] + 3 * mt * mt * t * P1[0] + 3 * mt * t * t * P2[0] + t ** 3 * P3[0]
        y = mt ** 3 * P0[1] + 3 * mt * mt * t * P1[1] + 3 * mt * t * t * P2[1] + t ** 3 * P3[1]
        mx = max(mx, abs(math.hypot(x - C[0], y - C[1]) - ARC_R))
    return mx


def collar_regions():
    """第 5 步核心：领子按衣片分三块，各自「形状 + 边缘曲线 + 积分面积」。
    纯解析，不量图、不引入新参数；右襟块严格取左襟块关于 x=0 的镜像。"""
    cp = collar_points()
    P1, P2, P1p, P2p = (tuple(cp[k]) for k in ("P1", "P2", "P1p", "P2p"))
    A, B, Ap = (tuple(cp[k]) for k in ("A", "B", "Ap"))
    ta = math.radians(ARC_END_DEG)      # P₂ 极角
    tb = math.radians(ARC_START_DEG)    # P₁ 极角 ⇒ Δθ = −60°
    cub = arc_to_cubic(ta, tb)[0]

    def L(a, b, name):
        return dict(kind="L", a=a, b=b, name=name)

    def C(ctrl, name):
        return dict(kind="C", ctrl=ctrl, name=name)

    # ① 前片左襟领子（基准）
    e_left = [C(cub, "下缘 右 60° 弧 P₂→P₁（三次贝塞尔）"),
              L(P1, A, "宽度边 P₁A"),
              L(A, B, "上缘 A→B（直线）"),
              L(B, P2, "端头 B→P₂")]
    # ② 后片领子
    e_back = [L(P1, P1p, "下缘 后颈直线 P₁→P₁′"),
              L(P1p, Ap, "宽度边 P₁′A′"),
              L(Ap, A, "上缘 A′→A（直线）"),
              L(A, P1, "宽度边 A→P₁")]

    def mirror_edge(e):
        if e["kind"] == "L":
            return L(mirror_x(e["a"]), mirror_x(e["b"]), e["name"] + "（镜像）")
        return C([mirror_x(q) for q in e["ctrl"]], e["name"] + "（镜像）")

    # ③ 前片右襟领子 ＝ ① 镜像
    e_right = [mirror_edge(e) for e in e_left]

    def green(edges):
        I = 0.0
        for e in edges:
            I += _line_green(e["a"], e["b"]) if e["kind"] == "L" else _bezier_green(e["ctrl"])
        return 0.5 * abs(I)

    def to_cmds(edges, start):
        cmds = [["M", list(start)]]
        for e in edges:
            if e["kind"] == "L":
                cmds.append(["L", list(e["b"])])
            else:
                c = e["ctrl"]
                cmds.append(["C", list(c[1]), list(c[2]), list(c[3])])
        cmds.append(["Z"])
        return cmds

    def edge_desc(e):
        d = dict(kind=e["kind"], name=e["name"])
        if e["kind"] == "L":
            d.update(a=list(e["a"]), b=list(e["b"]),
                     length=math.dist(e["a"], e["b"]), equation="L 直线段（幂基一次）")
        else:
            d.update(ctrl=[list(q) for q in e["ctrl"]],
                     equation="C 三次贝塞尔（k=4/3·tan(Δθ/4)，端点精确）")
        return d

    def build(name, edges, start, role, mirror_of=None):
        cmds = to_cmds(edges, start)
        area = green(edges)
        pts = sheet.sample(cmds, BEZIER_SAMPLES)
        area_num = _shoelace(pts)
        perim = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        return dict(
            name=name, role=role, mirror_of=mirror_of,
            edges=[edge_desc(e) for e in edges],
            cmds=cmds,
            start=list(start),
            perimeter=perim,
            area=area,
            area_numeric=area_num,
            area_diff=area - area_num,
            curve_definition="三次贝塞尔 C + 直线 L；与 sheet.py 出图定义一致（M/L/C/Z）",
        )

    regions = [
        build(COLLAR_REGION_NAMES[0], e_left, P2, "前片左襟领子（基准，未镜像）"),
        build(COLLAR_REGION_NAMES[1], e_back, P1, "后片领子（梯形，上窄下宽）"),
        build(COLLAR_REGION_NAMES[2], e_right, mirror_x(P2),
              "前片右襟领子（＝左襟关于 x=0 镜像）", mirror_of=COLLAR_REGION_NAMES[0]),
    ]
    ci = collar_integral()
    total = sum(r["area"] for r in regions)
    return dict(
        method="领子按衣片分三块平面区域；每块边缘曲线由第 3/4 步解析几何给出；"
               "面积＝½∮(x dy−y dx)（格林公式线积分，贝塞尔段用幂基解析积分）",
        curve="三次贝塞尔 C（k=4/3·tan(Δθ/4)）+ 直线 L；cmds 只含 M/L/C/Z",
        flat_cut=True,
        note="平裁：上身立起是空间遮挡折叠，裁片本身是平面；无三维法向 / 可展性假设",
        arc_approx=dict(
            sweep_deg=ARC_SWEEP_DEG, R=ARC_R, chord=cp["arc"]["neckline_chord"],
            k=4.0 / 3.0 * math.tan((tb - ta) / 4.0),
            control_points=[list(q) for q in cub],
            max_radial_error_mm=_bezier_radial_error(cub),
            analytic_arc_length=ARC_LENGTH,
        ),
        regions=regions,
        area_total=total,
        area_total_numeric=sum(r["area_numeric"] for r in regions),
        area_total_diff=total - sum(r["area_numeric"] for r in regions),
        join="三块沿 P₁A / P₁′A′ 共边拼接＝第 4 步一条连续竖起领子；"
             "穿着时左右襟在前中交叠，平铺裁片各自独立，不扣减交叠量",
        old_strip_area=ci["area"],
        old_strip_area_note="12:29 旧版「等宽直条 L×h」，已被用户否定，仅作差量对照",
        area_diff_vs_old=total - ci["area"],
    )


def collar_integral():
    """装领线 ∫ds 数据（**保留作对照，不再是领条裁片依据**）。
    【定位变更 2026-11-11 14:24】用户否定「等宽直条」：∫ds 本身无误，
    但不能用 L×h 当裁片；领条改为三块平面区域，各自对边缘曲线作面积分。
    本函数只保留装领线弧长 L、特征点累积弧长 s、旧直条面积，供差量对照。
    纯函数，不量图、不引入任何新参数。"""
    cp = collar_points()
    right_arc = ARC_LENGTH                        # ∫R dθ，R=弦长、θ=π/3
    back = cp["P1p"][0] - cp["P1"][0]             # 后颈段 |P₁P₁′| = 100
    left_arc = ARC_LENGTH                         # 左片 = 右片 x=0 镜像，弧长相同
    L = right_arc + back + left_arc

    # 独立数值线积分：沿 lower_path 的解析采样折线逐段累加 |Δ|
    lp = [tuple(q) for q in cp["lower_path"]]
    ds_num = sum(math.dist(lp[i], lp[i + 1]) for i in range(len(lp) - 1))
    # 上缘（竖起投影）线积分，仅作对照，不进裁片
    up = [tuple(q) for q in cp["upper_path"]]
    upper_num = sum(math.dist(up[i], up[i + 1]) for i in range(len(up) - 1))

    # 特征点的弧长坐标 s（累积 ∫ds），按装领线走向 P₂ → P₁ → P₁′ → P₂′
    stations = [
        dict(name="P₂B", s=0.0, xy=[0.0, 0.0],
             role="起点边 P₂B（右侧前中）"),
        dict(name="P₁A", s=right_arc, xy=[right_arc, 0.0],
             role="右 60° 弧结束 / 后颈段起点；对位刀口"),
        dict(name="P₁′A′", s=right_arc + back, xy=[right_arc + back, 0.0],
             role="后颈段结束 / 左 60° 弧起点；对位刀口"),
        dict(name="P₂′B′", s=L, xy=[L, 0.0],
             role="终点边 P₂′B′（左侧前中）"),
    ]
    # 格林公式对领条长方形作面积积分 ½∮(x dy − y dx) 校验
    rect = [(0.0, 0.0), (L, 0.0), (L, COLLAR_H), (0.0, COLLAR_H)]
    area_green = abs(sum(rect[i][0] * rect[(i + 1) % 4][1]
                         - rect[(i + 1) % 4][0] * rect[i][1]
                         for i in range(4))) / 2.0

    return dict(
        method="沿装领线作线积分 ∫ds（三段：弧 / 直线 / 弧）；无新参数、不量图",
        segments=[
            dict(name="右 60° 弧 P₂→P₁", kind="arc",
                 integral="∫R dθ = R·π/3", value=right_arc,
                 R=ARC_R, sweep_deg=ARC_SWEEP_DEG),
            dict(name="后颈直线 P₁→P₁′", kind="line",
                 integral="∫ds = |P₁P₁′|", value=back),
            dict(name="左 60° 弧 P₁′→P₂′", kind="arc",
                 integral="右片关于 x=0 镜像 ⇒ 弧长相同", value=left_arc),
        ],
        length=L,
        length_numeric_ds=ds_num,
        numeric_diff=ds_num - L,
        upper_projection_length=upper_num,
        upper_minus_lower=upper_num - ds_num,
        width=COLLAR_H,
        width_source="第 4 步 COLLAR_H：四条宽度边各 30mm、等高连续竖起",
        area=L * COLLAR_H,
        area_green=area_green,
        stations=stations,
        strip_shape="【已作废·仅作对照】12:29 旧版等宽直条 L×h；用户 14:24 否定，领条改为三块平面区域",
        upper_note="第 4 步上缘直线折线是竖起 / 交叠投影，线积分 %.6f mm，不进平铺裁片" % upper_num,
        template_collar_note="模板「领缘条」1740×70 属旧领口（贯通门襟），本裁片图不采用",
    )


def collar_strip_pieces(regions=None):
    """领条＝三块平面裁片（前片左襟 / 后片 / 前片右襟＝左襟镜像）。
    每片 cmds 由 M/L/C/Z 组成（曲边是三次贝塞尔），**不是等宽直条、不用采样折线**；
    grain 沿用模板「领缘条」[1,0]。片内 note 写积分面积（≤16 字）。"""
    rg = regions or collar_regions()
    tpl_collar = next(p for p in TPL["pieces"] if p["name"] == "领缘条")
    out = []
    for r in rg["regions"]:
        out.append({
            "name": r["name"], "qty": 1,
            "cmds": json.loads(json.dumps(r["cmds"])),
            "grain": list(tpl_collar["grain"]),
            "notches": [],
            "marks": [],
            "aux": [],
            "points": [],
            "dims": [],
            "note": "A=%.2f mm²" % r["area"],
            "links": [], "dashed": [],
        })
    return out


def sheet_pieces_step5():
    """完整裁片图：前片 2 + 后片 2 + 领条 3 = **7 片**。
    前片沿用第 3 步片表（新领口红弧、旧边虚线、cmds 与模板逐项相同）；
    后片两片只对模板「后片半」做镜像变换；领条三块是新增（平面曲边区域，非等宽直条）。
    前 / 后片几何始终未改（geometry_changed=False）。"""
    pieces = sheet_pieces_step3()

    rb = back_piece()
    rb["name"] = "后片（右·半）"
    rb["qty"] = 1
    rb["marks"] = []
    rb["aux"] = []
    rb["points"] = []
    rb["dims"] = []
    rb["note"] = ""
    lb = json.loads(json.dumps(rb))
    lb["name"] = "后片（左·半·镜像）"
    lb["cmds"] = mirror_cmds(rb["cmds"])
    lb["grain"] = [-rb["grain"][0], rb["grain"][1]]
    lb["notches"] = [[-n[0], n[1]] for n in rb["notches"]]
    pieces += [rb, lb]

    pieces += collar_strip_pieces()
    return pieces


# ---- 第 6 步（重做 2026-11-11 16:00）：领条＝一条带状，三段沿共边相接、首尾不接 ----
# 15:58 用户否定上一版（三块拼成自交闭合轮廓、视觉两层）：
#   「产物不会是这种两层的不明物体，而是一条由三部分组成的带状领子」
# 16:00 补充：「首尾相接 领条首尾不想接」⇒ 领条两端 P₂B / P₂′B′ 分开、不相接（不绕成环）。
#
# 做法＝沿共边依次**翻折展开**（刚性铰接，每段形状严格不变）：
#   段 1（左襟）不动；
#   段 2（后片）关于直线 P₁A 反射；
#   段 3（右襟）先随段 2 用同一反射，再关于**反射后的** P₁′A′ 反射。
# 反射是等距变换 ⇒ 边长 / 角度 / 面积全部不变（不拉伸、不近似、不量图）。
# 展开后三段沿 x 依次排开：段 3′ x[-220.6,-129.1]／段 2′ x[-144.0,-44.8]／段 1 x[-50,8.6]，
# 只在共边 P₁A、P₁′A′（各 30mm）处相接 ⇒ **不自交**，两端自然分开。
BAND_NAME = "领条"


def _seg_cross(p1, p2, p3, p4):
    """两线段严格相交（不含端点相切）时的交点，否则 None。用于如实记录自交。"""
    def cr(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = cr(p3, p4, p1), cr(p3, p4, p2)
    d3, d4 = cr(p1, p2, p3), cr(p1, p2, p4)
    if ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4)):
        t = d1 / (d1 - d2)
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


def _refl_pt(p, a, b):
    """点 p 关于过 a、b 的直线作镜像（等距变换）。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    vx, vy = p[0] - a[0], p[1] - a[1]
    d = vx * dx + vy * dy
    return (a[0] + 2.0 * d * dx - vx, a[1] + 2.0 * d * dy - vy)


def _refl_cmds(cmds, a, b):
    """整条 cmds 关于直线 a—b 镜像（M/L/C 的点与控制点全部反射，Z 保留）。"""
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
        elif c[0] in ("M", "L"):
            out.append([c[0], list(_refl_pt(c[1], a, b))])
        elif c[0] == "C":
            out.append(["C", list(_refl_pt(c[1], a, b)),
                        list(_refl_pt(c[2], a, b)), list(_refl_pt(c[3], a, b))])
    return out


def collar_band():
    """第 6 步核心：三段沿共边翻折展开成**一条开放的带状裁片**（首尾不接）。
    纯解析：反射是等距变换，段形状 / 面积严格不变。"""
    rg = collar_regions()
    cp = collar_points()
    P1, P2, P1p, P2p = (tuple(cp[k]) for k in ("P1", "P2", "P1p", "P2p"))
    A, B, Ap, Bp = (tuple(cp[k]) for k in ("A", "B", "Ap", "Bp"))
    regs = rg["regions"]
    c1, c2, c3 = [json.loads(json.dumps(r["cmds"])) for r in regs]

    # 段 2 关于 P₁A 反射；段 3 先同反射、再关于反射后的 P₁′A′ 反射
    c2r = _refl_cmds(c2, P1, A)
    P1p_r, Ap_r = _refl_pt(P1p, P1, A), _refl_pt(Ap, P1, A)
    c3r = _refl_cmds(_refl_cmds(c3, P1, A), P1p_r, Ap_r)

    P2p_r = _refl_pt(_refl_pt(P2p, P1, A), P1p_r, Ap_r)
    Bp_r = _refl_pt(_refl_pt(Bp, P1, A), P1p_r, Ap_r)
    Ap_r2 = _refl_pt(_refl_pt(Ap, P1, A), P1p_r, Ap_r)

    ta, tb = math.radians(ARC_END_DEG), math.radians(ARC_START_DEG)
    cub_r = arc_to_cubic(ta, tb)[0]                     # P₂→P₁
    cub_l = [mirror_x(q) for q in cub_r]                # P₂′→P₁′（段 3 原弧）
    cub3 = [_refl_pt(_refl_pt(q, P1, A), P1p_r, Ap_r)
            for q in reversed(cub_l)]                   # P₁′→P₂′（反射两次）

    edges = [
        dict(kind="C", a=P2, b=P1, ctrl=cub_r, name="下缘 段① 右 60° 弧 P₂→P₁"),
        dict(kind="L", a=P1, b=P1p_r, name="下缘 段② 后颈直线 P₁→P₁′"),
        dict(kind="C", a=P1p_r, b=P2p_r, ctrl=cub3, name="下缘 段③ 左 60° 弧 P₁′→P₂′"),
        dict(kind="L", a=P2p_r, b=Bp_r, name="端头 段③ P₂′→B′"),
        dict(kind="L", a=Bp_r, b=Ap_r, name="上缘 段③ B′→A′"),
        dict(kind="L", a=Ap_r, b=A, name="上缘 段② A′→A"),
        dict(kind="L", a=A, b=B, name="上缘 段① A→B"),
        dict(kind="L", a=B, b=P2, name="端头 段① B→P₂"),
    ]

    cmds = [["M", list(P2)]]
    for e in edges:
        if e["kind"] == "L":
            cmds.append(["L", list(e["b"])])
        else:
            c = e["ctrl"]
            cmds.append(["C", list(c[1]), list(c[2]), list(c[3])])
    cmds.append(["Z"])

    joints = [math.dist(edges[i - 1]["b"], edges[i]["a"]) for i in range(len(edges))]
    joints_max = max(joints)

    I = 0.0
    for e in edges:
        I += _line_green(e["a"], e["b"]) if e["kind"] == "L" else _bezier_green(e["ctrl"])
    area_signed = 0.5 * I

    pts = sheet.sample(cmds, BEZIER_SAMPLES)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    area_numeric = _shoelace(pts)
    perim = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

    # 自交（应为 0）：展开后不自交是关键判据
    co = sheet.sample(cmds, 256)
    if co[0] != co[-1]:
        co.append(co[0])
    nseg = len(co) - 1
    raw = []
    for i in range(nseg):
        for j in range(i + 2, nseg):
            if i == 0 and j == nseg - 1:
                continue
            x = _seg_cross(co[i], co[i + 1], co[j], co[j + 1])
            if x is not None:
                raw.append(x)
    uniq = []
    for x in raw:
        if not any(math.dist(x, u) < 0.5 for u in uniq):
            uniq.append(x)

    segs = [
        dict(name="段① 前片左襟", idx=1, area=regs[0]["area"], cmds=c1,
             role="基准，未镜像；下缘右 60° 弧、上缘 A→B"),
        dict(name="段② 后片", idx=2, area=regs[1]["area"], cmds=c2r,
             role="关于 P₁A 反射展开；下缘后颈直线、上缘 A′→A"),
        dict(name="段③ 前片右襟", idx=3, area=regs[2]["area"], cmds=c3r,
             role="两次反射展开；＝段① 的镜像"),
    ]
    seams = [
        dict(name="共边 P₁A（段①|段②）", a=P1, b=A, length=math.dist(P1, A)),
        dict(name="共边 P₁′A′（段②|段③）", a=P1p_r, b=Ap_r, length=math.dist(P1p_r, Ap_r)),
    ]
    ends = [
        dict(name="端头 B→P₂（段①）", a=B, b=P2, length=math.dist(B, P2)),
        dict(name="端头 P₂′→B′（段③）", a=P2p_r, b=Bp_r, length=math.dist(P2p_r, Bp_r)),
    ]

    def edesc(e):
        d = dict(kind=e["kind"], name=e["name"], a=list(e["a"]), b=list(e["b"]))
        if e["kind"] == "L":
            d.update(length=math.dist(e["a"], e["b"]))
        else:
            d.update(ctrl=[list(q) for q in e["ctrl"]])
        return d

    return dict(
        name=BAND_NAME,
        method="三段沿共边 P₁A / P₁′A′ 依次翻折展开（刚性铰接）：段①不动、段②关于 P₁A 反射、"
               "段③两次反射；展开成一条开放带状裁片，两端 P₂B / P₂′B′ 分开、首尾不接",
        basis="第 3/4/5 步解析几何；反射为等距变换，无拉伸/无近似/不量图、无新参数",
        edges=[edesc(e) for e in edges],
        edge_count=len(edges),
        joints_max=joints_max,
        cmds=cmds,
        segments=segs,
        seams=seams,
        ends=ends,
        area_total=rg["area_total"],
        area_signed=area_signed,
        area_numeric=area_numeric,
        area_diff=abs(area_signed) - area_numeric,
        perimeter=perim,
        self_intersection_count=len(uniq),
        self_intersections=[list(x) for x in uniq],
        flat_cut=True,
        curve_definition="三次贝塞尔 C + 直线 L；cmds 只含 M/L/C/Z，与 sheet.py 出图定义一致",
        P1=list(P1), P2=list(P2), P1p=list(P1p), P2p=list(P2p), A=list(A), B=list(B),
        P1p_r=list(P1p_r), Ap_r=list(Ap_r), P2p_r=list(P2p_r), Bp_r=list(Bp_r),
        regions_area=[r["area"] for r in regs],
    )


def collar_band_piece(band=None):
    """领条＝**一片**带状平面裁片（qty=1）；grain 沿用模板「领缘条」[1,0]。"""
    b = band or collar_band()
    tpl_collar = next(p for p in TPL["pieces"] if p["name"] == "领缘条")
    return {
        "name": b["name"], "qty": 1,
        "cmds": json.loads(json.dumps(b["cmds"])),
        "grain": list(tpl_collar["grain"]),
        "notches": [], "marks": [], "aux": [], "points": [], "dims": [],
        "note": "A=%.2f mm²" % b["area_total"],
        "links": [], "dashed": [],
    }


def sheet_pieces_step6():
    """完整裁片图：前片 2 + 后片 2 + 领条 1（一条带状，三段）= **5 片**。"""
    pieces = sheet_pieces_step3()

    rb = back_piece()
    rb["name"] = "后片（右·半）"
    rb["qty"] = 1
    rb["marks"] = []
    rb["aux"] = []
    rb["points"] = []
    rb["dims"] = []
    rb["note"] = ""
    lb = json.loads(json.dumps(rb))
    lb["name"] = "后片（左·半·镜像）"
    lb["cmds"] = mirror_cmds(rb["cmds"])
    lb["grain"] = [-rb["grain"][0], rb["grain"][1]]
    lb["notches"] = [[-n[0], n[1]] for n in rb["notches"]]
    pieces += [rb, lb]

    pieces.append(collar_band_piece())
    return pieces

