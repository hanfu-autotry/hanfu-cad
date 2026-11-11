# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 第 3 步：连接 P₁P₂ 作为「新领口」，前片左右镜像同步

    python pattern/step3.py
      → out/step3_P1P2连线.svg / .pieces.json / .png
      → out/step3_平铺线稿.svg / .png
      → out/step3.json

用户 2026-11-10 口径：
  ① **P₁P₂ 就是新领口**（语义定名）。
  ② **这整个步骤是前片左右镜像同步的**：前片 ×2 是关于前中缝 x=0 的左右镜像两片，
     新领口在两片上各有一条 —— 右片 P₁→P₂、左片 P₁′→P₂′，平铺线稿左右各画一条。
  ③ **V→P₁ / V→P₂（及镜像片）这两段旧边改为虚线标注**：只改画法，不动 cmds。
  **2026-11-11 11:48 修正**：P₁P₂ 改为**圆心角 60°** 的解析圆弧 —— 用户令
     「P1P2 为圆心角 60 度的弧」。端点 P₁/P₂ 不动、弦长 c=76.5732 不变，
     由 c=2R·sin30° ⇒ **R=c=76.5732mm**（不再是 VP₁=50、圆心不再是 V）；
     圆心在弦中垂线上由弦心距 d=R·cos30° 解析确定，取「弧中点 y 较小」一支＝**凹向下摆**。
     右片圆心 (21.967982, 796.154590)、极角 −160.027853°→−100.027853°、扫角精确 60°；
     左片圆心 = 右片关于 x=0 镜像，两段**不共圆**、在中缝 x=0 相交于 y≈722.8002。
     弦 76.5732 / 弧长 80.1873 / 矢高 10.2589 mm。
     裁片 cmds 一处未改；links 里的多点折线只是等角采样（64 段），不是新增控制点。

平铺骨架照搬 `hanfu-zhidui/pattern/flat.py`（正面线稿：白底纯黑、不填色、不做背视）：
  · 外轮廓 ＝ 后片半 ×2 关于后中缝镜像合成整片；
  · 中央 V 形两线 ＝ 前片门襟边（模板原边，未改）；
  · 前片不整片重画，避免与后片轮廓叠乱；
  · 两条新领口**圆弧**（左右镜像同步）叠在 V 形上方。
底＝厂商基准男 M 模板原衣长 L=770（衣长改动已撤销）。前片、后片 cmds 一处未改，
左片只做镜像变换。
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet
from step1 import make_png

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

PAIR = geo.segment_p1p2_pair()
RIGHT, LEFT = PAIR["right"], PAIR["left"]
SEG = RIGHT                      # 右片新领口（主段），兼容第 3 步原有引用
TITLE = "试验竖领浅交襟 · 第 3 步 · P₁P₂ 新领口（圆心角 60° 圆弧）"
SUBTITLE = "底＝hanfu-cad 厂商基准男 M（模板原衣长 770）「前片左右镜像同步 ×2 + 后片半 ×2」只读　｜　净版 mm"
NOTES = [
    "P₁P₂ = 新领口（用户 2026-11-11 11:48 令：圆心角 60° 的弧）；端点 P₁/P₂ 不动、弦长不变 ⇒ R = 弦长 = 76.5732mm",
    "右片弧 P₁(%.2f,%.2f)→P₂(%.2f,%.2f)：弦 %.2f / 弧长 %.2f / 矢高 %.2f mm；圆心 (%.3f, %.3f)、扫角 60°"
    % (RIGHT["P1"][0], RIGHT["P1"][1], RIGHT["P2"][0], RIGHT["P2"][1],
       RIGHT["chord"], RIGHT["arc_length"], RIGHT["sagitta"],
       RIGHT["center"][0], RIGHT["center"][1]),
    "左片圆心 = 右片关于 x=0 镜像，两段不共圆、在中缝 y≈722.80 相交；V→P₁ / V→P₂ 及镜像旧边仍是虚线标注",
    "平铺：外轮廓＝后片整片（后片半 ×2 镜像），中央 V 形＝前片门襟边；正面线稿、不填色、不做背视",
]


