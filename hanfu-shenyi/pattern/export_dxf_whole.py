# -*- coding: utf-8 -*-
"""通裁 · 整衣铺开一片 DXF（方案 B：一条连续闭合外轮廓 + 标注）
────────────────────────────────────────────────────────────────
口径（2026-11-02 与用户对齐后重写，替代已删除的旧版）：
  · 外轮廓 = 一条连续闭合线：裳·后(3幅) + 衣(4幅,中段对折) + 裳·前(3幅)，
    腰线处因裳(3幅)窄于布片(4幅)而内收成台阶 —— 不是"两片各自闭合"。
  · 前中 = 剪开贯通开口：±SLIT_HALF 两道剪开、中间一条 160 宽直边缺口挖掉，
    两襟各自独立可滑动（"左右衣襟活动"）；开口从肩线贯通到裳摆。
  · 几何里没有"交"：交襟是穿法（两襟交叠着系，交叠量决定上身领形），只进标注。
  · 裳收褶：真实存在，但 DXF 不画褶线，只在标注里写差值（由幅宽推算）。
  · 领条 = 直条另裁（压边可见 40，绕颈后连成一条）；后领不是折出来的部件。
  · 不新增任何尺寸：全部取自 build_shenyi.py 的 DEF / HANFU_PARAMS；
    唯一补充 N_SHANG=3（裳每片 3 幅）—— 剪裁图实测：上/下块 168..477，
    中带 111..519，内缩 57px ≈ 半幅（fig_深衣_剪裁与平铺.jpg）。
用法：
  python export_dxf_whole.py            # 默认 V3 窄袖
  HANFU_PARAMS='{"L_BODY":624,"GARMENT_L":1872}' python export_dxf_whole.py
输出：out/整衣_<名称>.dxf + out/整衣_<名称>_preview.svg/.png（交付前必须自己看过）
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# ── 参数：与 build_shenyi.py 同一套 DEF（勿在此另立数值）──────────────
_DEF = dict(
    FAB_W=500.0, N_PANEL=4, L_BODY=195.0, GARMENT_L=770.0,
    SLIT_HALF=80.0, LAPEL_FOLD=40.0, COLLAR_W=95.0,
    NECK_TOP_HALF=44.5, NECK_H=77.0,
    ARMPIT=370.0, ARMPIT_H=200.0, HOOK_OUT=60.0, HOOK_H=70.0,
    N_SHANG=2,           # 裳每片幅数（用户 2026-11-04 定 2 幅）
)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

FAB_W = P["FAB_W"]; N = int(P["N_PANEL"]); NS = int(P["N_SHANG"])
L_BODY = P["L_BODY"]; SHANG_H = P["GARMENT_L"] - L_BODY
SLIT = P["SLIT_HALF"]; LFLD = P["LAPEL_FOLD"]
COLLAR_W = P["COLLAR_W"]; NTH = P["NECK_TOP_HALF"]; NH = P["NECK_H"]
ARP = P["ARMPIT"]; ARP_H = P["ARP_H" if "ARP_H" in P else "ARMPIT_H"] * (L_BODY / 624.0)
HK_H = P["HOOK_H"] * (L_BODY / 624.0)   # 挖弧矢高（弧的腰线端已实测改落在幅缝 ±FAB_W）

S = FAB_W * N / 2.0            # 布片半宽 1000
SH = FAB_W * NS / 2.0          # 裳半宽 750
SEG_MID = 2 * L_BODY
W1 = SHANG_H                   # 前腰线（衣带下边）
F = SHANG_H + L_BODY           # 肩线（对折线）
W2 = SHANG_H + SEG_MID         # 后腰线（衣带上边）
H = W2 + SHANG_H               # 布片总高
COLLAR_L = 2 * (L_BODY + SHANG_H) + SLIT * 2
SLIT_W = SLIT * 2

NAME = ("V2宽袖" if abs(L_BODY - 624) < 1 else
        "V3窄袖" if abs(L_BODY - 195) < 1 else
        "自定义_L%d" % round(L_BODY))
_ho = os.environ.get("HANFU_OUT")
if _ho and _ho.lower().endswith(".dxf"):
    DST = _ho; OUTDIR = os.path.dirname(_ho)
elif _ho:
    OUTDIR = _ho; DST = os.path.join(OUTDIR, "整衣_%s.dxf" % NAME)
else:
    OUTDIR = os.path.join(ROOT, "out"); DST = os.path.join(OUTDIR, "整衣_%s.dxf" % NAME)
os.makedirs(OUTDIR, exist_ok=True)

# ── 几何（衣片坐标：x 右正、y 上正、原点=布片下边中点）────────────────
outline = [(-SH, 0), (-SLIT, 0), (-SLIT, F), (SLIT, F), (SLIT, 0), (SH, 0),
           (SH, W1), (S, W1), (S, W2), (SH, W2), (SH, H), (-SH, H),
           (-SH, W2), (-S, W2), (-S, W1), (-SH, W1)]

seams = []   # 拼幅缝（衣带 ±FAB_W；裳块 ±FAB_W；背中缝 x=0 自肩线到顶）
for k in range(1, N):
    x = -S + FAB_W * k
    if abs(x) < 1:                       # 中缝单独画（背中缝）
        continue
    seams.append(((x, W1), (x, W2)))
for k in range(1, NS):
    x = -SH + FAB_W * k
    seams.append(((x, 0), (x, W1)))      # 裳·前
    seams.append(((x, W2), (x, H)))      # 裳·后
seams.append(((0, F), (0, H)))           # 背中缝（竖，肩线以上）

fold = [((-S, F), (-SLIT, F)), ((SLIT, F), (S, F))]      # 折线（中段正中=肩线）
cutline = [((-SLIT, 0), (-SLIT, F)), ((SLIT, 0), (SLIT, F))]  # 前中两道剪开
# ── 腰线与袖底：衣、裳分开想（关键）────────────────────────────────
#   衣（一块布）：底边 ±ARP 以内是「衣身摆线」（接收褶的裳），±(ARP+HOOK_OUT) 以外是
#   「袖底缝」（与镜像缝合）。裳（另一块布）：腰边 1500(3幅)，比 740 宽，差值收褶吃掉。
#   两片布的线各归各，互不抢地盘；腰线(±750)在排料图里同时是「裳/衣分界＝下剪线」。
# 腰线＝裳/衣分界（下剪线；缝合时收褶）。前腰线在前中 ±SLIT 处断开——那里布已挖掉。
waist = [((-SH, W1), (-SLIT, W1)), ((SLIT, W1), (SH, W1)), ((-SH, W2), (SH, W2))]
sleeve = []; hooks = []                                   # 袖底缝(衣) + 侧缝垂线记号(衣) + 腋下挖弧
def hook_pts(sx, yy, d):
    """腋下挖弧（剪裁图实测）：自幅缝脚 (±FAB_W, yy) 沿腰线向内，向「中段内侧」（肩线方向）
    弯到躯干边缘记号 (±ARP, yy+d*HK_H)。d=+1 前片向折线上弯，d=-1 后片向下弯。
    弧与腰线之间那块小角＝腋下敞口（侧视倒 U），不缝。"""
    xa, xf = sx * ARP, sx * FAB_W
    y0 = yy; yb = yy + d * HK_H
    c1 = (xa, yb + 0.45 * (y0 - yb))
    c2 = (xa + 0.55 * (xf - xa), y0)
    return [((1-t)**3*xa + 3*(1-t)**2*t*c1[0] + 3*(1-t)*t*t*c2[0] + t**3*xf,
             (1-t)**3*yb + 3*(1-t)**2*t*c1[1] + 3*(1-t)*t*t*c2[1] + t**3*y0)
            for t in (i / 16.0 for i in range(17))]
for yy in (W1, W2):
    d = 1 if yy == W1 else -1          # 前片向折线上弯，后片向下弯（都在中段内侧）
    for sx in (-1, 1):
        sleeve.append(((sx * FAB_W, yy), (sx * S, yy)))                   # 袖底缝：幅缝→袖口
        sleeve.append(((sx * ARP, yy), (sx * ARP, yy + d * ARP_H)))       # 侧缝垂线记号（衣）
        hooks.append(hook_pts(sx, yy, d))                                 # 挖弧（折线近似）
band = [((-SLIT, F), (-LFLD, F)), ((SLIT, F), (LFLD, F))]  # 领条压边（可见宽）
band_tab = [(-SLIT, F), (-NTH, F + NH), (NTH, F + NH), (SLIT, F)]  # 领条折转段(梯形)
grain = []
for k in range(N):
    cx = -S + FAB_W * (k + .5)
    grain.append(((cx, W1 + 120), (cx, W2 - 120)))
for k in range(NS):
    cx = -SH + FAB_W * (k + .5)
    if abs(cx) < SLIT:                # 前中 ±80 挖空区不画布纹
        grain.append(((cx, W2 + 120), (cx, H - 120)))
        continue
    grain.append(((cx, 120), (cx, W1 - 120)))
    grain.append(((cx, W2 + 120), (cx, H - 120)))
notches = [(sx * ARP, yy + d * ARP_H)                       # 腋点刀口（垂线末端，中段内侧）
           for yy, d in ((W1, 1), (W2, -1)) for sx in (-1, 1)]

collar = [(S + 300, 0), (S + 300 + COLLAR_L, 0),
          (S + 300 + COLLAR_L, COLLAR_W), (S + 300, COLLAR_W)]

ANN = [
    "通袖 %d ＝ %d 幅 × %.0f ｜ 布片高 %d ＝ 中段 %d（对折＝上衣，衣长 %d＝袖口）＋ 裳 %d × 2" % (
        round(S * 2), N, FAB_W, round(H), round(SEG_MID), round(L_BODY), round(SHANG_H)),
    "裳·前 / 裳·后：另一块布（同料），各 %d 幅宽，缝于腰线（衣身接缝）→ 缝合成深衣" % NS,
    "前中开口 %d 贯通到摆：两襟独立可滑（左右衣襟活动）；交襟＝系出来的，几何里没有'交'" % round(SLIT_W),
    "领条压边可见 %d（中间露出后片 %d）；领条另裁 %d × %d，直条绕颈后" % (
        round(LFLD), round(SLIT_W - LFLD * 2), round(COLLAR_L), round(COLLAR_W)),
    "外轮廓各段角色：裳摆=自由边 ｜ 裳两侧=侧缝(与镜像缝合) ｜ 腰线台阶段(±%d~%d)=袖底缝(与镜像缝合) "
    "｜ ±%d=袖口(自由) ｜ ±%d=前中剪开 ｜ 肩线=折线" % (
        round(SH), round(S), round(S), round(SLIT)),
    "衣裳分开：衣底边 ±%d 以内＝衣身摆线（接收褶的裳：裳腰 %d 收褶接 %d，比≈2:1，推算）；"
    "幅缝 ±%d 到袖口 ±%d＝袖底缝（与镜像缝合，沿外幅整条）；本图不画褶线" % (
        round(ARP), round(SH * 2), round(ARP * 2), round(FAB_W), round(S)),
    "净版未含缝份 ｜ 单位 mm ｜ 裳半宽 %d ＜ 布片半宽 %d → 腰线处台阶（剪裁图实测上/下块各 %d 幅）" % (
        round(SH), round(S), NS),
]

# ── 写 DXF ─────────────────────────────────────────────────────────
def write_dxf():
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    LAYERS = [("CUT_轮廓", 7), ("SEAM_拼缝", 5), ("FOLD_折线", 30), ("CUTLINE_剪开", 1),
              ("BAND_领条", 3), ("NOTCH_刀口", 1), ("GRAIN_布纹", 8),
              ("TEXT_文字", 7), ("DIM_标注", 4)]
    for nm, c in LAYERS:
        doc.layers.add(nm, color=c)
    doc.styles.add("CN", font="simsun.ttc")
    msp = doc.modelspace()
    OX, OY = 200.0, 200.0                       # 图形原点在 CAD 里的落位
    C = lambda p: (p[0] + OX, p[1] + OY)

    msp.add_lwpolyline([C(p) for p in outline], close=True, dxfattribs={"layer": "CUT_轮廓"})
    msp.add_lwpolyline([C(p) for p in collar], close=True, dxfattribs={"layer": "CUT_轮廓"})

    for a, b in seams + waist + sleeve:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "SEAM_拼缝"})
    for pts in hooks:
        msp.add_lwpolyline([C(q) for q in pts], dxfattribs={"layer": "SEAM_拼缝"})
    for a, b in fold + band:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "FOLD_折线"})
    for a, b in cutline:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "CUTLINE_剪开"})
    msp.add_lwpolyline([C(p) for p in band_tab], dxfattribs={"layer": "BAND_领条"})
    for a, b in grain:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "GRAIN_布纹"})
    for (x, y) in notches:
        for d in ((-12, -12), (-12, 12)):
            msp.add_line(C((x + d[0], y + d[1])), C((x - d[0], y - d[1])),
                         dxfattribs={"layer": "NOTCH_刀口"})

    ty = H + 260
    msp.add_text("通裁 · 整衣铺开一片（%s）｜ 一条连续外轮廓：裳后 + 衣(中段对折) + 裳前" % NAME,
                 height=48, dxfattribs={"layer": "TEXT_文字", "style": "CN"}
                 ).set_placement((OX - 100, OY + ty + 190), align=TextEntityAlignment.LEFT)
    for i, t in enumerate(ANN):
        msp.add_text(t, height=32, dxfattribs={"layer": "TEXT_文字", "style": "CN"}
                     ).set_placement((OX - 100, OY + ty + 120 - i * 55),
                                     align=TextEntityAlignment.LEFT)
    msp.add_text("领条 ×1（另裁）", height=32, dxfattribs={"layer": "TEXT_文字", "style": "CN"}
                 ).set_placement((C(collar[0])[0], C(collar[3])[1] + 30),
                                 align=TextEntityAlignment.LEFT)
    # 100mm 标尺
    x0, y0 = OX, OY - 160
    msp.add_line((x0, y0), (x0 + 1000, y0), dxfattribs={"layer": "DIM_标注"})
    for k in range(11):
        hh = 26 if k % 5 == 0 else 14
        msp.add_line((x0 + k * 100, y0), (x0 + k * 100, y0 + hh), dxfattribs={"layer": "DIM_标注"})
    doc.saveas(DST)
    return len(outline), (2 * S + 400 + COLLAR_L, H)


# ── 预览 SVG（交付前必须自己看过：白底、线宽随画幅、无遮挡）──────────
def write_svg(path):
    W = 250 + (S + 300 + COLLAR_L) + S + 120      # 右端要容下领条（x 平移量 250+S）
    Hh = H + 700
    k = max(W, Hh) / 2600.0 * 1.6
    COL = {"CUT_轮廓": ("#111111", 2.6, ""),
           "SEAM_拼缝": ("#1a4d8f", 1.4, ' stroke-dasharray="26 10"'),
           "FOLD_折线": ("#b85400", 2.2, ' stroke-dasharray="46 16 10 16"'),
           "CUTLINE_剪开": ("#b3241c", 2.6, ""),
           "BAND_领条": ("#1d6b3a", 1.8, ' stroke-dasharray="18 12"'),
           "NOTCH_刀口": ("#b3241c", 1.6, ""),
           "GRAIN_布纹": ("#8a8a8a", 1.1, "")}
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
         % (int(W * 0.62), int(Hh * 0.62), W, Hh),
         '<rect width="100%" height="100%" fill="#ffffff"/>']
    Y = lambda y: 520 + (H - y)                       # 翻到屏幕坐标
    P2 = lambda p: (250 + (p[0] + S), Y(p[1]))        # x 平移到画布内

    def seg(a, b, layer):
        c, w, extra = COL[layer]
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.2f" fill="none"%s/>'
                 % (P2(a)[0], P2(a)[1], P2(b)[0], P2(b)[1], c, w * k, extra))

    def poly(pts, layer, dash=""):
        c, w, _ = COL[layer]
        d = " ".join("%g %g" % P2(p) for p in pts)
        o.append('<polyline points="%s" stroke="%s" stroke-width="%.2f" fill="none"%s%s/>'
                 % (d, c, 2.6 * k, dash, ' stroke-linejoin="round"'))

    poly(outline, "CUT_轮廓")
    poly(collar, "CUT_轮廓")
    for a, b in seams + waist + sleeve: seg(a, b, "SEAM_拼缝")
    for pts in hooks: poly(pts, "SEAM_拼缝")
    for a, b in fold + band: seg(a, b, "FOLD_折线")
    for a, b in cutline: seg(a, b, "CUTLINE_剪开")
    poly(band_tab, "BAND_领条")
    for a, b in grain: seg(a, b, "GRAIN_布纹")
    for (x, y) in notches:
        px, py = P2((x, y))
        o.append('<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="%.2f"/>'
                 % (px - 8, py - 8, px + 8, py + 8, px - 8, py + 8, px + 8, py - 8,
                    COL["NOTCH_刀口"][0], 1.6 * k))
    o.append('<g font-family="sans-serif" fill="#111111">')
    o.append('<text x="60" y="70" font-size="42" font-weight="600">通裁 · 整衣铺开一片（%s）｜ 一条连续外轮廓：裳后 + 衣(中段对折) + 裳前</text>' % NAME)
    for i, t in enumerate(ANN):
        o.append('<text x="60" y="%d" font-size="27" fill="#444444">%s</text>' % (130 + i * 44, t))
    o.append('<text x="%g" y="%g" font-size="28">领条 ×1（另裁）</text>' % (P2(collar[0])[0], P2(collar[3])[1] - 14))
    o.append('</g>')
    o.append('<text x="60" y="%d" font-size="24" fill="#8a8a8a">预览：CUT 黑 / 拼缝·腰线·袖底 蓝虚 / 折线·压边 橙点划 / 剪开 红 / 领条 绿 / 布纹 灰</text>' % (Hh - 30))
    o.append('</svg>')
    open(path, "w", encoding="utf-8").write("\n".join(o))
    return W, Hh


if __name__ == "__main__":
    nv, size = write_dxf()
    svg = DST.replace(".dxf", "_preview.svg")
    W, Hh = write_svg(svg)
    print(json.dumps({"dxf": DST, "png": DST.replace(".dxf", "_preview.png"),
                      "outline_pts": nv, "cad_box_mm": [round(size[0]), round(size[1])],
                      "preview_svg": svg, "resolved": {
                          "S": S, "SH": SH, "W1": W1, "F": F, "W2": W2, "H": H,
                          "L_BODY": L_BODY, "SHANG_H": SHANG_H, "COLLAR_L": COLLAR_L}},
                     ensure_ascii=False))
    try:
        from preview import render
        render(svg, DST.replace(".dxf", "_preview.png"), scale=0.62)
    except Exception as e:
        print("预览 PNG 失败（SVG 已出）：", e)
