# -*- coding: utf-8 -*-
"""唐圆领 · 第 8 步：完整裁片图

    python pattern/step6.py [--tilt 20]
      → out/裁片图.svg / out/裁片图.png
      → out/裁片图.pieces.json
      → out/裁片数据.json

四片各自摊开、1:1（mm）：领条 / 前片原生 / 前片续衽 / 后片（半·模板原样）。
内襟＝前片原生的镜像、内襟续衽＝前片续衽的镜像，故 qty 记 2，不另画。

出图与 studio 版型入口（make.py）**同一套排版器**（sheet.write_sheet，照搬
ming-gaojiaoling）：图层 OUTLINE/NOTCH/MARK/AUX_PATH/GRAIN/DIM/LABEL/BLOCK/SCALE
一致。后片按「模板后片半 ×2」画，不拼成整片（与明制高交领/接袖/深衣同口径）。
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

ap = argparse.ArgumentParser(description="唐圆领完整裁片图")
ap.add_argument("--tilt", type=float, default=None,
                help="续衽左缘与竖直方向夹角（度）")
_args = ap.parse_args()

d = geo.derive(geo.CASE)
if _args.tilt is not None:
    d["XUREN_TILT_DEG"] = _args.tilt

X = geo.xuren_data(d)
F = geo.full_collar_data(d)
grid = geo.sheet_pieces(d)
_tilt = X["tilt_deg"]
_tilt_s = ("%.1f°" % _tilt) if _tilt is not None else "平行衣身左缘"
out_dir = os.path.join(ROOT, "out")
os.makedirs(out_dir, exist_ok=True)

info = sheet.write_sheet(
    d, grid, os.path.join(out_dir, "裁片图.svg"),
    "唐圆领 · 裁片图（过程稿）",
    "底片＝ming-gaojiaoling 模板后片　｜　净版　mm　｜　后片不挖领",
    [
        "前片原生（中缝右边）×2：圆领＝以 PP′ 为直径的下半圆；肩/袖/腋圆角/侧缝/摆沿用模板",
        "前片续衽（中缝左边）×2：左缘＝过 P′ 的直线（%s），下端＝左缘∩下摆；"
        "面积＝½∮(x dy−y dx)＝%.1f" % (_tilt_s, X["integral"]["area"]),
        "后片（半·模板原样）×2：不挖后领，顶边到后中保持模板那条水平直线",
        "领条（全衣一条）×1：长＝∫ds＝2πr+2r＝%.1f，宽＝%.0f，开放不闭合；"
        "内襟＝前片镜像、内襟续衽＝续衽镜像；共 %d 片"
        % (F["flat"]["length"], F["flat"]["width"], sum(p["qty"] for p in grid)),
    ])

data = geo.piece_data(d)
data["sheet"] = dict(
    note="裁片图上真正排的四片（后片按半片 ×2，与其它版型同口径）",
    canvas=info["size"],
    pieces=[dict(name=p["name"], qty=p["qty"], w=p["w"], h=p["h"])
            for p in info["pieces"]])
jpath = os.path.join(out_dir, "裁片数据.json")
with open(jpath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(info["svg"])
print(jpath)
for p in info["pieces"]:
    print("  %s ×%d：%.1f × %.1f mm" % (p["name"], p["qty"], p["w"], p["h"]))
print("领条 %.2f × %.0f（开放，三段：%s）"
      % (F["flat"]["length"], F["flat"]["width"],
         " / ".join("%.2f" % sg["exact"] for sg in F["segments"])))
