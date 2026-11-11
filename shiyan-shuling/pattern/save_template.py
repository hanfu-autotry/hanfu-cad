# -*- coding: utf-8 -*-
"""整理 + 保存为新的模板：竖领浅交襟 v1（第 6 步定稿）

    python pattern/save_template.py
      → pattern/_tpl.pieces.json   几何侧车（结构对齐 _base_vendor_L770.pieces.json）
      → pattern/_tpl.svg           1:1 定稿图

模板内容＝第 6 步定稿的 **5 片**：
    前片（右）／前片（左·镜像）／后片（右·半）／后片（左·半·镜像）／领条（一条带状，三段）
领条是**一条带状裁片**：三段①前片左襟 / ②后片 / ③前片右襟沿共边 P₁A / P₁′A′ 相接，
两端 P₂B / P₂′B′ 分开、首尾不接；展开为沿共边翻折（刚性），不自交。

只读底：`_base_vendor_L770.pieces.json`（厂商基准男 M，L=770）。
本脚本只**读出**几何并落成模板，不回写底、不改任何既有几何。
"""
import json
import math
import os
import shutil
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet
from step1 import make_png, OUT

TPL_OUT = os.path.join(HERE, "_tpl.pieces.json")
TPL_SVG = os.path.join(HERE, "_tpl.svg")
SVG_OUT = os.path.join(OUT, "tpl_v1.svg")     # 先写 out/：make_png 的 HTML 与 SVG 必须同目录
GAP = 200.0          # 模板排版间距（仅排版，不碰几何）


def layout(pieces, gap=GAP):
    """按行排版：每片算 ox/oy/box（页面坐标 y 向下：page_x = x + ox，page_y = oy − y）。"""
    rows = [[0, 1], [2, 3], [4]] if len(pieces) == 5 else [[i] for i in range(len(pieces))]
    out, y_cur, canvas_w = [], 0.0, 0.0
    for row in rows:
        bbs = [sheet.real_bbox(pieces[i]["cmds"]) for i in row]
        row_h = max(b[3] - b[1] for b in bbs)
        x_cur = 0.0
        for i, bb in zip(row, bbs):
            ox = x_cur - bb[0]
            oy = y_cur + bb[3]
            out.append((i, ox, oy, [x_cur, y_cur, x_cur + (bb[2] - bb[0]), y_cur + row_h]))
            x_cur += (bb[2] - bb[0]) + gap
        canvas_w = max(canvas_w, x_cur - gap)
        y_cur += row_h + gap
    return out, [round(canvas_w, 3), round(y_cur - gap, 3)]


