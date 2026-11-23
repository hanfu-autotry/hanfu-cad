# -*- coding: utf-8 -*-
"""
窄袖深衣 V4（含 V4B 变体 arc_po）· 裁片与平铺（2026-11-18 从 V3 分出；V4B 2026-11-22 重置：左片＝右片镜像 + 古制通用上领、删续衽）
────────────────────────────────────────────────────────────────
依据：深衣三步图 / 剪裁与平铺图（hanfu-studio/kit/sources/02-深衣_古制/）
      孙韬《拒绝碰瓷，一篇文章说清楚西周矩领》"窄袖深衣的腰线，实为高腰甚至齐胸位置"
  · 材料 = 4 幅 × 2 段（上衣段 = 2×衣长，裳段 = 裳高）——两段同宽，无台阶
  · 上衣段水平对折 → 上衣前后；**衣长 = 袖肥 = 袖口**（同一个数！）
  · 裳段 = 一条 4 幅 × 裳高 的带子，**左右折**：两侧（±1 幅）折、中缝缝合（用户 2026-11-18）
  · 前中直接剪开两道（间距 160，不折）；领条＝**与襟缘平行的等宽带**（宽＝领宽 30），
    颈口转折为「前片两三角 ＋ 后片梯形」（底 160 → 顶 160−2×30＝100，高 30）；
    立起高 ≡ 带宽；中间露出后片 160−2×30＝100 —— 与 `hanfu-zhidui` 的领条算法完全一致（2026-11-18）
    ↑ **V3 原法，V4 已弃用**：V4 新领口 PP′D′D ＋ 领条统一算法（见下方「一步一画」注释块）
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
import os, json, math
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collar

_DEF = dict(
    FAB_W=500.0,        # 单幅宽
    N_PANEL=4,          # 拼幅数（= 通袖 4 匹）
    L_BODY=195.0,       # ★衣长（＝袖肥＝袖口，三者同值）：窄袖 195；V2 宽袖版填 624
                        #   （★V4B 变体模式用 385＝总长一半，由 V4B 夹具传入，默认值仍 195）
    GARMENT_L=770.0,    # ★成衣总长（肩线到摆）：便服外套 770（厂商实测男 M 衣长）；礼服去掉这行用 1872
    NECK_W=160.0,       # ★领口宽（旋钮）＝前中开口宽（两剪开线间距）
    COLLAR_W=30.0,      # ★领宽（3cm）= 领条宽 = 立起高（与 hanfu-zhidui 同一口径）
    PD=70.0,            # ★一步一画①：颈侧点 P 沿原领缘直线到动点 D 的距离（7cm）
    LL_W=30.0,          # ★领宽（旋钮）：领条全路线统一带宽（含中缝两边），暂 3cm
    NECK_MODE="ec",     # ★领口形态：ec=矩领（EC 交叉版）｜arc_po=V4B（左片＝右片镜像，襟缘斜线 P→O / P′→O）
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

# 领条（古制统一算法，见 pattern/collar.py）：开领＝颈侧点→O 的弦，领条＝平行襟缘等宽带
#   ★弦的下端 O（2026-11-22 已回滚）：O＝下摆中点 (0,0)，前中剪开贯通到摆（两种形态相同）。
_NECK = P.get("NECK_MODE", "ec")                # 领口形态：ec=矩领（EC 交叉）｜arc_po=V4B（镜像＋古制上领）
_O_PT = (0.0, 0.0)                              # O＝下摆中点（回滚：上衣中点版本已撤）
_CHORD_DROP = Y_FOLD - _O_PT[1]                 # 弦的竖直落差（collar.geom 的 y_top）
_CG = collar.geom(SLIT_HALF, _CHORD_DROP, COLLAR_W)
COLLAR_L, NECK_H = _CG["length"], _CG["stand"]

# ── 一步一画①：新领口 PP'D'D（2026-11-20）────────────────────────────
#   P  ＝既有颈侧点 (±SLIT_HALF, Y_FOLD)，镜像得 P'
#   原领缘直线 ＝ 弦 P → Q(0,0)（即旧开领剪除线）
#   D  ＝该弦上、距 P 沿弦 PD 的动点；PD=70（7cm）；镜像得 D'
#   连接 DD' 得新领口四边形 P-P'-D'-D；原贯通到摆的开领剪除移除。
#   一步一画②：中缝两边装竖直矩形领条——D 垂线到摆 = DD1（右片领左缘），镜像 D'D2；
#   领宽不写死，＝D 到中缝距离 DX（见下）。旧斜襟缘 D→Q 已删除，不再画。
PD = P["PD"]
_CHORD = math.hypot(SLIT_HALF, Y_FOLD)          # 原领缘弦 P→Q 长
_T = PD / _CHORD                                # D 自 P 向 Q 的比例
DX = SLIT_HALF * (1.0 - _T)                     # D 的 x（右侧为正）
DY = Y_FOLD * (1.0 - _T)                        # D 的 y（布面，上为正）
assert DY >= Y_WAIST, "PD=%.1f 过大：D 已越过上衣段下界（腰线）" % PD

# 领条（一步一画③·如实绘制）：**连续一条**，沿路线 O→O′→D′→P′→P→D→O′→O（中缝不缝合），
#   即沿中缝上下＋绕领口一周；领条宽＝LL_W（独立旋钮，暂 30）——中缝两边的矩形区域领
#   就是领条在中缝段的部分，**与领口领条同宽**（2026-11-20 统一）。
#   每段路线按真实带宽画带、不做整体填充；带宽与领口区高（69.6）的叠合/留空如实呈现。
LL_W = P["LL_W"]                                # 领宽（领条与中缝两边统一，旋钮，暂 30）
assert LL_W > 0, "LL_W=%.1f 必须为正" % LL_W
DO_W = LL_W                                     # 领条带宽（画带代码用名）

# ── V4B 领子几何（arc_po）：左片＝右片镜像 ＋ 古制通用上领算法（collar.py）────────
#   第①步：左片不再有自己的算法，只由右片 x 取反镜像：
#     右片襟缘 = 弦 P′(+a,Y_FOLD) → O(0,0)；左片襟缘 = 同一份点的镜像 → P(−a,Y_FOLD) → O
#     后片颈口 = 直线 P → P′
#   第②步：删掉「唐圆领端边扫掠」的 70mm 领带，改回**古制通用上领算法**
#     （pattern/collar.py::geom —— 与 V2/V3 用的是同一处代码，不另写一套）：
#       开领 = 弦 P(±a,Y_FOLD) → O(0,Y_WAIST)           ← 就是上面两条镜像襟缘
#       领条 = 与襟缘**平行的等宽带**，宽 = COLLAR_W；内缘 = 襟缘向领口内让 COLLAR_W
#       颈口 = 在肩线处转折为「前片两三角 ＋ 后片梯形」，顶半宽 NTH 由 miter 闭式解出
#       立起高 ≡ 带宽；领条长 = 2·|PO| ＋ 开领宽 2a（见 ④ 领条裁片）
#   第③步（已回滚）：O 曾移到上衣中点 (0,Y_WAIST)（止于腰线、裳不剪开），现按用户要求退回
#     O＝下摆中点 (0,0)、衣长退回 1/2 —— 即第②步的状态。
if _NECK == "arc_po":
    _N_LAPEL = 28

    def _mir(pts):
        """右片 → 左片：x 取反。左片不再有任何独立算法/独立参数。"""
        return [(-x, y) for (x, y) in pts]

    # 右片襟缘（唯一一版几何）：弦 P′(a,Y_FOLD) → O(0,0)＝下摆中点（贯通到摆）
    _LAPEL_R = [(SLIT_HALF + (_O_PT[0] - SLIT_HALF) * i / float(_N_LAPEL),
                 Y_FOLD + (_O_PT[1] - Y_FOLD) * i / float(_N_LAPEL))
                for i in range(_N_LAPEL + 1)]
    _LAPEL_L = _mir(_LAPEL_R)                                   # 左片襟缘＝镜像（P→O）
    _NECK_BACK = [(-SLIT_HALF + 2 * SLIT_HALF * i / 8.0, Y_FOLD) for i in range(9)]   # P→P′

    # 古制通用上领（collar.py 口径，直接用模块级的 _CG，见文件头）：
    N_X, N_Y = _CG["nx"], _CG["ny"]        # 指向领口内侧的单位法向（右襟；左襟取负）
    NTH = _CG["top_half"]                  # 后领条顶半宽（miter 解出）
    _LS_W = COLLAR_W                       # 领条带宽＝领宽＝立起高
    # ── 第⑤步（2026-11-22 用户定）：上领路线 H→F→P′；三角形 O-H-F ＝ 续衽 ──────────
    #   H＝下摆上的自由点（旋钮 H_X）；F＝右片边缘(弦 P′O)上与**腋点**同高的点；
    #   腋点＝腋下记号竖线上端 (ARMPIT, Y_WAIST + ARMPIT_H)。
    #   上领路线（右片）＝ H → F → P′，内襟同样镜像；三条线围出的三角形 O-H-F 为续衽。
    #   ★原先 P′→H 的虚线弧已按要求删除。
    _H_X = float(P.get("H_X", -270.0))
    _H_PT = (_H_X, _O_PT[1])                                       # H＝(H_X, 下摆)
    _ARM_PT = (ARMPIT, Y_WAIST + ARMPIT_H)                          # 右腋点
    _uF = (_ARM_PT[1] - _O_PT[1]) / (Y_FOLD - _O_PT[1])
    _F_PT = (_O_PT[0] + _uF * (SLIT_HALF - _O_PT[0]), _ARM_PT[1])   # F＝弦上与腋点同高处
    _ROUTE_R = [_H_PT, _F_PT, (SLIT_HALF, Y_FOLD)]                  # 上领路线 H→F→P′

    def _offset_route(pts, w):
        """折线按「行进方向左侧」内让 w，拐点用斜接。返回偏移后的点列（含两端）。"""
        n = len(pts)
        segs = []
        for i in range(n - 1):
            dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            L = math.hypot(dx, dy) or 1.0
            segs.append((dx / L, dy / L))
        off = [((pts[i][0] - segs[i][1] * w, pts[i][1] + segs[i][0] * w), segs[i])
               for i in range(len(segs))]                            # 每段：左法向偏移后的点 + 方向
        res = [off[0][0]]
        for i in range(1, len(off)):
            (p1, u1), (p2, u2) = off[i - 1], off[i]
            den = u1[0] * u2[1] - u1[1] * u2[0]
            if abs(den) < 1e-9:
                res.append(p2)
            else:
                t = ((p2[0] - p1[0]) * u2[1] - (p2[1] - p1[1]) * u2[0]) / den
                res.append((p1[0] + t * u1[0], p1[1] + t * u1[1]))    # F 处斜接点
        res.append((pts[-1][0] - segs[-1][1] * w, pts[-1][1] + segs[-1][0] * w))
        return res
    _INNER_R = _offset_route(_ROUTE_R, _LS_W)      # 领条内缘（右片）
    _INNER_L = _mir(_INNER_R)                      # 内襟镜像
    #   ★内外襟完全对称：H/F 与续衽三角形都镜像一份（H′、F′）
    _H_M_PT = (-_H_PT[0], _H_PT[1])                 # H′（内襟）
    _F_M_PT = (-_F_PT[0], _F_PT[1])                 # F′（内襟）
    _XUR_FILL = "#f6e9de"                           # 续衽填充（ORANGE 13% 叠白预混合；studio 解析器不认 fill-opacity）
    _XUR_R = [_O_PT, _H_PT, _F_PT]                  # 续衽（外襟·右）
    _XUR_L = [_O_PT, _H_M_PT, _F_M_PT]              # 续衽（内襟·左，镜像）
    # 领条长 = 2×(|HF| + |FP′|) + 后领宽 2a（沿上领路线量，不再用整条弦）
    _LEAD_LEN = 2 * (math.dist(_H_PT, _F_PT) + math.dist(_F_PT, (SLIT_HALF, Y_FOLD))) + 2 * SLIT_HALF
    _LEAD_NOTCH = [math.dist(_H_PT, _F_PT), math.dist(_H_PT, _F_PT) + math.dist(_F_PT, (SLIT_HALF, Y_FOLD))]
    print("[古制上领] arc_po：开领宽=%.0f 带宽=%.0f 顶半宽=%.1f H=(%.0f,%.0f) F=(%.1f,%.1f) "
          "内缘斜接=(%.1f,%.1f)" %
          (2 * SLIT_HALF, _LS_W, NTH, _H_PT[0], _H_PT[1], _F_PT[0], _F_PT[1],
           _INNER_R[1][0], _INNER_R[1][1]), file=sys.stderr)

if _NECK != "arc_po":
    _LEAD_LEN = COLLAR_L                           # 矩领：仍用 collar.py 的领条长
    _LEAD_NOTCH = [SLIT_HALF, COLLAR_L - SLIT_HALF]

# ── 领条统一算法 v3：两条镜像带，经 E-C 斜线在中央下垂（右带压左带）────────
#   E＝中缝上 O′E=领宽（DD′ 上方）；C＝DD′ 上 O′C=领宽（中线右侧）；连接 EC（45°）。
#   左带：P →(左斜边内让)→ D →(45°斜接)→ DD′ 上方横段(D→E) →(沿 EC 斜下)→ C
#         → 右竖带外缘(x=+30) 垂到摆。右带镜像（E→C′→ 左竖带 x=−30）。
#   O′ 不接缝（只是中缝/竖带交点）；中缝不缝合；肩段向外过肩（转到背面）。
def _line_isect(p1, u1, p2, u2):
    """两直线 p1+t·u1 与 p2+s·u2 求交。"""
    den = u1[0] * u2[1] - u1[1] * u2[0]
    t = ((p2[0] - p1[0]) * u2[1] - (p2[1] - p1[1]) * u2[0]) / den
    return (p1[0] + t * u1[0], p1[1] + t * u1[1])

_W = DO_W
_DD_TOP = DY + _W                               # E 的高度（DD′ 上方一个带宽）
# 领口角点（布面坐标）
P_pt = (-SLIT_HALF, Y_FOLD)                     # 左颈侧点
Pp_pt = (SLIT_HALF, Y_FOLD)                     # 右颈侧点
D_pt = (-DX, DY)                                # 左领边角
Dp_pt = (DX, DY)                                # 右领边角
E_pt = (0.0, _DD_TOP)                           # E＝中缝上 O′E=领宽
C_pt = (_W, DY)                                 # C＝DD′ 上 O′C=领宽
Cm_pt = (-_W, DY)                               # C′（镜像）
# 左斜边（P→D）行进方向与左法向（＝向领口内）
_ux5, _uy5 = D_pt[0] - P_pt[0], D_pt[1] - P_pt[1]
_l5 = math.hypot(_ux5, _uy5)
_ux5, _uy5 = _ux5 / _l5, _uy5 / _l5             # (0.1033, -0.9945)
_n5x, _n5y = -_uy5, _ux5                        # (0.9945, 0.1033) 内让法向
P_n5 = (P_pt[0] + _n5x * _W, P_pt[1] + _n5y * _W)
D_n5 = (D_pt[0] + _n5x * _W, D_pt[1] + _n5y * _W)
M_D = _line_isect(D_n5, (_ux5, _uy5), (D_pt[0], _DD_TOP), (1.0, 0.0))    # D 角斜接点
M_P = _line_isect(P_n5, (_ux5, _uy5), (P_pt[0], Y_FOLD + _W), (1.0, 0.0))# 肩角斜接点
# 右斜边（D′→P′）镜像
D_n3 = (-D_n5[0], D_n5[1])
P_n3 = (-P_n5[0], P_n5[1])
M_Dp = (-M_D[0], M_D[1])
M_Pp = (-M_P[0], M_P[1])

_BANDS = [
    dict(name="左带",
         fills=[(P_pt, D_pt, D_n5, P_n5),                               # 左斜边带
                (D_pt, (0.0, DY), E_pt, M_D),                           # DD′ 上方横段（D→E）
                ((0.0, 0.0), (_W, 0.0), C_pt, (0.0, DY))],              # 右竖带（顶边斜至 C）
         free=[(P_n5, M_D), (M_D, E_pt),                                # 斜边自由缘→DD′ 自由缘（至 E）
               (E_pt, C_pt),                                            # 45° EC 斜线（关键）
               (C_pt, (_W, 0.0))],                                      # 竖带外缘垂到摆
         seams=[(D_pt, M_D)]),                                          # 领边角 D 45° 折转缝
    dict(name="右带",
         fills=[(Pp_pt, Dp_pt, D_n3, P_n3),                             # 右斜边带
                (Dp_pt, (0.0, DY), E_pt, M_Dp),                         # DD′ 上方横段（D′→E）
                ((0.0, 0.0), (-_W, 0.0), Cm_pt, (0.0, DY))],            # 左竖带（顶边斜至 C′）
         free=[(P_n3, M_Dp), (M_Dp, E_pt),
               (E_pt, Cm_pt),                                           # 镜像 EC′ 斜线
               (Cm_pt, (-_W, 0.0))],
         seams=[(Dp_pt, M_Dp)]),
]
# 肩段（两带共用的一整条，向外过肩＝转到背面）
_SHOULDER = dict(quad=(P_pt, Pp_pt, M_Pp, M_P),
                 free=[(M_P, M_Pp)],
                 seams=[(P_pt, M_P), (Pp_pt, M_Pp)])

# 矩形区域领（＝领条在中缝两边的部分）：外缘 x＝±LL_W；D1/D2 ＝ 外缘在下摆上的垂足。
#   旧斜襟缘 D→Q 已删，不再画。
D1_X = LL_W                                     # 矩形区域领外缘 x（统一到领口领条宽，旋钮 LL_W）
Y_SEG1 = Y_WAIST                        # （兼容旧名）腰线
Y_SEG2 = CLOTH_H                        # （兼容旧名）布片顶边

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

NAME = "V4 一步一画" if abs(L_BODY - 195) < 1 else "V4（衣长 %d）" % round(L_BODY)

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
def _txt(x, y, t, size=26, color=None, weight=None, anchor=None, family="sans-serif"):
    """画布坐标写一行字。"""
    _a = (' text-anchor="%s"' % anchor) if anchor else ''
    _w = (' font-weight="%s"' % weight) if weight else ''
    s.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d"%s%s fill="%s">%s</text>'
             % (x, y, family, size, _w, _a, color or BLACK, t))

if _NECK == "arc_po":
    _txt(MARGIN, 96, "古制过渡-襦 · 左片＝右片镜像 ＋ 古制通用上领 ＋ 续衽", 44, BLACK, "700")
    _txt(MARGIN, 148,
         "衣长 %.0f（＝成衣总长 %.0f 的 1/2）｜裳高 %.0f｜开领宽 %.0f｜领宽（带宽＝立起高）%.0f｜"
         "领条长 %.1f｜续衽 2 片" % (L_BODY, L_BODY + SHANG_H, SHANG_H, NECK_W, COLLAR_W, _LEAD_LEN),
         26, "#4a4a4a")
    # 图例（右上）
    _lx, _ly = 1980.0, 96.0
    _legend = ((RED, None, "红线＝开领/襟缘（弦 P→O、P′→O）"),
               (GREEN, "18 12", "绿虚线＝领条内缘（沿上领路线内让一个领宽）"),
               (ORANGE, None, "橙＝续衽三角 O-H-F 与 O-H′-F′"),
               (PURPLE, None, "紫＝H/H′（下摆自由点）、F/F′（与腋点同高）"),
               (BLACK, None, "黑＝布片轮廓 / 颈口三角＋后片梯形"))
    for _i, (_c, _d, _t) in enumerate(_legend):
        _yy = _ly + _i * 34
        s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="3"%s fill="none"/>'
                 % (_lx, _yy - 8, _lx + 46, _yy - 8, _c,
                    (' stroke-dasharray="%s"' % _d) if _d else ''))
        _txt(_lx + 58, _yy, _t, 22, "#4a4a4a")

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
# （段标注文字移除）

# ── 对折线（中段正中 = 肩线）──────────────────────────────────────
s.append('<g id="FOLD" stroke="%s" stroke-width="3" fill="none" stroke-dasharray="46 16 10 16">' % ORANGE)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF_S - 55), Y(Y_FOLD), X(HALF_S + 55), Y(Y_FOLD)))
s.append('</g>')
# （对折线标注文字移除）

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
# （裳折/布边/前中标注文字移除）

# ── 一步一画③：领条统一算法 v2（先画，垫在红/黑路线边之下）────────────────
#   两条镜像带在中缝 O′ 处 45° 交叉（右带压左带）；转角 45° 斜接于领边角 D/D′
#   与肩角 P/P′；DD′ 上方中线 ±30 以内为领口开口（无带）。
def _poly_main(pts, fill_op=None):
    _ps = " ".join("%.1f,%.1f" % (X(p[0]), Y(p[1])) for p in pts)
    if fill_op is not None:
        s.append('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="none"/>' % (_ps, GREEN, fill_op))
    else:
        s.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="2.2"/>' % (_ps, GREEN))
def _line_main(a, b, dash=False, w=2.2):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"%s stroke="%s" stroke-width="%.1f" fill="none"/>' % (
        X(a[0]), Y(a[1]), X(b[0]), Y(b[1]),
        ' stroke-dasharray="18 12"' if dash else '', GREEN, w))
if _NECK == "ec":                              # 矩领（EC 交叉版）才画领条
    s.append('<g id="COLLAR_BAND">')
    for _bd in _BANDS:                                  # 带填充：左带 → 右带（右带压左带）
        for _q in _bd["fills"]:
            _poly_main(_q, 0.14)
    _poly_main(_SHOULDER["quad"], 0.14)                 # 肩段（两带共用，向外过肩）
    for _bd in _BANDS:                                  # 线：左带 → 右带
        for _a, _b in _bd["free"]:
            _line_main(_a, _b, dash=True, w=2.6)        # 自由缘（绿虚线）
        for _a, _b in _bd["seams"]:
            _line_main(_a, _b, w=2.2)                   # 45° 折转缝（实线）
    for _a, _b in _SHOULDER["free"]:
        _line_main(_a, _b, dash=True, w=2.6)            # 肩段自由缘（绿虚线）
    for _a, _b in _SHOULDER["seams"]:
        _line_main(_a, _b, w=2.2)                       # 肩角 45° 折转缝
    s.append('</g>')
# （"中缝不缝合"文字移除）
if _NECK == "arc_po":
    # ── 古制通用上领（主图·折布）：领条内缘 = 与襟缘平行的等宽带外沿 ──────────────
    #   照 V3 同款画法（build_v3.py::LAPELFOLD）：内缘＝襟缘点 + 带宽·法向；颈侧点向下
    #   130 的短竖线接到内缘起点（＝领条在颈口折转的那条边，平铺图里展开成三角/梯形）。
    #   ★续衽已按要求删除（原弧 O′P′ + P′F + FO 围成的区域不再画）。
    s.append('<g id="LAPELFOLD" stroke="%s" stroke-width="2.6" fill="none" stroke-dasharray="18 12">' % GREEN)
    for _inr, _sx in ((_INNER_R, 1), (_INNER_L, -1)):
        s.append('  <path d="%s"/>' % " ".join(
            "%s %.1f %.1f" % ("M" if _i == 0 else "L", X(_q[0]), Y(_q[1]))
            for _i, _q in enumerate(_inr)))                     # 内缘＝上领路线 H→F→P′ 的内让折线
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
            X(_sx * SLIT_HALF), Y(Y_FOLD - 130), X(_inr[-1][0]), Y(_inr[-1][1])))
    s.append('</g>')

# ── 一步一画①：新领口 PP′D′D（原贯通到摆的开领剪除已移除）────────────
#   P/P′＝既有颈侧点（红）；D/D′＝原领缘弦上距 P 沿弦 PD 的动点及其镜像（黑）；连 DD′
s.append('<g id="NECK" stroke="%s" stroke-width="3.6" fill="none">' % RED)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(SLIT_HALF), Y(Y_FOLD), X(-SLIT_HALF), Y(Y_FOLD)))  # P→P′
if _NECK == "ec":
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(SLIT_HALF), Y(Y_FOLD), X(DX), Y(DY)))          # P→D
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-SLIT_HALF), Y(Y_FOLD), X(-DX), Y(DY)))        # P′→D′
else:
    # 变体（arc_po·第①步）：左右两片襟缘同形——只写一次右片斜线 P′→O，左片由镜像得出（斜线 P→O）。
    #   ★原「左片领口＝同心底圆弧左段 P→O′」已删（那是一套独立的左片算法）。
    s.append('  <path d="%s"/>' % " ".join("%s %.1f %.1f" % ("M" if i == 0 else "L", X(p[0]), Y(p[1]))
                                          for i, p in enumerate(_LAPEL_R)))   # 右片襟缘 P′→O
    s.append('  <path d="%s"/>' % " ".join("%s %.1f %.1f" % ("M" if i == 0 else "L", X(p[0]), Y(p[1]))
                                          for i, p in enumerate(_LAPEL_L)))   # 左片襟缘＝镜像 P→O
s.append('</g>')
if _NECK == "ec":                              # D/D′/DD′ 属矩领（ec）概念；arc_po 已无此角点
    s.append('<g id="DD" stroke="%s" stroke-width="3.2" fill="none">' % BLACK)
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(DX), Y(DY), X(-DX), Y(DY)))                    # D→D′
    s.append('</g>')
def _xmark(cx, cy, color, r):
    s.append('<g stroke="%s" stroke-width="2.8" fill="none">'
             '<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
             '<circle cx="%.1f" cy="%.1f" r="5" fill="%s"/></g>'
             % (color, cx - r, cy - r, cx + r, cy + r, cx - r, cy + r, cx + r, cy - r, cx, cy, color))
for sx in (-1, 1):
    _xmark(X(sx * SLIT_HALF), Y(Y_FOLD), RED, 16)     # P / P′
    if _NECK == "ec":
        _xmark(X(sx * DX), Y(DY), BLACK, 18)          # D / D′（仅矩领）
s.append('<g font-family="sans-serif" font-size="30" font-weight="600">')
s.append('  <text x="%.1f" y="%.1f" fill="%s">P</text>' % (X(-SLIT_HALF) - 46, Y(Y_FOLD) - 24, RED))
s.append('  <text x="%.1f" y="%.1f" fill="%s">P′</text>' % (X(SLIT_HALF) + 22, Y(Y_FOLD) - 24, RED))
if _NECK == "ec":
    s.append('  <text x="%.1f" y="%.1f" fill="%s">D</text>' % (X(-DX) - 52, Y(DY) - 20, BLACK))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">D′</text>' % (X(DX) + 24, Y(DY) - 20, BLACK))
s.append('</g>')

# ── 记号与标注（矩形区域领已并入领条统一算法，不再单独画）────────
if _NECK == "ec":
    # （领宽标注绿字移除）D1 / D2 / E / C 点位保留
    for sx in (-1, 1):
        _xmark(X(sx * D1_X), Y(0), BLACK, 18)        # D1 / D2（下摆上的垂足）
    _xmark(X(0), Y(_DD_TOP), BLACK, 14)              # E＝中缝上 O′E=领宽
    _xmark(X(_W), Y(DY), BLACK, 14)                  # C＝DD′ 上 O′C=领宽
if _NECK == "ec":
    _xmark(X(0), Y(DY), BLUE, 14)                    # O′＝中缝∩DD′（仅矩领有 DD′）
_xmark(X(_O_PT[0]), Y(_O_PT[1]), BLUE, 14)           # O＝弦下端（下摆中点）
if _NECK == "arc_po":
    _xmark(X(_H_PT[0]), Y(_H_PT[1]), PURPLE, 14)     # H＝下摆上的自由点（旋钮 H_X）
    _xmark(X(_F_PT[0]), Y(_F_PT[1]), PURPLE, 14)     # F＝弦上与腋点同高处（分段点）
    _xmark(X(_H_M_PT[0]), Y(_H_M_PT[1]), PURPLE, 14)  # H′（内襟镜像）
    _xmark(X(_F_M_PT[0]), Y(_F_M_PT[1]), PURPLE, 14)  # F′（内襟镜像）
    # 直连 H—F（外襟）与 H′—F′（内襟）
    s.append('<g id="HF_LINE" stroke="%s" stroke-width="2.4" fill="none">' % PURPLE)
    for _a, _b in ((_H_PT, _F_PT), (_H_M_PT, _F_M_PT)):
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
            X(_a[0]), Y(_a[1]), X(_b[0]), Y(_b[1])))
    s.append('</g>')
    # 续衽＝三角形 O-H-F（外襟）与 O-H′-F′（内襟镜像），淡橙填充＋橙实线
    s.append('<g id="XURAN">')
    for _tri in (_XUR_L, _XUR_R):                                # 先内襟后外襟（外襟压上）
        _p = "M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (
            X(_tri[0][0]), Y(_tri[0][1]), X(_tri[1][0]), Y(_tri[1][1]),
            X(_tri[2][0]), Y(_tri[2][1]))
        s.append('  <path d="%s" fill="%s" stroke="none"/>' % (_p, _XUR_FILL))
        s.append('  <path d="%s" stroke="%s" stroke-width="2.6" fill="none"/>' % (_p, ORANGE))
    s.append('</g>')
s.append('<g font-family="sans-serif" font-size="30" font-weight="600">')
if _NECK == "ec":
    s.append('  <text x="%.1f" y="%.1f" fill="%s">D1</text>' % (X(-D1_X) - 62, Y(0) - 26, BLACK))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">D2</text>' % (X(D1_X) + 22, Y(0) - 26, BLACK))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">E</text>' % (X(0) + 20, Y(_DD_TOP) + 36, BLACK))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">C</text>' % (X(_W) + 26, Y(DY) - 12, BLACK))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">O′</text>' % (X(0) + 18, Y(DY) + 44, BLUE))
s.append('  <text x="%.1f" y="%.1f" fill="%s">O</text>' % (X(_O_PT[0]) + 18, Y(_O_PT[1]) - 34, BLUE))
if _NECK == "arc_po":
    s.append('  <text x="%.1f" y="%.1f" fill="%s">H</text>' % (
        X(_H_PT[0]) + 14, Y(_H_PT[1]) - 20, PURPLE))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">H′</text>' % (
        X(_H_M_PT[0]) - 46, Y(_H_M_PT[1]) - 20, PURPLE))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">F</text>' % (
        X(_F_PT[0]) + 24, Y(_F_PT[1]) + 8, PURPLE))
    s.append('  <text x="%.1f" y="%.1f" fill="%s">F′</text>' % (
        X(_F_M_PT[0]) - 52, Y(_F_M_PT[1]) + 8, PURPLE))
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
# （图例文字整块移除；点位字母标注不在图例内，保留）

# ── ③ 平铺 ────────────────────────────────────────────────────────
s.append('<g id="FLAT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
# 袖带（衣身连袖）：左右两端 = 袖口，上边 = 肩线（折线），下边 = 腰线
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f"/>' % (
    FX(-HALF_S), FY(0), FX(-HALF_S), FY(L_BODY), FX(HALF_S), FY(L_BODY)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (FX(HALF_S), FY(L_BODY), FX(HALF_S), FY(0)))
# 肩线（折边）：领口段（P→P′ 之间 ±SLIT_HALF）断开
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (FX(-HALF_S), FY(0), FX(-SLIT_HALF), FY(0)))
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

# ── 平铺前中（同步③统一算法）：新领口 PP′D′D ＋ 领条线稿 ─────────────────
#   领口：P(±SLIT_HALF, 肩线) → D(±DX, 领口深 D0)，DD′ 横线封口；
#   领条（含中缝两段）由统一算法 _BANDS 在下方以线稿画出（无填充，虚实线表遮挡）。
#   旧画法（襟缘斜弦贯通到摆＋平行领条内缘＋颈口三角/梯形）已随主图一并移除。
_D0 = Y_FOLD - DY                                 # 领口深（肩线→DD′）
s.append('<g id="NECK_FLAT" stroke="%s" stroke-width="3.6" fill="none">' % RED)
if _NECK == "ec":
    for sx in (-1, 1):                            # 领口两侧边 P→D / P′→D′
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
            FX(sx * SLIT_HALF), FY(0), FX(sx * DX), FY(_D0)))
else:
    # 变体（第①步）：平铺的左片也＝右片镜像——右片斜线 P′→O，左片由同一份点镜像（P→O）。
    #   主图布面点 (x,y) → 平铺深度 d=Y_FOLD−y（P/P′→0，O→Y_FOLD＝摆），x 不变。
    for _lap in (_LAPEL_R, _LAPEL_L):
        _flat_lap = " ".join("%s %.1f %.1f" % ("M" if _i == 0 else "L",
                                               FX(_p[0]), FY(Y_FOLD - _p[1]))
                             for _i, _p in enumerate(_lap))
        s.append('  <path d="%s"/>' % _flat_lap)
s.append('</g>')
s.append('<g id="CENTER" stroke="%s" fill="none">' % BLACK)
if _NECK == "ec":
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="3.6"/>' % (
        FX(-DX), FY(_D0), FX(DX), FY(_D0)))        # DD′（领口封口线，仅矩领）
s.append('  <path d="M %.1f %.1f L %.1f %.1f" stroke-width="1.8" stroke-dasharray="26 14"/>' % (
    FX(0), FY(0), FX(0), FY(L_BODY + SHANG_H)))    # 中缝（虚线，保留）
s.append('</g>')
# 领条线稿（平铺，同步③统一算法 v2）：无填充、纯线条；遮挡关系用虚实线——
#   肩段（向外过肩＝转到背面）的自由缘与肩角缝＝虚线；其余（正面）实线。
def _poly_flat(pts):
    _ps = " ".join("%.1f,%.1f" % (FX(p[0]), FY(Y_FOLD - p[1])) for p in pts)
    s.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="2.2"/>' % (_ps, GREEN))
def _line_flat(a, b, dash=False, w=2.2):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"%s stroke="%s" stroke-width="%.1f" fill="none"/>' % (
        FX(a[0]), FY(Y_FOLD - a[1]), FX(b[0]), FY(Y_FOLD - b[1]),
        ' stroke-dasharray="14 10"' if dash else '', GREEN, w))
if _NECK == "ec":                              # 矩领（EC 交叉版）才画领条线稿
    s.append('<g id="COLLAR_BAND_FLAT" fill="none">')
    for _bd in _BANDS:
        for _a, _b in _bd["free"]:
            _line_flat(_a, _b)                          # 自由缘（正面实线）
        for _a, _b in _bd["seams"]:
            _line_flat(_a, _b)                          # 45° 折转缝（正面实线）
    for _a, _b in _SHOULDER["free"]:
        _line_flat(_a, _b, dash=True)                   # 肩段自由缘：转到背面＝虚线
    for _a, _b in _SHOULDER["seams"]:
        _line_flat(_a, _b, dash=True)                   # 肩角缝：连背面＝虚线
    s.append('</g>')

if _NECK == "arc_po":
    # ── 平铺：古制通用上领（照 V3 同款：内缘平行线 ＋ 颈口「前片两三角＋后片梯形」）───────
    #   平铺坐标：x 不变，深度 d = Y_FOLD − y（肩线 d=0，摆 d=Y_FOLD）；肩线上方 d<0 ＝ 翻到背面。
    #   ★原「端边扫掠 70mm 领带」（蓝斜纹填充带/脊线/端边封口）已按要求整块删除。
    def _fd(p):
        return (FX(p[0]), FY(Y_FOLD - p[1]))

    # ① 领条内缘（细黑）：与襟缘平行的等宽带外沿，自颈侧点内让到摆上
    s.append('<g id="LAPEL_INNER_FLAT" stroke="%s" stroke-width="1.8" fill="none">' % BLACK)
    for _inr in (_INNER_R, _INNER_L):
        s.append('  <path d="%s"/>' % " ".join(
            "%s %.1f %.1f" % ("M" if _i == 0 else "L", *_fd(_q)) for _i, _q in enumerate(_inr)))
    s.append('</g>')
    # 续衽三角形（平铺）：内襟 O-H′-F′ 与外襟 O-H-F 各一份，淡橙＋橙线
    s.append('<g id="XURAN_FLAT">')
    for _tri in (_XUR_L, _XUR_R):
        _XURF = "M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (
            *_fd(_tri[0]), *_fd(_tri[1]), *_fd(_tri[2]))
        s.append('  <path d="%s" fill="%s" stroke="none"/>' % (_XURF, _XUR_FILL))
        s.append('  <path d="%s" stroke="%s" stroke-width="2.6" fill="none"/>' % (_XURF, ORANGE))
    s.append('</g>')

    # ② 颈口转折（黑实线）：PB ＝ 内缘在颈口的起点；M ＝ 顶角（±NTH，肩线上方 NECK_H）
    _PBX = SLIT_HALF + N_X * _LS_W                 # PB.x（右襟）
    _PBY = -N_Y * _LS_W                            # PB 深度（负数＝肩线上方）
    s.append('<g id="COLLAR_NECK" stroke="%s" stroke-width="3" fill="none">' % BLACK)
    for _sx in (-1, 1):                            # 前片三角 {P, PB, M}
        s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
            FX(_sx * SLIT_HALF), FY(0), FX(_sx * _PBX), FY(_PBY),
            FX(_sx * NTH), FY(-NECK_H)))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (   # 后片梯形
        FX(-SLIT_HALF), FY(0), FX(-NTH), FY(-NECK_H), FX(NTH), FY(-NECK_H), FX(SLIT_HALF), FY(0)))
    s.append('</g>')

    # ③ H、F 两点（第④步按参考图量角确立；平铺同标）
    s.append('<g id="HF_FLAT" stroke="%s" stroke-width="2.8" fill="none">' % PURPLE)
    for _p in (_H_PT, _F_PT, _H_M_PT, _F_M_PT):
        _cx, _cy = FX(_p[0]), FY(Y_FOLD - _p[1])
        s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
                 '<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (
                     _cx - 12, _cy - 12, _cx + 12, _cy + 12, _cx - 12, _cy + 12, _cx + 12, _cy - 12,
                     _cx, _cy, PURPLE))
    s.append('</g>')
    s.append('<g id="HF_LINE_FLAT" stroke="%s" stroke-width="2.4" fill="none">' % PURPLE)
    for _a, _b in ((_H_PT, _F_PT), (_H_M_PT, _F_M_PT)):
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
            FX(_a[0]), FY(Y_FOLD - _a[1]), FX(_b[0]), FY(Y_FOLD - _b[1])))
    s.append('</g>')
    s.append('<g font-family="sans-serif" font-size="28" font-weight="600" fill="%s">' % PURPLE)
    s.append('  <text x="%.1f" y="%.1f">H</text>' % (FX(_H_PT[0]) + 14, FY(Y_FOLD - _H_PT[1]) - 16))
    s.append('  <text x="%.1f" y="%.1f">H′</text>' % (FX(_H_M_PT[0]) - 46, FY(Y_FOLD - _H_M_PT[1]) - 16))
    s.append('  <text x="%.1f" y="%.1f">F</text>' % (FX(_F_PT[0]) + 20, FY(Y_FOLD - _F_PT[1]) + 10))
    s.append('  <text x="%.1f" y="%.1f">F′</text>' % (FX(_F_M_PT[0]) - 52, FY(Y_FOLD - _F_M_PT[1]) + 10))
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

# （尺寸标注数字与平铺标题文字移除；版型几何线保留）
_CLIP_NOTE = "｜⚠裳高已截到布幅上限（衣长按可容纳范围输出）" if HEM_CLIP else ""

# ── ④ 领条裁片 ────────────────────────────────────────────────────
s.append('<g id="CUT" stroke="%s" stroke-width="3" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>' % (
    MARGIN, COLLAR_OY, MARGIN + _LEAD_LEN, COLLAR_OY,
    MARGIN + _LEAD_LEN, COLLAR_OY + COLLAR_W, MARGIN, COLLAR_OY + COLLAR_W))
if _NECK == "arc_po":                            # 刀口（仅 V4B：F 处与 P′/P 处，上下各一组）
    for _nx in _LEAD_NOTCH + [_LEAD_LEN - _nx for _nx in _LEAD_NOTCH]:
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (
            MARGIN + _nx, COLLAR_OY + 18, MARGIN + _nx, COLLAR_OY + COLLAR_W - 18))
s.append('</g>')
# （领条裁片标题文字移除）

# ── 图内文字（小节标题＋关键尺寸；仅 arc_po，保 ec 输出不变）───────────────
if _NECK == "arc_po":
    _HF_L = math.dist(_H_PT, _F_PT)
    _FP_L = math.dist(_F_PT, (SLIT_HALF, Y_FOLD))
    # ① 折布图
    _txt(MARGIN, MAIN_OY - 26,
         "① 折布图：4 幅 ×（上衣段 %.0f 水平对折 ＋ 裳段 %.0f）" % (2 * L_BODY, SHANG_H), 30, BLACK, "600")
    _rx = MAIN_OX + HALF_S + 95
    _txt(_rx, Y(Y_FOLD) + 8, "肩线（对折线）", 24, "#3a3a3a")
    _txt(_rx, Y(Y_WAIST) + 8, "腰线（衣裳接缝）", 24, "#3a3a3a")
    _txt(_rx, Y(0) + 10, "摆（下摆）", 24, "#3a3a3a")
    # ③ 平铺
    _txt(MARGIN, FTOP - 26,
         "③ 平铺（正面）：P/P′ 颈侧点｜O 下摆中点｜H/H′ 续衽下角｜F/F′ 领条分界（与腋点同高）", 30, BLACK, "600")
    _txt(MAIN_OX + HEM_HALF + 60, FTOP + FLAT_H + 40, "下摆", 24, "#3a3a3a")
    _ny = FTOP + FLAT_H * 0.30
    _nx = MAIN_OX + ARMPIT + 120
    _txt(_nx, _ny, "续衽（左右各一片）：", 24, ORANGE, "600")
    _txt(_nx, _ny + 32, "OH %.0f｜OF %.1f｜HF %.1f" % (
        abs(_H_PT[0] - _O_PT[0]), math.dist(_O_PT, _F_PT), _HF_L), 24, ORANGE)
    _txt(_nx, _ny + 64, "上领路线 H→F→P′（内襟 H′→F′→P 镜像）", 22, "#4a4a4a")
    _txt(_nx, _ny + 94, "开领宽 %.0f｜领宽 %.0f｜F 高 %.0f" % (NECK_W, COLLAR_W, _F_PT[1]), 22, "#4a4a4a")
    # ④ 领条裁片
    _txt(MARGIN, COLLAR_OY - 26,
         "④ 领条裁片 ×1：长 %.1f × 宽 %.0f（按上领路线展开）" % (_LEAD_LEN, COLLAR_W), 30, BLACK, "600")
    _txt(MARGIN, COLLAR_OY + COLLAR_W + 42,
         "刀口：距左端 %.1f（F）与 %.1f（P′）；右端对称（F′、P）" % (_HF_L, _HF_L + _FP_L), 24, "#4a4a4a")

# ── 100mm 标尺 ────────────────────────────────────────────────────
# （标尺文字移除，保留标尺刻度线）
bx0, by0 = MARGIN, TOTAL_H - 100
s.append('<g id="SCALE" stroke="%s" stroke-width="2.4" fill="none">' % BLACK)
for k in range(11):
    hh = 30 if k % 5 == 0 else 16
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0 + k * 100, by0, bx0 + k * 100, by0 - hh))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx0, by0, bx0 + 1000, by0))
if _NECK == "arc_po":
    _txt(bx0 + 1020, by0 + 8, "100 mm（每格 100，粗格 500）", 22, "#3a3a3a")
s.append('</g>')

s.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" '
         'orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.6"/></marker></defs>' % GRAY)
s.append('</svg>')

HERE = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("HANFU_OUT"):
    fp = os.environ["HANFU_OUT"]
else:
    fp = os.path.join(HERE, "深衣_V4_新领口.svg")
open(fp, "w", encoding="utf-8").write("\n".join(s))

json.dump({
    "params": P,
    "resolved": {"S": S, "HALF_S": HALF_S, "CLOTH_H": CLOTH_H,
                 "SEG_MID": SEG_MID, "SEG_OUT": SHANG_H, "Y_WAIST": Y_WAIST, "GARMENT_L": L_BODY + SHANG_H,
                 "Y_SEG1": Y_SEG1, "Y_FOLD": Y_FOLD, "Y_SEG2": Y_SEG2,
                 "L_BODY": L_BODY, "SHANG_H": SHANG_H, "ARMPIT": ARMPIT,
                 "ARMPIT_H": ARMPIT_H, "HOOK_H": HOOK_H, "HOOK_OUT": HOOK_OUT,
                 "HEM_HALF": HEM_HALF, "HEM_CLIP": HEM_CLIP, "COLLAR_L": COLLAR_L,
                 "PD": PD, "DX": DX, "DY": DY, "D1_X": D1_X, "LAPEL_W": LL_W, "DO_W": DO_W,
                 "LEAD_LEN": _LEAD_LEN, "LEAD_NOTCH": _LEAD_NOTCH,
                 "NECK_MODE": _NECK, "COLLAR_W": COLLAR_W,
                 "H_X": float(P.get("H_X", -ARMPIT)), "ARM_Y": Y_WAIST + ARMPIT_H},
    "canvas": [CANVAS_W, TOTAL_H],
}, open(fp.rsplit(".", 1)[0] + ".pieces.json", "w", encoding="utf-8"),
   ensure_ascii=False, indent=1)

print(json.dumps({"file": fp, "canvas": [CANVAS_W, round(TOTAL_H, 1)],
                  "S": S, "CLOTH_H": CLOTH_H, "SEG_MID": SEG_MID, "SEG_OUT": round(SHANG_H, 1),
                  "L_BODY": L_BODY, "SHANG_H": round(SHANG_H, 1),
                  "ARMPIT": ARMPIT, "ARMPIT_H": round(ARMPIT_H, 1), "COLLAR_L": COLLAR_L,
                  "LEAD_LEN": round(_LEAD_LEN, 1)},
                 ensure_ascii=False))