def selftest(pieces):
    r = []

    def ck(name, ok, extra=""):
        r.append((name, bool(ok), extra))

    r_ = geo.points_resolved()
    tpl_front = [p for p in geo.TPL["pieces"] if p["name"] == "前片"][0]
    tpl_back = [p for p in geo.TPL["pieces"] if p["name"] == "后片半"][0]
    ck("前片（右）cmds 与模板逐项相同（几何未改）", pieces[0]["cmds"] == tpl_front["cmds"])
    ck("后片半 cmds 与模板逐项相同（几何未改）", geo.back_piece()["cmds"] == tpl_back["cmds"])
    ck("片表 = 前片左右两片（镜像同步）", len(pieces) == 2)
    ck("左片 cmds = 右片关于 x=0 镜像",
       pieces[1]["cmds"] == geo.mirror_cmds(pieces[0]["cmds"]))
    ck("右片新领口首末点 = 第 2 步的 P₁/P₂",
       pieces[0]["links"][0][0] == list(r_["P1"]) and
       pieces[0]["links"][0][-1] == list(r_["P2"]))
    ck("左片新领口首末点 = P₁′/P₂′",
       pieces[1]["links"][0][0] == list(LEFT["P1"]) and
       pieces[1]["links"][0][-1] == list(LEFT["P2"]))
    ck("两段新领口弧长相等", abs(LEFT["arc_length"] - RIGHT["arc_length"]) < 1e-9,
       "%.4f mm" % RIGHT["arc_length"])
    ck("两段关于前中缝 x=0 对称（端点）",
       all(abs(LEFT[k][0] + RIGHT[k][0]) < 1e-9 and
           abs(LEFT[k][1] - RIGHT[k][1]) < 1e-9 for k in ("P1", "P2")))
    ck("P₁ 仍在顶边 y=L 上", abs(r_["P1"][1] - geo.L) < 1e-9)
    ck("P₂ 仍在门襟边上",
       abs(geo._cross((r_["P2"][0] - geo.V[0], r_["P2"][1] - geo.V[1]), geo.U_LAP)) < 1e-9)
    ck("新领口为圆弧采样折线（点数 > 2，首末点不延长）",
       len(pieces[0]["links"][0]) > 2 and len(pieces[1]["links"][0]) > 2)
    ck("★ 圆心角 = 60°（用户 11:48 令「P1P2 为圆心角 60 度的弧」）",
       abs(abs(RIGHT["sweep_deg"]) - geo.ARC_SWEEP_DEG) < 1e-9 and
       abs(abs(LEFT["sweep_deg"]) - geo.ARC_SWEEP_DEG) < 1e-9,
       "%.6f°" % RIGHT["sweep_deg"])
    ck("R = 弦长（60° 弧：c = 2R·sin30° = R），不再是 VP₁=50",
       abs(RIGHT["radius"] - RIGHT["chord"]) < 1e-9 and
       abs(RIGHT["radius"] - geo.ARC_R) < 1e-9,
       "R=%.6f mm" % RIGHT["radius"])
    ck("圆心由「弦中垂线 + 弦心距 R·cos30°」解析确定；左片圆心 = 右片镜像",
       abs(RIGHT["center"][0] + LEFT["center"][0]) < 1e-9 and
       abs(RIGHT["center"][1] - LEFT["center"][1]) < 1e-9 and
       abs(math.dist(RIGHT["center"], RIGHT["P1"]) - geo.ARC_R) < 1e-9,
       "C=(%.6f, %.6f)" % (RIGHT["center"][0], RIGHT["center"][1]))
    ck("所有采样点都在各自圆心、R=ARC_R 的圆上",
       all(abs(math.dist(q, RIGHT["center"]) - geo.ARC_R) < 1e-6
           for q in pieces[0]["links"][0]) and
       all(abs(math.dist(q, LEFT["center"]) - geo.ARC_R) < 1e-6
           for q in pieces[1]["links"][0]))
    ck("弧凹向下摆（弧最低点低于弦中点）",
       min(q[1] for q in RIGHT["samples"]) < RIGHT["midpoint"][1],
       "最低 y=%.4f" % min(q[1] for q in RIGHT["samples"]))
    ck("弧长 = R·60°(rad)",
       abs(RIGHT["arc_length"] - geo.ARC_R * math.radians(60.0)) < 1e-9,
       "%.4f mm" % RIGHT["arc_length"])
    ck("矢高 = R − √(R²−(c/2)²)",
       abs(RIGHT["sagitta"] -
           (geo.ARC_R - math.sqrt(geo.ARC_R ** 2 - (RIGHT["chord"] / 2) ** 2))) < 1e-9,
       "%.4f mm" % RIGHT["sagitta"])
    y_cross = RIGHT["center"][1] - math.sqrt(geo.ARC_R ** 2 - RIGHT["center"][0] ** 2)
    a_cross = math.degrees(math.atan2(y_cross - RIGHT["center"][1],
                                      0.0 - RIGHT["center"][0]))
    ck("两段 60° 弧不共圆、在中缝 x=0 相交（左右镜像的几何必然，非 bug）",
       math.dist(RIGHT["center"], LEFT["center"]) > 1e-6 and
       RIGHT["start_deg"] - 1e-6 <= a_cross <= RIGHT["end_deg"] + 1e-6,
       "交点 y=%.4f" % y_cross)
    ck("左片采样点 = 右片关于 x=0 镜像",
       all(abs(LEFT["samples"][i][0] + RIGHT["samples"][i][0]) < 1e-9 and
           abs(LEFT["samples"][i][1] - RIGHT["samples"][i][1]) < 1e-9
           for i in range(len(RIGHT["samples"]))))
    ck("右片旧边虚线段 = V→P₂ 与 P₁→V",
       pieces[0]["dashed"] == [[list(geo.V), list(r_["P2"])],
                               [list(r_["P1"]), list(geo.V)]])
    ck("左片旧边虚线段 = V→P₂′ 与 P₁′→V",
       pieces[1]["dashed"] == [[list(geo.mirror_x(geo.V)), list(LEFT["P2"])],
                               [list(LEFT["P1"]), list(geo.mirror_x(geo.V))]])
    ck("出图时每片恰拆出 2 段虚线旧边（实线路径已跳过）",
       all(len(sheet.path_d_dashed(p["cmds"], p["dashed"], 0, 0)[1]) == 2
           for p in pieces))
    half = sheet.sample(geo.back_piece()["cmds"], 32)
    whole = half + list(reversed([(-x, y) for x, y in half]))
    ck("平铺外轮廓 = 后片半 ×2 镜像", len(whole) == 2 * len(half))
    ck("平铺外轮廓首尾同在下摆中点（去掉 Z 仍闭合，不生斜贯线）",
       abs(whole[0][0] - whole[-1][0]) < 1e-9 and
       abs(whole[0][1] - whole[-1][1]) < 1e-9)
    ck("平铺外轮廓 x 关于后中缝对称",
       abs(min(x for x, _ in whole) + max(x for x, _ in whole)) < 1e-9)
    ck("平铺 V 形两线端点 = V 与 ±H",
       list(geo.V) == [0.0, geo.L] and list(geo.H) == [geo.LAP_DX, 0.0])
    return r