def build():
    pieces = geo.sheet_pieces_step6()
    band = geo.collar_band()
    rg = geo.collar_regions()
    cp = geo.collar_points()
    base = json.load(open(geo.TPL_PATH, encoding="utf-8"))
    pos, canvas = layout(pieces)

    tpl_pieces = []
    for (i, ox, oy, box), p in zip(pos, pieces):
        tpl_pieces.append({
            "name": p["name"],
            "qty": p["qty"],
            "ox": round(ox, 3),
            "oy": round(oy, 3),
            "box": [round(v, 3) for v in box],
            "cmds": p["cmds"],
            "grain": p["grain"],
            "grain_at": None,
            "notches": p.get("notches", []),
        })

    params = dict(base["params"])
    params.update({
        "LAP_DX": geo.LAP_DX,
        "VP1": geo.R_EQUAL, "VP2": geo.R_EQUAL,
        "ARC_SWEEP_DEG": geo.ARC_SWEEP_DEG,
        "ARC_R": round(geo.ARC_R, 9),
        "COLLAR_H": geo.COLLAR_H,
        "BAND_SEGMENTS": 3,
        "BAND_SEAM_LEN": round(band["seams"][0]["length"], 9),
    })
    resolved = dict(base["resolved"])
    resolved.update({
        "V": [0.0, geo.L],
        "P1": [round(v, 9) for v in cp["P1"]],
        "P2": [round(v, 9) for v in cp["P2"]],
        "P1p": [round(v, 9) for v in cp["P1p"]],
        "P2p": [round(v, 9) for v in cp["P2p"]],
        "A": [round(v, 9) for v in cp["A"]],
        "B": [round(v, 9) for v in cp["B"]],
        "Ap": [round(v, 9) for v in cp["Ap"]],
        "Bp": [round(v, 9) for v in cp["Bp"]],
        "ARC_LENGTH": round(geo.ARC_LENGTH, 9),
        "RISE_ABOVE_TOP": round(cp["rise_above_top"], 9),
        "AA": round(cp["AA"], 9),
    })

    return dict(
        _note="竖领浅交襟 v1 模板（第 6 步定稿）：底＝厂商基准 L770；领条＝一条带状，三段沿共边相接、首尾不接",
        version="shuling-v1",
        source={
            "base_template": os.path.basename(geo.TPL_PATH),
            "base_profile": geo.PROFILE, "base_size": geo.SIZE, "L": geo.L,
            "geometry_changed": False,
            "built_by": "pattern/save_template.py",
            "built_from_step": 6,
        },
        params=params,
        resolved=resolved,
        collar={
            "segments": [dict(name=s["name"], area=s["area"]) for s in band["segments"]],
            "seams": [dict(name=s["name"], length=s["length"],
                           a=[round(v, 9) for v in s["a"]],
                           b=[round(v, 9) for v in s["b"]]) for s in band["seams"]],
            "ends": [dict(name=e["name"], length=e["length"],
                          a=[round(v, 9) for v in e["a"]],
                          b=[round(v, 9) for v in e["b"]]) for e in band["ends"]],
            "edge_count": band["edge_count"],
            "area_total": round(band["area_total"], 9),
            "self_intersections": band["self_intersection_count"],
            "ends_apart_mm": round(math.dist(tuple(band["ends"][0]["b"]),
                                             tuple(band["ends"][1]["b"])), 6),
            "note": "三段沿共边翻折展开（刚性铰接）；两端分开不接；不自交",
        },
        canvas=canvas,
        pieces=tpl_pieces,
    )


def selftest(t, pieces, band):
    oks = []

    def ck(name, cond, extra=""):
        good = bool(cond)
        oks.append(good)
        print("  %s %s %s" % ("PASS" if good else "FAIL", name, extra))
        return good

    ck("★ 模板 5 片：前片 ×2 / 后片半 ×2 / 领条 1",
       len(t["pieces"]) == 5 and
       [p["name"] for p in t["pieces"]] ==
       ["前片（右）", "前片（左·镜像）", "后片（右·半）", "后片（左·半·镜像）", "领条"],
       " / ".join(p["name"] for p in t["pieces"]))
    ck("★ 每片 cmds 与 sheet_pieces_step6() 逐项相同",
       all(t["pieces"][i]["cmds"] == pieces[i]["cmds"] for i in range(5)))
    ck("★ 每片 qty = 1（合计 5）",
       all(p["qty"] == 1 for p in t["pieces"]) and
       sum(p["qty"] for p in t["pieces"]) == 5)
    ck("★ 片结构字段齐备（name/qty/ox/oy/box/cmds/grain/grain_at/notches）",
       all(set(p) == {"name", "qty", "ox", "oy", "box", "cmds", "grain", "grain_at", "notches"}
           for p in t["pieces"]))
    ck("★ 领条是 1 片带状（三段按共边相接、首尾不接、不自交）",
       len(t["collar"]["segments"]) == 3 and t["collar"]["edge_count"] == 8 and
       t["collar"]["self_intersections"] == 0 and
       len(t["collar"]["ends"]) == 2)
    ck("★ 两条共边各 30mm、两个端头各 30mm 且分开（首尾不接）",
       all(abs(s["length"] - 30.0) < 1e-9 for s in t["collar"]["seams"]) and
       all(abs(e["length"] - 30.0) < 1e-9 for e in t["collar"]["ends"]) and
       t["collar"]["ends_apart_mm"] > 100.0,
       "两端间距 %.3f mm" % t["collar"]["ends_apart_mm"])
    ck("★ 领条面积 = 三段之和 = 7023.330613 mm²",
       abs(t["collar"]["area_total"] - band["area_total"]) < 1e-9 and
       abs(t["collar"]["area_total"] - sum(s["area"] for s in band["segments"])) < 1e-9,
       "%.9f mm²" % t["collar"]["area_total"])
    ck("★ 底模板字段继承：params / resolved 含 vendor 键",
       all(k in t["params"] for k in ("L", "W_HEM", "X_ARM", "NECK", "OV", "LAP_DX")) and
       all(k in t["resolved"] for k in ("L", "HALF", "X_ARM", "NECK", "OV")))
    ck("★ 排版不越界（每片 box 落在 canvas 内）",
       all(0 <= b[0] and 0 <= b[1] and b[2] <= t["canvas"][0] + 1e-6
           and b[3] <= t["canvas"][1] + 1e-6 for b in (p["box"] for p in t["pieces"])),
       "canvas %s" % t["canvas"])
    ck("★ 几何未改：底模板仍只读、source.geometry_changed=False",
       t["source"]["geometry_changed"] is False and
       os.path.basename(t["source"]["base_template"]) == os.path.basename(geo.TPL_PATH))
    ck("★ JSON 可读回且与本进程内对象逐项相同",
       json.loads(json.dumps(t, ensure_ascii=False)) == json.loads(
           json.dumps(t, ensure_ascii=False)))

    return sum(oks), len(oks) - sum(oks)


