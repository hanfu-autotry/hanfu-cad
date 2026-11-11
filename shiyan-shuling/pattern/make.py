# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 一键出图（studio 契约入口）

    python pattern/make.py --size 本案 --out out
    python pattern/make.py --size 本案 --out out --dump-params

产物（写进 `--out` 目录）：
    竖领浅交襟_<size>.svg          裁片图（1:1，mm；5 片）
    竖领浅交襟_<size>.pieces.json  几何侧车（studio 读它做排料 / DXF）

口径：底＝厂商基准半臂 L770（`_base_vendor_L770.pieces.json`，**只读**）；
领条＝**一条带状**——三段①前片左襟 / ②后片 / ③前片右襟沿共边 P₁A / P₁′A′ 相接，
两端 P₂B / P₂′B′ 分开、**首尾不接**；展开为沿共边翻折（刚性），不自交。
本版型是**定稿几何（第 6 步）**，暂无旋钮；`--params` 只接受空对象。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet

NAME = "竖领浅交襟"
SIZES = {"本案": dict(L=geo.L)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sex", default="男")
    ap.add_argument("--size", default="本案")
    ap.add_argument("--out", default=os.path.join(ROOT, "out"))
    ap.add_argument("--params", default=None, help="旋钮覆盖（JSON）；本版型暂无旋钮")
    ap.add_argument("--dump-params", action="store_true",
                    help="只打印当前参数（JSON，供界面滑杆取基准），不出图")
    a = ap.parse_args()

    if a.size not in SIZES:
        raise SystemExit("未知号型 %s；本版型可用：%s" % (a.size, "、".join(SIZES)))
    ov = json.loads(a.params) if a.params else {}
    if ov:
        raise SystemExit("本版型暂无旋钮（定稿几何）；未知参数：%s" % "、".join(sorted(ov)))
    if a.dump_params:
        print(json.dumps(dict(kind="params", sex=a.sex, size=a.size, params={}),
                         ensure_ascii=False))
        return 0

    band = geo.collar_band()
    pieces = geo.sheet_pieces_step6()
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, "%s_%s" % (NAME, a.size))

    sheet.GAP = 420.0   # 仅排料间距；不碰几何、不改 sheet.py
    info = sheet.write_sheet(
        dict(L=geo.L, ARC_R=geo.ARC_R, ARC_SWEEP_DEG=geo.ARC_SWEEP_DEG,
             COLLAR_H=geo.COLLAR_H, BAND_EDGES=band["edge_count"],
             SEAM=round(band["seams"][0]["length"], 3),
             ENDS_APART=round(__import__("math").dist(
                 tuple(band["ends"][0]["b"]), tuple(band["ends"][1]["b"])), 3),
             AREA=round(band["area_total"], 3)),
        pieces, stem + ".svg",
        "试验竖领浅交襟 · 裁片图 · %s" % a.size,
        "底＝厂商基准半臂 L770（只读）　｜　净版　mm　｜　领条＝一条带状：三段沿共边 P₁A / P₁′A′ 相接，两端分开、首尾不接",
        ["前片 ×2（右 / 左·镜像）：cmds 与模板逐项相同，几何未改",
         "后片半 ×2（右 / 左·镜像）：模板「后片半」原样 + 关于 x=0 镜像",
         "领条 ×1：一条带状 —— 段①前片左襟 / 段②后片 / 段③前片右襟，沿共边相接；两端 P₂B / P₂′B′ 分开不接",
         "共边 2×30mm、端头 2×30mm；面积＝三段和 %.3f mm²；自交 0" % band["area_total"]])

    print(json.dumps(dict(size=a.size, sex=a.sex, svg=info["svg"], pieces_json=info["side"],
                          canvas=info["size"], pieces=info["pieces"]),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
