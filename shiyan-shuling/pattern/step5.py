# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 第 5 步：领子按衣片分三块 + 完整裁片图

    python pattern/step5.py
      → out/step5_完整裁片图.svg / .pieces.json / .png
        out/step5_领子三块放大.svg / .png
        out/step5.json

用户令（2026-11-11 14:24 / 14:35）：
  「算出前片左襟领子形状，边缘曲线，积分得到面积，
    算出后片领子形状，边缘曲线，积分得到面积，
    右襟前片由左襟镜像得到」
  「用贝塞尔近似，出图用什么你就用什么」
  「这不是立裁，这是平裁」「上身立起，平铺平面」

口径：
  领条不是等宽直条；第 4 步那条连续竖起领子按 P₁A / P₁′A′ 分成三块**平面区域**：
    ① 前片左襟领子  ② 后片领子  ③ 前片右襟领子（＝① 关于 x=0 镜像）
  每块边缘曲线：60° 弧 → 三次贝塞尔 C（sheet.py 原生支持 C，模板前/后片各带 5 条 C），
    直线边 → L；cmds 只含 M / L / C / Z，**不用采样折线**。
  面积＝½∮(x dy−y dx)：直线段叉积、贝塞尔段幂基多项式解析积分；
    另用 sheet.sample(cmds, 4096) 鞋带公式独立数值交叉验证。
  三块沿 P₁A / P₁′A′ 共边拼接＝第 4 步一条连续竖起领子；平铺各自独立，不扣减交叠。
  前 / 后片 cmds 与模板逐项相同；裁片图走 sheet.write_sheet。
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

TITLE = "试验竖领浅交襟 · 第 5 步 · 完整裁片图（前片 / 后片 / 领条三块）"
SUBTITLE = "平裁：领子按衣片分三块，贝塞尔曲边 + 格林公式面积分　｜　净版 mm　｜　前 / 后片 cmds 与模板逐项相同"
NOTES = [
    "领条＝三块平面裁片：前片左襟 / 后片 / 前片右襟（左襟镜像）；非等宽直条、非立裁",
    "60° 弧＝三次贝塞尔 C（k=4/3·tan(Δθ/4)，与 sheet.py 一致）；直线＝L，cmds 仅 M/L/C/Z",
    "面积＝½∮(x dy−y dx)：直线叉积 + 贝塞尔幂基解析积分；sheet.sample 鞋带交叉验证",
    "三块沿 P₁A / P₁′A′ 共边拼接＝一条连续竖起领子；前 / 后片 cmds 与模板逐项相同",
]