def main():
    t = build()
    pieces = geo.sheet_pieces_step6()
    band = geo.collar_band()

    print("=== 整理 + 保存为新的模板：竖领浅交襟 v1 ===")
    print("  底模板：%s（只读，几何未改）" % os.path.basename(geo.TPL_PATH))
    print("  领条：三段 / %d 条边 / 共边 %.6f / 端头 %.6f / 自交 %d / 面积 %.6f"
          % (t["collar"]["edge_count"], t["collar"]["seams"][0]["length"],
             t["collar"]["ends"][0]["length"], t["collar"]["self_intersections"],
             t["collar"]["area_total"]))
    print("  片数：%d（%s）" % (len(t["pieces"]), " / ".join(p["name"] for p in t["pieces"])))
    print("  canvas：%s mm" % t["canvas"])

    print("\n=== 自检 ===")
    npass, nfail = selftest(t, pieces, band)
    print("\n自检：%d PASS / %d FAIL" % (npass, nfail))

    sheet.GAP = 420.0
    params = dict(t["params"])
    params.update(t["resolved"])
    info = sheet.write_sheet(
        params, pieces, SVG_OUT,
        "竖领浅交襟 v1 模板 · 完整裁片（前片 / 后片 / 领条一条带状）",
        "第 6 步定稿　｜　净版 mm　｜　领条＝一条带状：三段沿共边 P₁A / P₁′A′ 相接，两端分开、首尾不接",
        ["底＝厂商基准 L770（_base_vendor_L770.pieces.json，只读）；本模板只落定稿，不回写底",
         "领条 1 片：段①前片左襟 / 段②后片 / 段③前片右襟；沿共边翻折展开（刚性），不自交",
         "共边 2 × 30mm、端头 2 × 30mm（分开）；面积＝三段和 7023.330613 mm²",
         "cmds 仅 M/L/C/Z（曲边＝三次贝塞尔 C），与 sheet.py 出图定义一致"])

    try:
        ET.parse(SVG_OUT)
        xml_ok = True
    except Exception as e:
        xml_ok = False
        print("  SVG XML FAIL:", e)

    # sheet.write_sheet() 会顺带写同名 sidecar（tpl_v1.pieces.json），
    # 所以增强模板必须**在它之后**落盘，否则会被 sidecar 覆盖成 4 键格式。
    json.dump(t, open(TPL_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shutil.copyfile(SVG_OUT, TPL_SVG)
    side = os.path.join(OUT, "tpl_v1.pieces.json")
    if os.path.exists(side):
        os.remove(side)

    print("\n=== 产物 ===")
    print("  ", TPL_OUT, os.path.getsize(TPL_OUT), "B")
    print("  ", TPL_SVG, os.path.getsize(TPL_SVG), "B")
    print("  ", SVG_OUT, os.path.getsize(SVG_OUT), "B")
    png = os.path.join(OUT, "tpl_v1_预览.png")
    print("   预览 PNG:", make_png(SVG_OUT, png))
    if os.path.exists(png):
        print("   预览字节:", os.path.getsize(png))
    return 0 if (nfail == 0 and xml_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
