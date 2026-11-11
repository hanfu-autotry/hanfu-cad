# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 第 6 步（重做）：领条＝一条带状，三段沿共边相接、首尾不接

    python pattern/step6.py
      → out/step6_完整裁片图.svg / .pieces.json / .png   （5 片）
        out/step6_领条一条带.svg / .png                   （带子放大）
        out/step6.json

用户令（2026-11-11 15:58 / 16:00）：
  「产物不会是这种两层的不明物体，而是一条由三部分组成的带状领子」
  「首尾相接　领条首尾不想接」

口径：
  领条＝**一条开放的带状裁片**，由三段（①前片左襟 / ②后片 / ③前片右襟）沿共边
  P₁A / P₁′A′ 相接；两端 P₂B / P₂′B′ 落在带子两端、**分开不接**（不绕成环）。
  展开方式＝沿共边依次**翻折展开**（刚性铰接）：段①不动、段②关于 P₁A 反射、
  段③两次反射。反射是等距变换 ⇒ 每段边长 / 角度 / 面积严格不变。
  → 展开后三段沿 x 依次排开、**不自交**；轮廓 8 条边（2 C + 6 L）。
  不新增参数、不量图、不改第 3/4/5 步几何。
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet
from step1 import make_png, OUT

TITLE = "试验竖领浅交襟 · 第 6 步 · 完整裁片图（前片 / 后片 / 领条一条带状）"
SUBTITLE = "领条＝一条带状裁片：三段沿共边 P₁A / P₁′A′ 翻折展开相接，两端分开不接　｜　净版 mm　｜　前 / 后片 cmds 与模板逐项相同"
NOTES = [
    "领条＝1 片带状（不再是 3 片、也不再是自交闭合轮廓）：三段①前片左襟 / ②后片 / ③前片右襟沿共边相接",
    "展开＝沿共边依次翻折（刚性铰接）：①不动、②关于 P₁A 反射、③两次反射；反射等距 ⇒ 形状 / 面积不变",
    "轮廓 8 条边：下缘 3（右 60° 弧 C / 后颈直线 / 左 60° 弧 C）+ 上缘 3（直线）+ 两端头 30mm；cmds 仅 M/L/C/Z",
    "首尾不接：两端 P₂B / P₂′B′ 各 30mm 落在带子两端、互不相连；展开后不自交（自交点 0）",
]