def make_flat():
    """成衣平铺线稿。骨架照搬 hanfu-zhidui/pattern/flat.py，几何全部来自 geo。
    两条新领口**圆弧**（右 P₁→P₂ / 左 P₁′→P₂′）左右镜像同步。"""
    INK, GRAY, RED = "#1a1a1a", "#6f6f6f", "#c0392b"
    W, H = 2200, 1500
    OX, OY = W / 2.0, 1120.0

    def tx(x, y, s, size=22, color=INK, anchor="start", weight=None):
        w = ' font-weight="600"' if weight else ""
        return ('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" '
                'fill="%s" text-anchor="%s"%s>%s</text>' % (x, y, size, color, anchor, w, s))

    def poly(pts):
        d = "M %.1f %.1f" % (OX + pts[0][0], OY - pts[0][1])
        for q in pts[1:]:
            d += " L %.1f %.1f" % (OX + q[0], OY - q[1])
        return d + " Z"

    def seg(a, b, w=2.2, dash=None, color=INK):
        ds = ' stroke-dasharray="%s"' % dash if dash else ""
        return ('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="%.1f" '
                'fill="none" stroke-linecap="round"%s/>'
                % (OX + a[0], OY - a[1], OX + b[0], OY - b[1], color, w, ds))

    def poly_seg(pts, w=2.2, dash=None, color=INK):
        """多点折线（解析圆弧的等角采样）；2 点时等价于 seg。"""
        ds = ' stroke-dasharray="%s"' % dash if dash else ""
        d = "M %.1f %.1f" % (OX + pts[0][0], OY - pts[0][1])
        for q in pts[1:]:
            d += " L %.1f %.1f" % (OX + q[0], OY - q[1])
        return ('<path d="%s" stroke="%s" stroke-width="%.1f" fill="none" '
                'stroke-linejoin="round" stroke-linecap="round"%s/>' % (d, color, w, ds))

    def dot(p, lab, dx, dy, color, rad=7):
        x, y = OX + p[0], OY - p[1]
        return ['<circle cx="%.1f" cy="%.1f" r="%d" fill="#ffffff" stroke="%s" stroke-width="2.2"/>'
                % (x, y, rad, color),
                tx(x + dx, y + dy, lab, 23, color, weight=1)]

    half = sheet.sample(geo.back_piece()["cmds"], 32)
    whole = half + list(reversed([(-x, y) for x, y in half]))
    L = max(y for _, y in whole)
    HW = max(x for x, _ in whole)
    V, Hh = geo.V, geo.H
    Hm = (-Hh[0], 0.0)
    R1, R2 = RIGHT["P1"], RIGHT["P2"]
    L1, L2 = LEFT["P1"], LEFT["P2"]

    # 旧边虚线化（用户令）：顶边 V→P₁ / V→P₁′ 落在外轮廓折线上，门襟边 V→P₂ / V→P₂′ 单独画
    flat_dashed = [[V, L1], [R1, V]]

    def TX(q):
        return (OX + q[0], OY - q[1])

    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         tx(56, 62, "试验竖领浅交襟 · 第 3 步 · 平铺线稿（新领口圆心角 60° 圆弧）", 38, INK, weight=1),
         tx(56, 102, "外轮廓＝后片半 ×2 镜像合成整片　｜　中央 V 形＝前片门襟边（模板原边）　｜　"
                     "白底纯黑、不填色、不做背视", 21, GRAY),
         tx(56, 134, "红线＝新领口圆弧（圆心角 60°、R=弦长=76.5732mm、凹向下摆，左右镜像同步、不共圆）　｜　"
                     "黑虚线＝V→P₁ / V→P₂ 及镜像旧边", 21, GRAY)]

    # 1 外轮廓（后片整片）：顶边 V 附近两段从实线路径断开，改由虚线画
    solid_d, top_dash = sheet.split_polyline(whole, flat_dashed, TX)
    # 不加 Z：split_polyline 用 M 断开后，Z 会闭合到「最近一个 M」（P₁ 附近），
    # 凭空多出一条从下摆中点斜贯到领口的长线。solid_d 首尾同在下摆中点，自然闭合。
    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" '
             'stroke-linejoin="round"/>' % (solid_d, INK))
    # 1b 顶边旧边 V→P₁ / V→P₁′：虚线标注
    for a, b in top_dash:
        s.append(seg(a, b, 2.6, "14 10"))
    # 2 后中缝（虚线，只到下摆→肩线）
    s.append(seg((0, 0), (0, L), 1.6, "26 14", GRAY))
    # 3 前片门襟边：P₂→H 仍实线，V→P₂ 旧边改虚线（左右镜像同步）
    s.append(seg(R2, Hh, 3.0))
    s.append(seg(L2, Hm, 3.0))
    s.append(seg(V, R2, 3.0, "14 10"))
    s.append(seg(V, L2, 3.0, "14 10"))
    # 4 新领口：左右镜像同步的两条**圆弧**（解析采样折线，红色实线）
    s.append(poly_seg(RIGHT["samples"], 4.2, color=RED))
    s.append(poly_seg(LEFT["samples"], 4.2, color=RED))

    # 5 点标记（P₂/P₂′ 相距仅 17mm，圈缩小、标签左右错开）
    for p, lab, dx, dy, col in [
        (V, "V", 16, -46, INK),
        (R1, "P₁", -108, -30, RED),
        (L1, "P₁′", 30, -30, RED),
        (R2, "P₂", 34, 46, RED),
        (L2, "P₂′", -140, 46, RED),
        ((-geo.X_SHLD, L), "S", -64, 34, INK),
        ((geo.X_SHLD, L), "S′", 18, 34, INK),
        (Hh, "H", 18, 22, INK),
        (Hm, "H′", -74, 22, INK),
    ]:
        s += dot(p, lab, dx, dy, col)

    # 6 图上说明（都在衣外或空白区）
    s.append(tx(OX + Hh[0] + 34, OY - L * 0.46, "前片门襟边（模板原边）", 21, INK))
    s.append(tx(OX - 26, OY - L * 0.34, "后中缝", 20, GRAY, "end"))
    s.append(tx(56, 300, "后片整片外轮廓（后片半 ×2 镜像）", 21, GRAY))
    s.append(tx(OX + 200, OY - L + 108, "新领口圆弧：P₁→P₂ 与 P₁′→P₂′（圆心角 60°、R=弦长=76.5732mm）", 21, RED))

    # 7 平铺宽尺寸线 + 底部说明
    s.append(seg((-HW, -70), (HW, -70), 1.0, color=GRAY))
    s.append(seg((-HW, -60), (-HW, -80), 1.0, color=GRAY))
    s.append(seg((HW, -60), (HW, -80), 1.0, color=GRAY))
    s.append(tx(OX, OY + 116,
                "P₁P₂ = 新领口圆弧：圆心角 60°　弦 %.2f / 弧长 %.2f / 矢高 %.2f mm（R=弦长=%.2f、凹向下摆）"
                % (RIGHT["chord"], RIGHT["arc_length"], RIGHT["sagitta"], geo.ARC_R), 23, RED, "middle"))
    s.append(tx(OX, OY + 152, "平铺宽 %.0f（2 × %.0f）　衣长 %.0f　θ=%.4f°　｜　为第 4 步备图"
                % (HW * 2, HW, L, geo.THETA), 21, GRAY, "middle"))
    s.append(tx(OX, OY + 188, "V→P₁ / V→P₂（及镜像）旧边改虚线标注；新领口圆弧仍为实线",
                21, GRAY, "middle"))

    # 8 100mm 标尺
    bx, by = 56, H - 56
    s.append('<g id="SCALE" stroke="%s" stroke-width="2.2" fill="none">' % INK)
    for k in range(11):
        hh = 28 if k % 5 == 0 else 15
        s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx + k * 100, by, bx + k * 100, by - hh))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (bx, by, bx + 1000, by))
    s.append('</g>')
    s.append(tx(bx, by + 30, "100mm 校验标尺（1:1 打印后实测，误差应 ≤0.5mm）", 20, INK))
    s.append('</svg>')

    svg = os.path.join(OUT, "step3_平铺线稿.svg")
    open(svg, "w", encoding="utf-8").write("\n".join(s))
    png = os.path.join(OUT, "step3_平铺线稿.png")
    return svg, png, make_png(svg, png)


