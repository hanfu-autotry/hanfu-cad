# -*- coding: utf-8 -*-
"""直领对襟 · 第 1 步：在现有模板上只留领条与后片，再复制后片为前片

    python pattern/step1.py
      → out/step1_领条与后片.svg
      → out/step1_领条与后片.pieces.json

底＝hanfu-cad（对穿交半臂）的裁片图，只读。
本步只做三件事：① 移除模板里除领条、后片以外的所有片；
② 后片复制一份；③ 复制件命名为「前片」。几何一处不改。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

grid = geo.sheet_pieces()
_cl, _cw = geo.collar_size()
info = sheet.write_sheet(
    geo.PARAMS, grid, os.path.join(OUT, "step1_领条与后片.svg"),
    "直领对襟 · 第 1 步 · 只留领条与后片",
    "底＝hanfu-cad 对穿交半臂裁片（只读）　｜　净版　mm　｜　几何未改",
    [
        "① 在现有模板基础上移除所有，只留领条（＝模板领缘条 %.0f×%.0f）与后片（＝模板后片半）"
        % (_cl, _cw),
        "② 后片复制一份，③ 复制件命名为前片 —— 两者几何完全相同，没有做任何修改",
        "本步共 3 种片：领条 ×1 ／ 后片 ×2 ／ 前片 ×2",
        "已移除：模板前片、三角拼接 A/B、系带、下摆绢衬条",
    ])

print(info["svg"])
print(info["side"])
for p in info["pieces"]:
    print("  %s ×%d：%.1f × %.1f mm" % (p["name"], p["qty"], p["w"], p["h"]))