def selftest(b, pieces):
    oks = []

    def ck(name, cond, extra=""):
        good = bool(cond)
        oks.append(good)
        print("  %s %s %s" % ("PASS" if good else "FAIL", name, extra))
        return good

    cp = geo.collar_points()
    rg = geo.collar_regions()
    by = {p["name"]: p for p in pieces}
    tpl_front = geo.front_piece()
    tpl_back = geo.back_piece()
    tpl_collar = next(p for p in geo.TPL["pieces"] if p["name"] == "领缘条")
    cmds = b["cmds"]
    kinds = [c[0] for c in cmds]
    segs = b["segments"]

    # ---- 一条带 / 三段 ----
    ck("★ 领条是 1 条带状裁片（cmds 1 个 M、1 个 Z）",
       kinds[0] == "M" and kinds[-1] == "Z" and sum(1 for k in kinds if k == "M") == 1,
       "".join(kinds))
    ck("★ 由三段组成：段①前片左襟 / 段②后片 / 段③前片右襟",
       len(segs) == 3 and [s["idx"] for s in segs] == [1, 2, 3],
       " / ".join(s["name"] for s in segs))
    ck("★ 轮廓 8 条边（2 C + 6 L），内部共边不在轮廓上",
       b["edge_count"] == 8 and
       [e["kind"] for e in b["edges"]] == ["C", "L", "C", "L", "L", "L", "L", "L"])
    ck("★ 端点首尾相接（8 处接缝 max < 1e-9mm）",
       b["joints_max"] < 1e-9, "%.3e mm" % b["joints_max"])

    # ---- 共边 / 首尾不接 ----
    ck("★ 两条共边各 30mm（段①|段② = P₁A，段②|段③ = P₁′A′）",
       len(b["seams"]) == 2 and all(abs(s["length"] - 30.0) < 1e-9 for s in b["seams"]),
       " / ".join("%.6f" % s["length"] for s in b["seams"]))
    ck("★ 两条端头各 30mm，且**互不相连**（首尾不接）",
       len(b["ends"]) == 2 and all(abs(e["length"] - 30.0) < 1e-9 for e in b["ends"]) and
       math.dist(tuple(b["ends"][0]["a"]), tuple(b["ends"][1]["a"])) > 100.0,
       "两端间距 %.3f mm" % math.dist(tuple(b["ends"][0]["b"]), tuple(b["ends"][1]["b"])))

    # ---- 不自交（关键）----
    ck("★ 展开后**不自交**（自交点 0）——不是「两层」",
       b["self_intersection_count"] == 0,
       "%d 处" % b["self_intersection_count"])

    # ---- 反射保形 / 面积守恒 ----
    ck("★ 段② cmds = 原后片 cmds 关于直线 P₁A 反射（等距）",
       segs[1]["cmds"] == geo._refl_cmds(rg["regions"][1]["cmds"],
                                         tuple(cp["P1"]), tuple(cp["A"])))
    P1p_r, Ap_r = geo._refl_pt(tuple(cp["P1p"]), tuple(cp["P1"]), tuple(cp["A"])), \
                  geo._refl_pt(tuple(cp["Ap"]), tuple(cp["P1"]), tuple(cp["A"]))
    ck("★ 段③ cmds = 原右襟 cmds 两次反射（先 P₁A、再反射后的 P₁′A′）",
       segs[2]["cmds"] == geo._refl_cmds(
           geo._refl_cmds(rg["regions"][2]["cmds"], tuple(cp["P1"]), tuple(cp["A"])),
           P1p_r, Ap_r))
    ck("★ 每段面积 = 第 5 步对应块面积（反射不改变面积）",
       all(abs(segs[i]["area"] - rg["regions"][i]["area"]) < 1e-9 for i in range(3)),
       " / ".join("%.6f" % s["area"] for s in segs))
    ck("★ 段③ 面积 = 段①（镜像等距）",
       abs(segs[2]["area"] - segs[0]["area"]) < 1e-9, "%.9f mm²" % segs[2]["area"])
    ck("★ 带子面积 = 三段面积之和（沿共边拼接、无重叠）",
       abs(b["area_total"] - sum(s["area"] for s in segs)) < 1e-9 and
       abs(b["area_total"] - rg["area_total"]) < 1e-9,
       "%.9f mm²" % b["area_total"])
    ck("★ 解析格林积分与 sheet.sample(4096) 鞋带吻合（<1e-3 mm²）",
       abs(b["area_diff"]) < 1e-3,
       "解析 %.9f / 鞋带 %.9f / 差 %.2e"
       % (abs(b["area_signed"]), b["area_numeric"], b["area_diff"]))

    # ---- 三段排开、呈带状 ----
    bbs = [sheet.real_bbox(s["cmds"]) for s in segs]
    ck("★ 三段沿 x 依次排开：段③ 在左、段②居中、段①在右",
       bbs[2][2] <= bbs[1][2] + 1e-6 and bbs[1][2] <= bbs[0][2] + 1e-6,
       "x 右界 %.1f / %.1f / %.1f" % (bbs[2][2], bbs[1][2], bbs[0][2]))
    gb = sheet.real_bbox(cmds)
    ratio = (gb[2] - gb[0]) / (gb[3] - gb[1])
    ck("★ 整体呈带状（bbox 长宽比 > 1.8）",
       ratio > 1.8, "%.3f（%.1f × %.1f mm）" % (ratio, gb[2] - gb[0], gb[3] - gb[1]))

    # ---- 片表 ----
    ck("★ 完整裁片图 = 前片 2 + 后片 2 + 领条 1，共 5 片",
       len(pieces) == 5 and sum(p["qty"] for p in pieces) == 5,
       "%d 片 / qty %d" % (len(pieces), sum(p["qty"] for p in pieces)))
    ck("★ 领条片 qty=1、名称 = BAND_NAME",
       by[geo.BAND_NAME]["qty"] == 1 and
       len([p for p in pieces if p["name"].startswith("领条")]) == 1)
    ck("★ 领条片 cmds 与 geo.collar_band() 逐项相同",
       by[geo.BAND_NAME]["cmds"] == cmds)
    ck("★ 领条 grain 沿用模板「领缘条」[1,0]",
       by[geo.BAND_NAME]["grain"] == list(tpl_collar["grain"]))
    ck("★ 片内 note 标注面积（≤16 字）",
       by[geo.BAND_NAME]["note"].startswith("A=") and len(by[geo.BAND_NAME]["note"]) <= 16)

    # ---- 前 / 后片未改 ----
    ck("★ 前片（右）cmds 与模板前片逐项相同",
       by["前片（右）"]["cmds"] == tpl_front["cmds"])
    ck("★ 前片（左）cmds = 模板前片关于 x=0 镜像",
       by["前片（左·镜像）"]["cmds"] == geo.mirror_cmds(tpl_front["cmds"]))
    ck("★ 后片（右·半）cmds 与模板后片半逐项相同",
       by["后片（右·半）"]["cmds"] == tpl_back["cmds"])
    ck("★ 后片（左·半·镜像）cmds = 模板后片半关于 x=0 镜像",
       by["后片（左·半·镜像）"]["cmds"] == geo.mirror_cmds(tpl_back["cmds"]))
    ck("★ 前片保留第 3 步新领口红弧（links）与旧边虚线（dashed）",
       len(by["前片（右）"]["links"]) == 1 and
       len(by["前片（右）"]["dashed"]) == 2 and
       len(by["前片（左·镜像）"]["links"]) == 1)

    # ---- 旧步骤未破坏 ----
    ck("★ 第 5 步三块片表仍可复现为 7 片（旧步骤未破坏）",
       len(geo.sheet_pieces_step5()) == 7 and len(rg["regions"]) == 3)

    return sum(oks), len(oks) - sum(oks)