def main():
    pieces = geo.sheet_pieces_step3()
    print("=== 第 3 步自检 ===")
    fails = []
    for name, ok, extra in selftest(pieces):
        print("  %s %s %s" % ("PASS" if ok else "FAIL", name, extra))
        if not ok:
            fails.append(name)
    if fails:
        print("!! 自检未过：", fails)
        return 1

    data = {
        "step": 3,
        "action": ["连接 P1P2（新领口·圆弧）", "前片左右镜像同步", "按前片/后片制作平铺线稿"],
        "semantic": "P1P2 = 新领口（用户 2026-11-10 定名）；2026-11-11 11:48 修正：改为圆心角 60° 的解析圆弧",
        "mirror_sync": True,
        "basis": {"profile": geo.PROFILE, "size": geo.SIZE, "L": geo.L,
                  "template": os.path.basename(geo.TPL_PATH),
                  "note": "衣长缩短 5cm 已撤销，回归厂商基准模板原值 770"},
        "segments": {"right": RIGHT, "left": LEFT},
        "arc": {
            "user_command": "2026-11-11 11:48：P1P2 为圆心角 60 度的弧（端点 P₁/P₂ 不动）；凹向下摆沿用 23:23 口径",
            "sweep_deg": RIGHT["sweep_deg"],
            "radius_mm": geo.ARC_R,
            "radius_source": "c = 2R·sin(60°/2) = R ⇒ R = 弦长 = 76.5732mm（不再是 VP₁=50、圆心不再是 V）",
            "center": RIGHT["center"],
            "center_left": LEFT["center"],
            "center_reason": "圆心在弦中垂线上、距弦中点 d = R·cos30°；取弧中点 y 较小的一支＝凹向下摆；左片圆心＝右片关于 x=0 镜像",
            "right_polar_deg": [RIGHT["start_deg"], RIGHT["end_deg"]],
            "left_polar_deg": [LEFT["start_deg"], LEFT["end_deg"]],
            "chord_mm": RIGHT["chord"],
            "chord_dist_mm": RIGHT["chord_dist"],
            "arc_length_mm": RIGHT["arc_length"],
            "sagitta_mm": RIGHT["sagitta"],
            "apex": RIGHT["apex"],
            "sagitta_dir": "向下摆（圆心在弦右上，弧向左下鼓；弧中点 y 低于弦中点）",
            "seam_cross_y_mm": RIGHT["center"][1] - math.sqrt(geo.ARC_R ** 2 - RIGHT["center"][0] ** 2),
            "seam_cross_note": "两段圆心互为镜像、不共圆，在中缝 x=0 相交于此（左右镜像的几何必然，非 bug）",
            "samples_note": "几何是连续解析圆弧；links 里的多点折线只是等角采样（64 段），不是新增控制点",
        },
        "flat": {"outline": "后片半 ×2 镜像合成整片",
                 "lap_edges": "前片门襟边 V→(±LAP_DX, 0)（模板原边）",
                 "neckline": "新领口两条圆心角 60° 的圆弧：右 P₁→P₂ / 左 P₁′→P₂′，左右镜像同步、不共圆",
                 "style": "正面线稿、白底纯黑、不填色、不做背视"},
        "old_edges": {
            "style": "虚线标注（用户 2026-11-10 令，第 3 步补充）",
            "segments": ["V→P₂", "P₁→V", "V→P₂′", "P₁′→V"],
            "note": "只改画法：cmds 与模板逐项相同；新领口圆弧仍为实线",
        },
        "geometry_changed": False,
        "note": "第 1/2 步产物保留（P₁/P₂ 端点与 VP₁=VP₂=50 未改）；11:48 按用户令把新领口圆弧改为圆心角 60°（R=弦长=76.5732mm、圆心解析确定）；裁片 cmds 一处未改；未推断第 5 步。",
    }
    json.dump(data, open(os.path.join(OUT, "step3.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    params = dict(L=geo.L, LAP_DX=geo.LAP_DX, X_SHLD=geo.X_SHLD,
                  LEN_TOP=geo.LEN_TOP, LEN_LAP=round(geo.LEN_LAP, 4),
                  THETA_DEG=round(geo.THETA, 6),
                  VP1=geo.R_EQUAL, VP2=geo.R_EQUAL,
                  ARC_R=geo.ARC_R, ARC_CENTER=list(geo.ARC_CENTER),
                  ARC_SWEEP_DEG=geo.ARC_SWEEP_DEG,
                  SEG_CHORD=round(RIGHT["chord"], 4),
                  ARC_LEN=round(RIGHT["arc_length"], 4),
                  ARC_SAGITTA=round(RIGHT["sagitta"], 4))
    svg = os.path.join(OUT, "step3_P1P2连线.svg")
    info = sheet.write_sheet(params, pieces, svg, TITLE, SUBTITLE, NOTES)
    print("\n=== 产物 ===")
    print("  ", info["svg"])
    print("  ", info["side"])
    for p in info["pieces"]:
        print("   %s ×%d：%.1f × %.1f mm" % (p["name"], p["qty"], p["w"], p["h"]))
    png = os.path.join(OUT, "step3_P1P2连线.png")
    print("   PNG:", make_png(svg, png))
    fsvg, fpng, fres = make_flat()
    print("   平铺线稿:", fsvg, "|", fpng, "|", fres)
    print("   ", os.path.join(OUT, "step3.json"))
    print("\n右片新领口圆弧 P₁ = %s → P₂ = %s  弦 %.4f / 弧长 %.4f mm"
          % (RIGHT["P1"], RIGHT["P2"], RIGHT["chord"], RIGHT["arc_length"]))
    print("左片镜像 P₁′ = %s → P₂′ = %s  圆心=%s（右片圆心关于 x=0 镜像）"
          % (LEFT["P1"], LEFT["P2"], LEFT["center"]))
    print("圆心角 60°：R=弦长=%.4f mm，弧长 %.4f / 矢高 %.4f mm；两段弧在中缝 y=%.4f 相交"
          % (geo.ARC_R, RIGHT["arc_length"], RIGHT["sagitta"],
             RIGHT["center"][1] - math.sqrt(geo.ARC_R ** 2 - RIGHT["center"][0] ** 2)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