def selftest(rg, pieces):
    """自检：分块 / 边缘曲线 / 贝塞尔 / 积分面积 / 镜像 / 拼接 / 片表 / 前后片未改。"""
    oks = []

    def ck(name, cond, extra=""):
        good = bool(cond)
        oks.append(good)
        print("  %s %s %s" % ("PASS" if good else "FAIL", name, extra))
        return good

    cp = geo.collar_points()
    regs = rg["regions"]
    by = {p["name"]: p for p in pieces}
    tpl_front = geo.front_piece()
    tpl_back = geo.back_piece()
    tpl_collar = next(p for p in geo.TPL["pieces"] if p["name"] == "领缘条")

    # ---- 分块与形状 ----
    ck("★ 领子分成三块，名称齐备（左襟 / 后片 / 右襟）",
       [r["name"] for r in regs] == list(geo.COLLAR_REGION_NAMES),
       " / ".join(r["name"] for r in regs))
    ck("★ 三块 cmds 只含 M/L/C/Z，曲边是 C（不是采样折线）",
       all(set(c[0] for c in r["cmds"]) <= {"M", "L", "C", "Z"} for r in regs) and
       all(sum(1 for c in r["cmds"] if c[0] == "C") == 1 for r in (regs[0], regs[2])) and
       sum(1 for c in regs[1]["cmds"] if c[0] == "C") == 0,
       "".join(c[0] for c in regs[0]["cmds"]) + " / " +
       "".join(c[0] for c in regs[1]["cmds"]))
    ck("★ 每块 4 条边缘曲线（左/右襟 1C+3L，后片 4L）",
       all(len(r["edges"]) == 4 for r in regs) and
       [e["kind"] for e in regs[0]["edges"]] == ["C", "L", "L", "L"] and
       [e["kind"] for e in regs[1]["edges"]] == ["L", "L", "L", "L"])
    ck("★ 出图脚本能处理 C：real_bbox 对三块均返回有效框",
       all((lambda b: b[2] > b[0] and b[3] > b[1])(sheet.real_bbox(r["cmds"]))
           for r in regs))

    # ---- 贝塞尔解析定义 ----
    ap = rg["arc_approx"]
    ck("★ 60° 弧贝塞尔系数 k = 4/3·tan(Δθ/4)（Δθ=−60°）",
       abs(ap["k"] - 4.0 / 3.0 * math.tan(math.radians(-60.0) / 4.0)) < 1e-12,
       "k = %.9f" % ap["k"])
    cub = ap["control_points"]
    ck("★ 贝塞尔端点精确落在解析圆弧 P₂ / P₁",
       math.dist(tuple(cub[0]), tuple(cp["P2"])) < 1e-9 and
       math.dist(tuple(cub[3]), tuple(cp["P1"])) < 1e-9,
       "err %.3e / %.3e mm" % (math.dist(tuple(cub[0]), tuple(cp["P2"])),
                               math.dist(tuple(cub[3]), tuple(cp["P1"]))))
    ck("★ 贝塞尔近似径向偏差 < 0.01mm（量化「近似」）",
       ap["max_radial_error_mm"] < 0.01,
       "%.9f mm" % ap["max_radial_error_mm"])

    # ---- 积分面积 ----
    ck("★ 每块解析格林积分 ½∮(x dy−y dx) 与 sheet.sample 鞋带吻合（<1e-3 mm²）",
       all(abs(r["area_diff"]) < 1e-3 for r in regs),
       " / ".join("%.2e" % r["area_diff"] for r in regs))
    ck("★ 后片领子＝梯形公式 ½(100+A—A′)·rise（全直线，解析精确）",
       abs(regs[1]["area"] - 0.5 * (100.0 + cp["AA"]) * cp["rise_above_top"]) < 1e-9,
       "%.9f mm²" % regs[1]["area"])
    ck("★ 三块面积和 = 2×左襟 + 后片",
       abs(rg["area_total"] - (2 * regs[0]["area"] + regs[1]["area"])) < 1e-9,
       "%.9f mm²" % rg["area_total"])
    ck("★ 三块面积和 ≠ 旧「等宽直条 L×h」（领条算错已纠正）",
       abs(rg["area_diff_vs_old"]) > 1.0,
       "新 %.6f / 旧 %.6f / 差 %+.6f mm²"
       % (rg["area_total"], rg["old_strip_area"], rg["area_diff_vs_old"]))

    # ---- 右襟 = 左襟镜像 ----
    ck("★ 右襟 cmds = 左襟关于 x=0 镜像（mirror_cmds，含 C 的 x 取负）",
       regs[2]["cmds"] == geo.mirror_cmds(regs[0]["cmds"]))
    ck("★ 右襟面积 = 左襟面积（反射等距，解析严格相等）",
       abs(regs[2]["area"] - regs[0]["area"]) < 1e-9,
       "%.9f mm²" % regs[2]["area"])
    ck("★ 右襟边缘曲线 = 左襟逐条镜像",
       all(abs(regs[2]["edges"][i]["a"][0] + regs[0]["edges"][i]["a"][0]) < 1e-9
           for i in (1, 2, 3)))

    # ---- 共边拼接 ----
    eL, eB, eR = regs[0]["edges"], regs[1]["edges"], regs[2]["edges"]
    ck("★ 左襟宽度边 P₁A 与后片 A→P₁ 共边（端点集合相同）",
       {tuple(q) for q in (eL[1]["a"], eL[1]["b"])} ==
       {tuple(q) for q in (eB[3]["a"], eB[3]["b"])})
    ck("★ 右襟宽度边 P₁′A′ 与后片 P₁′A′ 共边（端点集合相同）",
       {tuple(q) for q in (eR[1]["a"], eR[1]["b"])} ==
       {tuple(q) for q in (eB[1]["a"], eB[1]["b"])})
    ck("★ 平裁口径：无三维法向 / 可展性假设（flat_cut=True）",
       rg["flat_cut"] is True)

    # ---- 片表完整性 ----
    ck("★ 完整裁片图 = 前片 2 + 后片 2 + 领条 3，共 7 片",
       len(pieces) == 7 and sum(p["qty"] for p in pieces) == 7,
       "%d 片 / qty 合计 %d" % (len(pieces), sum(p["qty"] for p in pieces)))
    ck("★ 领条三片 grain 沿用模板「领缘条」[1,0]",
       all(by[r["name"]]["grain"] == list(tpl_collar["grain"]) for r in regs))
    ck("★ 领条三片 cmds 与 geo.collar_regions() 逐项相同",
       all(by[r["name"]]["cmds"] == r["cmds"] for r in regs))
    ck("★ 片内 note 标注积分面积（≤16 字）",
       all(by[r["name"]]["note"].startswith("A=") and
           len(by[r["name"]]["note"]) <= 16 for r in regs))

    # ---- 前 / 后片几何未改 ----
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

    return sum(oks), len(oks) - sum(oks)