def _tx(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_band_zoom(b):
    """一条带状领条放大图：三段 + 两条共边（蓝实线＝缝线）+ 两端头（绿粗线＝首尾不接）。"""
    INK, RED, BLUE, GRAY, GREEN = "#1a1a1a", "#c0392b", "#1f5fa8", "#6a6a6a", "#1e8449"
    VW, VH, PX = 520.0, 640.0, 5.0
    SCALE = 1.62

    def T(x, y, txt, size=4.6, anchor="start", color=INK, weight="400"):
        return ('<text x="%.3f" y="%.3f" font-family="sans-serif" font-size="%.2f" '
                'fill="%s" text-anchor="%s" font-weight="%s">%s</text>'
                % (x, y, size, color, anchor, weight, _tx(txt)))

    def sx(q):
        return [q[0] * SCALE, q[1] * SCALE]

    x0, y0, x1, y1 = sheet.real_bbox(b["cmds"])
    cx, ty = 250.0, 96.0
    ox = cx - (x0 + x1) / 2.0 * SCALE
    oy = ty + y1 * SCALE

    def P(q):
        return (q[0] * SCALE + ox, oy - q[1] * SCALE)

    def scaled(cmds):
        out = []
        for c in cmds:
            if c[0] == "Z":
                out.append(["Z"])
            elif c[0] in ("M", "L"):
                out.append([c[0], sx(c[1])])
            elif c[0] == "C":
                out.append(["C", sx(c[1]), sx(c[2]), sx(c[3])])
        return out

    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %.3f %.3f">' % (int(VW * PX), int(VH * PX), VW, VH),
         '<rect width="100%" height="100%" fill="#ffffff"/>']
    s.append(T(24, 22, "第 6 步 · 领条＝一条带状（三段沿共边相接 · 首尾不接）", 9.0, weight="600"))
    s.append(T(24, 37, "沿共边依次翻折展开（刚性铰接）：段① 不动 → 段② 关于 P₁A 反射 → 段③ 两次反射；反射等距，形状与面积不变", 4.5, color=GRAY))
    s.append(T(24, 50, "黑实线＝外轮廓（下缘 2 段贝塞尔 C 标红）｜蓝实线＝两条共边（段与段缝线，各 30mm）｜绿粗线＝两端头（各 30mm，分开不接）", 4.5, color=GRAY))

    # 外轮廓
    s.append('<path d="%s" stroke="%s" stroke-width="1.0" fill="none" stroke-linejoin="round"/>'
             % (sheet.path_d(scaled(b["cmds"]), ox, oy), INK))

    # 下缘两段 C 红色高亮
    cur = None
    for c in b["cmds"]:
        if c[0] in ("M", "L"):
            cur = c[1]
        elif c[0] == "C":
            seg = [["M", list(cur)], ["C", c[1], c[2], c[3]]]
            s.append('<path d="%s" stroke="%s" stroke-width="1.7" fill="none"/>'
                     % (sheet.path_d(scaled(seg), ox, oy), RED))
            cur = c[3]

    # 两条共边（缝线）蓝色实线
    for sm in b["seams"]:
        seg = [["M", list(sm["a"])], ["L", list(sm["b"])]]
        s.append('<path d="%s" stroke="%s" stroke-width="1.4" fill="none"/>'
                 % (sheet.path_d(scaled(seg), ox, oy), BLUE))

    # 两个端头绿色粗线（首尾不接）
    for en in b["ends"]:
        seg = [["M", list(en["a"])], ["L", list(en["b"])]]
        s.append('<path d="%s" stroke="%s" stroke-width="2.2" fill="none"/>'
                 % (sheet.path_d(scaled(seg), ox, oy), GREEN))

    # 三段标注（bbox 中心）
    for sg in b["segments"]:
        bb = sheet.real_bbox(sg["cmds"])
        mx, my = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
        p = P((mx, my))
        s.append(T(p[0], p[1] - 3, sg["name"], 4.6, anchor="middle", weight="600"))
        s.append(T(p[0], p[1] + 5, "A=%.6f mm²" % sg["area"], 4.2, anchor="middle", color=BLUE))

    # 共边 / 端头文字
    for sm, dx in zip(b["seams"], [-34, 6]):
        mx, my = (sm["a"][0] + sm["b"][0]) / 2.0, (sm["a"][1] + sm["b"][1]) / 2.0
        p = P((mx, my))
        s.append(T(p[0] + dx, p[1] + 2, "共边 %.0f" % sm["length"], 3.9, color=BLUE))
    for en, lab in zip(b["ends"], ["端头 30", "端头 30"]):
        p = P(tuple(en["a"]))
        s.append(T(p[0] + 4, p[1] + 10, lab, 3.9, color=GREEN))

    # ---- 数据区 ----
    rows_l = [
        ("段数 / 边数", "3 段 / 8 条边（2 C + 6 L）"),
        ("共边", "2 条 × %.6f mm" % b["seams"][0]["length"]),
        ("端头（首尾不接）", "2 条 × %.6f mm" % b["ends"][0]["length"]),
        ("自交", "%d 处（展开后不自交）" % b["self_intersection_count"]),
        ("面积（三段和）", "%.6f mm²" % b["area_total"]),
    ]
    rows_r = [
        ("段① 前片左襟", "%.6f mm²" % b["segments"][0]["area"]),
        ("段② 后片", "%.6f mm²" % b["segments"][1]["area"]),
        ("段③ 前片右襟", "%.6f mm²" % b["segments"][2]["area"]),
        ("解析 / 鞋带", "%.3f / %.3f" % (abs(b["area_signed"]), b["area_numeric"])),
        ("周长", "%.6f mm" % b["perimeter"]),
    ]
    for colx, rows in ((24.0, rows_l), (270.0, rows_r)):
        for i, (k, v) in enumerate(rows):
            s.append(T(colx, 322 + i * 16, k, 4.0, color=GRAY))
            s.append(T(colx, 329 + i * 16, v, 4.8, weight="600"))

    for j, ln in enumerate([
        "产物＝一条带状领子，由三部分组成：段①前片左襟 → 段②后片 → 段③前片右襟，沿共边 P₁A / P₁′A′ 首尾相接。",
        "领条首尾不接：两端 P₂B / P₂′B′（绿粗线，各 30mm）分开落在带子两端，不再绕成环、不再自交。",
        "展开为刚性铰接（反射等距）：边长 / 角度 / 面积全部不变，无拉伸、无近似；前 / 后片 cmds 与模板逐项相同。",
    ]):
        s.append(T(24, 470 + j * 13, ln, 3.9, color=GRAY))
    s.append('</svg>')

    svg = os.path.join(OUT, "step6_领条一条带.svg")
    open(svg, "w", encoding="utf-8").write("\n".join(s))
    png = os.path.join(OUT, "step6_领条一条带.png")
    make_png(svg, png)
    return svg, png


