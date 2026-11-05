# -*- coding: utf-8 -*-
"""通裁 · V1 原始直领交襟衣 · 整衣铺开一片 DXF（方案 B）
────────────────────────────────────────────────────────────────
V1 无裳：整衣＝一块布（通袖 2000＝4 幅 × 500，高＝对折线×2），
  肩线在对折线（不剪），前中开口 ±80 贯通到下摆（两襟可滑），领条直条另裁绕颈后。
  袖＝布的两个端头；袖底缝＝幅缝(±500)到袖口(±1000)，与镜像缝合（与深衣同构）。
  几何里没有"交"；数值全部取自 pattern/build.py 的 DEF / HANFU_PARAMS，不新增尺寸。
用法：python export_dxf_whole_v1.py（或 studio 产物下拉/导出自动调用）
输出：整衣_V1直领交襟.dxf + 预览 svg/png（交付前必须自己看过）
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

_DEF = dict(FAB_W=500.0, N_PANEL=4, HALF_L=624.0,
            SLIT_HALF=80.0, LAPEL_FOLD=40.0,
            COLLAR_L=2000.0, COLLAR_W=95.0,
            NECK_TOP_HALF=44.5, NECK_H=77.0)
P = dict(_DEF)
P.update(json.loads(os.environ.get("HANFU_PARAMS", "{}")))

FAB_W = P["FAB_W"]; N = int(P["N_PANEL"])
L = P["HALF_L"]; SLIT = P["SLIT_HALF"]; LFLD = P["LAPEL_FOLD"]
COLLAR_L = P["COLLAR_L"]; COLLAR_W = P["COLLAR_W"]
NTH = P["NECK_TOP_HALF"]; NH = P["NECK_H"]

S = FAB_W * N / 2.0            # 布片半宽 1000
H = L * 2                      # 布片总高
F = L                          # 对折线＝肩线
SLIT_W = SLIT * 2

NAME = "V1直领交襟"
_ho = os.environ.get("HANFU_OUT")
if _ho and _ho.lower().endswith(".dxf"):
    DST = _ho; OUTDIR = os.path.dirname(_ho)
elif _ho:
    OUTDIR = _ho; DST = os.path.join(OUTDIR, "整衣_%s.dxf" % NAME)
else:
    OUTDIR = os.path.join(ROOT, "out"); DST = os.path.join(OUTDIR, "整衣_%s.dxf" % NAME)
os.makedirs(OUTDIR, exist_ok=True)

# ── 几何（布片坐标：x 右正、y 上正、原点＝布片下边中点）────────────────
outline = [(-S, 0), (-SLIT, 0), (-SLIT, F), (SLIT, F), (SLIT, 0), (S, 0),
           (S, H), (-S, H)]
seams = []
for k in range(1, N):
    x = -S + FAB_W * k
    if abs(x) < 1:
        seams.append(((0, F), (0, H)))       # 背中缝（肩线以上）
        continue
    seams.append(((x, 0), (x, H)))           # 拼幅缝（通高）
fold = [((-S, F), (-SLIT, F)), ((SLIT, F), (S, F))]
cutline = [((-SLIT, 0), (-SLIT, F)), ((SLIT, 0), (SLIT, F))]
sleeve = []                                   # 袖底缝：幅缝→袖口（前后片缝合）
for yy in (0, H):
    for sx in (-1, 1):
        sleeve.append(((sx * FAB_W, yy), (sx * S, yy)))
band = [((-SLIT, 0), (-LFLD, 0)), ((SLIT, 0), (LFLD, 0)),
        ((-SLIT, F), (-LFLD, F)), ((SLIT, F), (LFLD, F))]
band_tab = [(-SLIT, F), (-NTH, F + NH), (NTH, F + NH), (SLIT, F)]
grain = []
for k in range(N):
    cx = -S + FAB_W * (k + 0.5)
    grain.append(((cx, 120), (cx, H - 120)))
collar = [(S + 300, 0), (S + 300 + COLLAR_L, 0),
          (S + 300 + COLLAR_L, COLLAR_W), (S + 300, COLLAR_W)]

ANN = [
    "通袖 %d ＝ %d 幅 × %.0f ｜ 布片高 %d ＝ 对折线 ×2（衣长 %d ＝ 肩线到下摆）" % (
        round(S * 2), N, FAB_W, round(H), round(L)),
    "上下对折（肩线折出，不另裁前后片）→ 前中剪开两道（不折），领条压边",
    "前中开口 %d 贯通到下摆：两襟独立可滑（左右衣襟活动）；交襟＝系出来的，几何里没有'交'" % round(SLIT_W),
    "领条压边可见 %d（中间露出后片 %d）；领条另裁 %d × %d，直条绕颈后" % (
        round(LFLD), round(SLIT_W - LFLD * 2), round(COLLAR_L), round(COLLAR_W)),
    "袖底缝：幅缝 ±%d 到袖口 ±%d（与镜像缝合，沿外幅整条）；幅缝 ±%d＝拼幅缝" % (
        round(FAB_W), round(S), round(FAB_W)),
    "净版未含缝份 ｜ 单位 mm ｜ 本件无裳（上衣下裳另接）",
]


def write_dxf():
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    for nm, c in (("CUT_轮廓", 7), ("SEAM_拼缝", 5), ("FOLD_折线", 30), ("CUTLINE_剪开", 1),
                  ("BAND_领条", 3), ("GRAIN_布纹", 8), ("TEXT_文字", 7), ("DIM_标注", 4)):
        doc.layers.add(nm, color=c)
    doc.styles.add("CN", font="simsun.ttc")
    msp = doc.modelspace()
    OX, OY = 200.0, 200.0
    C = lambda p: (p[0] + OX, p[1] + OY)
    msp.add_lwpolyline([C(p) for p in outline], close=True, dxfattribs={"layer": "CUT_轮廓"})
    msp.add_lwpolyline([C(p) for p in collar], close=True, dxfattribs={"layer": "CUT_轮廓"})
    for a, b in seams + sleeve:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "SEAM_拼缝"})
    for a, b in fold + band:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "FOLD_折线"})
    for a, b in cutline:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "CUTLINE_剪开"})
    msp.add_lwpolyline([C(p) for p in band_tab], dxfattribs={"layer": "BAND_领条"})
    for a, b in grain:
        msp.add_line(C(a), C(b), dxfattribs={"layer": "GRAIN_布纹"})
    ty = H + 240
    msp.add_text("通裁 · V1 原始直领交襟衣 · 整衣铺开一片（一条连续外轮廓）",
                 height=48, dxfattribs={"layer": "TEXT_文字", "style": "CN"}
                 ).set_placement((OX - 100, OY + ty + 190), align=TextEntityAlignment.LEFT)
    for i, t in enumerate(ANN):
        msp.add_text(t, height=32, dxfattribs={"layer": "TEXT_文字", "style": "CN"}
                     ).set_placement((OX - 100, OY + ty + 120 - i * 55),
                                     align=TextEntityAlignment.LEFT)
    msp.add_text("领条 ×1（另裁）", height=32, dxfattribs={"layer": "TEXT_文字", "style": "CN"}
                 ).set_placement((C(collar[0])[0], C(collar[3])[1] + 30),
                                 align=TextEntityAlignment.LEFT)
    x0, y0 = OX, OY - 160
    msp.add_line((x0, y0), (x0 + 1000, y0), dxfattribs={"layer": "DIM_标注"})
    for k in range(11):
        hh = 26 if k % 5 == 0 else 14
        msp.add_line((x0 + k * 100, y0), (x0 + k * 100, y0 + hh), dxfattribs={"layer": "DIM_标注"})
    doc.saveas(DST)
    return len(outline)


def write_svg(path):
    W = 250 + (S + 300 + COLLAR_L) + S + 120
    Hh = H + 700
    k = max(W, Hh) / 2600.0 * 1.6
    COL = {"CUT_轮廓": ("#111111", 2.6, ""),
           "SEAM_拼缝": ("#1a4d8f", 1.4, ' stroke-dasharray="26 10"'),
           "FOLD_折线": ("#b85400", 2.2, ' stroke-dasharray="46 16 10 16"'),
           "CUTLINE_剪开": ("#b3241c", 2.6, ""),
           "BAND_领条": ("#1d6b3a", 1.8, ' stroke-dasharray="18 12"'),
           "GRAIN_布纹": ("#8a8a8a", 1.1, "")}
    Y = lambda y: 520 + (H - y)
    P2 = lambda p: (250 + (p[0] + S), Y(p[1]))
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
         % (int(W * 0.62), int(Hh * 0.62), W, Hh),
         '<rect width="100%" height="100%" fill="#ffffff"/>']

    def seg(a, b, layer):
        c, w, extra = COL[layer]
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.2f" fill="none"%s/>'
                 % (P2(a)[0], P2(a)[1], P2(b)[0], P2(b)[1], c, w * k, extra))

    def poly(pts, layer):
        c, w, _ = COL[layer]
        d = " ".join("%g %g" % P2(p) for p in pts)
        o.append('<polyline points="%s" stroke="%s" stroke-width="%.2f" fill="none" stroke-linejoin="round"/>'
                 % (d, c, 2.6 * k))

    poly(outline, "CUT_轮廓")
    poly(collar, "CUT_轮廓")
    for a, b in seams + sleeve: seg(a, b, "SEAM_拼缝")
    for a, b in fold + band: seg(a, b, "FOLD_折线")
    for a, b in cutline: seg(a, b, "CUTLINE_剪开")
    poly(band_tab, "BAND_领条")
    for a, b in grain: seg(a, b, "GRAIN_布纹")
    o.append('<g font-family="sans-serif" fill="#111111">')
    o.append('<text x="60" y="70" font-size="42" font-weight="600">通裁 · V1 原始直领交襟衣 · 整衣铺开一片</text>')
    for i, t in enumerate(ANN):
        o.append('<text x="60" y="%d" font-size="27" fill="#444444">%s</text>' % (130 + i * 44, t))
    o.append('<text x="%g" y="%g" font-size="28">领条 ×1（另裁）</text>' % (P2(collar[0])[0], P2(collar[3])[1] - 14))
    o.append('</g>')
    o.append('<text x="60" y="%d" font-size="24" fill="#8a8a8a">预览：CUT 黑 / 拼缝·袖底 蓝虚 / 折线·压边 橙点划 / 剪开 红 / 领条 绿 / 布纹 灰</text>' % (Hh - 30))
    o.append('</svg>')
    open(path, "w", encoding="utf-8").write("\n".join(o))
    return W, Hh


if __name__ == "__main__":
    nv = write_dxf()
    svg = DST.replace(".dxf", "_preview.svg")
    write_svg(svg)
    print(json.dumps({"dxf": DST, "png": DST.replace(".dxf", "_preview.png"),
                      "outline_pts": nv, "resolved": {"S": S, "H": H, "F": F,
                                                      "HALF_L": L, "COLLAR_L": COLLAR_L}},
                     ensure_ascii=False))
    try:
        from preview import render
        render(svg, DST.replace(".dxf", "_preview.png"), scale=0.62)
    except Exception as e:
        print("预览 PNG 失败（SVG 已出）：", e)