def _tx(s):
    """SVG 文本 XML 转义：裸 < / > / & 会让整个 SVG 非法、Edge 拒渲染成白图。"""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_regions_zoom(rg):
    """领子三块放大图：形状（贝塞尔曲边）/ 边缘曲线 / 积分面积，一图看全。
    路径直接调 sheet.path_d()（出图脚本自己的 C 命令），不再手搓采样折线。"""
    regs = rg["regions"]
    INK, RED, BLUE, GRAY = "#1a1a1a", "#c0392b", "#1f5fa8", "#6a6a6a"
    PADX, COLW, TOP = 44.0, 128.0, 108.0
    VH = 108.0 + 104.0 + 176.0
    VW = 2 * PADX + 3 * COLW
    PX = 5

    def T(x, y, txt, size=4.4, anchor="start", color=INK, weight="400"):
        return ('<text x="%.3f" y="%.3f" font-family="sans-serif" font-size="%.2f" '
                'fill="%s" text-anchor="%s" font-weight="%s">%s</text>'
                % (x, y, size, color, anchor, weight, _tx(txt)))

    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %.3f %.3f">' % (int(VW * PX), int(VH * PX), VW, VH),
         '<rect width="100%" height="100%" fill="#ffffff"/>']
    s.append(T(PADX, 22, "第 5 步 · 领子三块（平裁平面区域 · 贝塞尔曲边 · 积分面积）", 8.0, weight="600"))
    s.append(T(PADX, 36, "60° 弧＝三次贝塞尔 C（k=4/3·tan(Δθ/4)）；直线边＝L；cmds 仅 M/L/C/Z，与 sheet.py 出图定义一致",
               4.2, color=GRAY))
    s.append(T(PADX, 48, "面积＝½∮(x dy−y dx)：直线段叉积 + 贝塞尔幂基解析积分；sheet.sample(4096) 鞋带独立交叉验证",
               4.2, color=GRAY))

    for i, r in enumerate(regs):
        x0, y0, x1, y1 = sheet.real_bbox(r["cmds"])
        colx = PADX + i * COLW
        ox = colx + 10.0 - x0
        oy = TOP + y1
        s.append(T(colx, 68, r["name"], 5.6, weight="600"))
        s.append(T(colx, 78, r["role"], 3.9, color=GRAY))
        # 轮廓（出图脚本自己的 C 命令）
        s.append('<path d="%s" stroke="%s" stroke-width="0.9" fill="none" '
                 'stroke-linejoin="round"/>' % (sheet.path_d(r["cmds"], ox, oy), INK))
        # 曲边 C 段红色高亮
        cur = None
        for c in r["cmds"]:
            if c[0] in ("M", "L"):
                cur = c[1]
            elif c[0] == "C":
                seg = [["M", list(cur)], ["C", c[1], c[2], c[3]]]
                s.append('<path d="%s" stroke="%s" stroke-width="1.35" fill="none"/>'
                         % (sheet.path_d(seg, ox, oy), RED))
                cur = c[3]
        # 角点（构造点）
        verts = []
        for e in r["edges"]:
            qs = [e["a"], e["b"]] if e["kind"] == "L" else [e["ctrl"][0], e["ctrl"][-1]]
            for q in qs:
                t = tuple(q)
                if t not in verts:
                    verts.append(t)
        for q in verts:
            s.append('<circle cx="%.3f" cy="%.3f" r="1.6" fill="#ffffff" '
                     'stroke="%s" stroke-width="0.6"/>' % (q[0] + ox, oy - q[1], RED))
        # 积分面积数据
        yb = TOP + 104.0 + 10.0
        s.append(T(colx, yb, "A = %.6f mm²" % r["area"], 5.4, weight="600", color=BLUE))
        s.append(T(colx, yb + 10, "鞋带 %.6f　差 %.2e" % (r["area_numeric"], r["area_diff"]),
                   3.8, color=GRAY))
        s.append(T(colx, yb + 19, "边缘曲线周长 ∫ds = %.6f mm" % r["perimeter"], 3.8, color=GRAY))
        s.append(T(colx, yb + 31, "边缘曲线（%d 条）：" % len(r["edges"]), 4.0))
        for j, e in enumerate(r["edges"]):
            s.append(T(colx, yb + 40 + j * 9,
                       "  %s  %s" % (e["kind"], e["name"]), 3.4,
                       color=RED if e["kind"] == "C" else GRAY))

    by = VH - 58.0
    for j, ln in enumerate([
        "总面积 = %.6f mm²　｜　旧「等宽直条 L×h」= %.6f mm²　｜　差 = %.6f mm²"
        % (rg["area_total"], rg["old_strip_area"], rg["area_diff_vs_old"]),
        "右襟块＝左襟块关于 x=0 镜像；三块沿 P₁A / P₁′A′ 共边拼接＝第 4 步一条连续竖起领子",
        "平裁：上身立起是空间遮挡折叠关系，裁片本身为平面；不扣减交叠量",
        "贝塞尔近似最大径向偏差 = %.6f mm（R = %.3f mm，60° 单段）"
        % (rg["arc_approx"]["max_radial_error_mm"], geo.ARC_R),
    ]):
        s.append(T(PADX, by + j * 12, ln, 4.0, color=GRAY))
    s.append('</svg>')

    svg = os.path.join(OUT, "step5_领子三块放大.svg")
    open(svg, "w", encoding="utf-8").write("\n".join(s))
    png = os.path.join(OUT, "step5_领子三块放大.png")
    make_png(svg, png)
    return svg, png