def main():
    b = geo.collar_band()
    pieces = geo.sheet_pieces_step6()
    rg = geo.collar_regions()

    print("=== 第 6 步 · 领条＝一条带状（三段沿共边相接、首尾不接）===")
    print("  三段：%s" % " / ".join(s["name"] for s in b["segments"]))
    print("  轮廓 %d 条边：%s" % (b["edge_count"], "".join(e["kind"] for e in b["edges"])))
    print("  共边：%s" % " / ".join("%.6f" % s["length"] for s in b["seams"]))
    print("  端头（首尾不接）：%s，两端间距 %.3f mm"
          % (" / ".join("%.6f" % e["length"] for e in b["ends"]),
             math.dist(tuple(b["ends"][0]["b"]), tuple(b["ends"][1]["b"]))))
    print("  自交：%d 处" % b["self_intersection_count"])
    print("  面积：三段和 %.9f mm²；解析 %.9f；鞋带 %.9f；差 %.2e"
          % (b["area_total"], abs(b["area_signed"]), b["area_numeric"], b["area_diff"]))
    print("  完整裁片图 %d 片：%s" % (len(pieces), " / ".join(p["name"] for p in pieces)))

    print("\n=== 自检 ===")
    npass, nfail = selftest(b, pieces)
    print("\n自检：%d PASS / %d FAIL" % (npass, nfail))

    sheet.GAP = 420.0

    params = dict(
        L=geo.L, LAP_DX=geo.LAP_DX, VP1=geo.R_EQUAL, VP2=geo.R_EQUAL,
        ARC_R=geo.ARC_R, ARC_SWEEP_DEG=geo.ARC_SWEEP_DEG,
        ARC_LEN=round(geo.ARC_LENGTH, 9), COLLAR_H=geo.COLLAR_H,
        BEZIER_K=round(rg["arc_approx"]["k"], 9),
        AREA_TOTAL=round(b["area_total"], 6),
        SEAM_LEN=round(b["seams"][0]["length"], 6),
        END_LEN=round(b["ends"][0]["length"], 6),
        EDGE_COUNT=b["edge_count"], SEGMENTS=len(b["segments"]),
        SELF_INTERSECTIONS=b["self_intersection_count"],
    )
    svg = os.path.join(OUT, "step6_完整裁片图.svg")
    info = sheet.write_sheet(params, pieces, svg, TITLE, SUBTITLE, NOTES)

    try:
        ET.parse(svg)
        xml_ok = True
    except Exception as e:
        xml_ok = False
        print("  SVG XML FAIL:", e)

    zsvg, zpng = make_band_zoom(b)
    try:
        ET.parse(zsvg)
        zoom_xml_ok = True
    except Exception as e:
        zoom_xml_ok = False
        print("  放大图 SVG XML FAIL:", e)

    data = {
        "step": 6,
        "action": "领条＝一条带状裁片：三段沿共边 P₁A / P₁′A′ 翻折展开相接，两端分开、首尾不接；完整裁片图 5 片",
        "user_orders": [
            "2026-11-11 15:58「产物不会是这种两层的不明物体，而是一条由三部分组成的带状领子」",
            "2026-11-11 16:00「首尾相接　领条首尾不想接」",
        ],
        "negated": [
            "15:42 三块拼成自交闭合轮廓（视觉两层，已回滚）",
            "领条首尾相连绕成环",
            "等宽直条 L×h",
        ],
        "basis": {
            "template": os.path.basename(geo.TPL_PATH),
            "profile": geo.PROFILE, "size": geo.SIZE, "L": geo.L,
            "readonly": True, "geometry_changed": False,
        },
        "band": b,
        "area_note": "反射为等距变换 ⇒ 每段面积严格不变；带子面积＝三段之和（沿共边拼接、无重叠）",
        "pieces": [dict(name=p["name"], qty=p["qty"],
                        bbox=[round(v, 3) for v in sheet.real_bbox(p["cmds"])])
                   for p in pieces],
        "selftest": dict(pass_=npass, fail=nfail),
        "svg_xml_valid": xml_ok,
        "zoom": {
            "svg": os.path.basename(zsvg),
            "png": os.path.basename(zpng),
            "svg_xml_valid": zoom_xml_ok,
            "png_bytes": os.path.getsize(zpng) if os.path.exists(zpng) else 0,
        },
        "note": "第 3/4/5 步几何一字未改；前 / 后片 cmds 与模板逐项相同；未推断第 7 步。",
    }
    json.dump(data, open(os.path.join(OUT, "step6.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n=== 产物 ===")
    print("  ", info["svg"])
    print("  ", info["side"])
    for p in info["pieces"]:
        print("   %s ×%d：%.1f × %.1f mm" % (p["name"], p["qty"], p["w"], p["h"]))
    png = os.path.join(OUT, "step6_完整裁片图.png")
    print("   PNG:", make_png(svg, png))
    if os.path.exists(png):
        print("   PNG 字节:", os.path.getsize(png))
    print("  ", os.path.join(OUT, "step6.json"))
    print("  放大图:", zsvg)
    if os.path.exists(zpng):
        print("  放大图 PNG 字节:", os.path.getsize(zpng))
    return 0 if (nfail == 0 and xml_ok and zoom_xml_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