def main():
    rg = geo.collar_regions()
    pieces = geo.sheet_pieces_step5()
    regs = rg["regions"]

    print("=== 领子按衣片分三块（平裁平面区域）===")
    print("  曲边：60° 弧 → 三次贝塞尔 C，k = %.9f，最大径向偏差 %.9f mm"
          % (rg["arc_approx"]["k"], rg["arc_approx"]["max_radial_error_mm"]))
    for r in regs:
        print("  %-24s cmds=%-8s 面积 %15.9f mm²（数值 %15.9f，差 %.2e）"
              % (r["name"], "".join(c[0] for c in r["cmds"]),
                 r["area"], r["area_numeric"], r["area_diff"]))
    print("  总面积 = %.9f mm²　｜　旧等宽直条 %.9f mm²　｜　差 %+.9f mm²"
          % (rg["area_total"], rg["old_strip_area"], rg["area_diff_vs_old"]))

    print("\n=== 自检 ===")
    npass, nfail = selftest(rg, pieces)
    print("\n自检：%d PASS / %d FAIL" % (npass, nfail))

    # 排版：领条三片只有 58.6 / 100 / 58.6 mm 宽，长片名会互相压住；
    # 默认 200mm 片距也会让 05/06 与前/后片挤在同一行。只调排版间距，不碰几何、不改 sheet.py 源码。
    sheet.GAP = 420.0

    params = dict(
        L=geo.L, LAP_DX=geo.LAP_DX, VP1=geo.R_EQUAL, VP2=geo.R_EQUAL,
        ARC_R=geo.ARC_R, ARC_SWEEP_DEG=geo.ARC_SWEEP_DEG,
        ARC_LEN=round(geo.ARC_LENGTH, 9), COLLAR_H=geo.COLLAR_H,
        BEZIER_K=round(rg["arc_approx"]["k"], 9),
        BEZIER_RADIAL_ERR=round(rg["arc_approx"]["max_radial_error_mm"], 9),
        AREA_LEFT=round(regs[0]["area"], 6),
        AREA_BACK=round(regs[1]["area"], 6),
        AREA_RIGHT=round(regs[2]["area"], 6),
        AREA_TOTAL=round(rg["area_total"], 6),
        OLD_STRIP_AREA=round(rg["old_strip_area"], 6),
    )
    svg = os.path.join(OUT, "step5_完整裁片图.svg")
    info = sheet.write_sheet(params, pieces, svg, TITLE, SUBTITLE, NOTES)

    try:
        ET.parse(svg)
        xml_ok = True
    except Exception as e:
        xml_ok = False
        print("  SVG XML FAIL:", e)

    zsvg, zpng = make_regions_zoom(rg)
    try:
        ET.parse(zsvg)
        zoom_xml_ok = True
    except Exception as e:
        zoom_xml_ok = False
        print("  放大图 SVG XML FAIL:", e)

    data = {
        "step": 5,
        "action": "领子按衣片分三块（前片左襟 / 后片 / 前片右襟＝左襟镜像），"
                  "各自边缘曲线 + 积分面积；完整裁片图 7 片",
        "user_orders": [
            "2026-11-11 14:24「算出前片左襟领子形状，边缘曲线，积分得到面积，"
            "算出后片领子形状，边缘曲线，积分得到面积，右襟前片由左襟镜像得到」",
            "2026-11-11 14:35「用贝塞尔近似，出图用什么你就用什么」",
            "「这不是立裁，这是平裁」「上身立起，平铺平面」",
        ],
        "negated": [
            "12:29 等宽直条领条 L×h",
            "12:52 立裁法向贴附（绿色对比图 verify_fit.py）",
            "14:24 前中交叠量 / 类将军饮马反射展开",
            "14:35 把弧边退化成采样折线",
        ],
        "basis": {
            "template": os.path.basename(geo.TPL_PATH),
            "profile": geo.PROFILE, "size": geo.SIZE, "L": geo.L,
            "readonly": True, "geometry_changed": False,
        },
        "regions": rg,
        "old_equal_width_strip": {
            "length": geo.collar_integral()["length"],
            "width": geo.COLLAR_H,
            "area": rg["old_strip_area"],
            "note": rg["old_strip_area_note"],
        },
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
        "note": "前 / 后片 cmds 与模板逐项相同；领条三块是新增平面曲边裁片；未推断第 6 步。",
    }
    json.dump(data, open(os.path.join(OUT, "step5.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n=== 产物 ===")
    print("  ", info["svg"])
    print("  ", info["side"])
    for p in info["pieces"]:
        print("   %s ×%d：%.1f × %.1f mm" % (p["name"], p["qty"], p["w"], p["h"]))
    png = os.path.join(OUT, "step5_完整裁片图.png")
    print("   PNG:", make_png(svg, png))
    if os.path.exists(png):
        print("   PNG 字节:", os.path.getsize(png))
    print("  ", os.path.join(OUT, "step5.json"))
    print("  放大图:", zsvg)
    if os.path.exists(zpng):
        print("  放大图 PNG 字节:", os.path.getsize(zpng))
    return 0 if (nfail == 0 and xml_ok and zoom_xml_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
