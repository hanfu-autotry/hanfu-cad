# -*- coding: utf-8 -*-
"""唐圆领 · studio 版型入口（patterns.json 里 run.kind=make）。

只做「把已有几何打包成 studio 认识的产物」，不重写任何版型几何：

    python pattern/make.py --sex — --size 本案 --out <dir> [--params '{"COLLAR_W":80}']
    python pattern/make.py --sex — --size 本案 --dump-params

产物：<out>/唐圆领_本案.svg（四片裁片图 1:1）＋ 同名 .pieces.json。
出图走 `sheet.write_sheet`（照搬 ming-gaojiaoling），图层与图签跟其它版型一致。
可调参数只暴露项目里已定义的四个量，其余几何全部由 geo.py 派生。
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet

_U0 = geo.xuren_dir(geo.derive(geo.CASE))
BASE = dict(
    P_SHIFT=geo.P_SHIFT,
    COLLAR_W=geo.COLLAR_W,
    COLLAR_SPLIT=geo.COLLAR_SPLIT,
    XUREN_TILT_DEG=round(math.degrees(math.atan2(_U0[0], _U0[1])), 4),
)

# 照 ming-gaojiaoling/pattern/make.py 的口径：可被 --params 覆盖的键即 NUM_KEYS。
# 这里只列项目里已定义、且改动后几何确实联动的四个量；
# CASE 里的 L/NECK 等属于模板只读来源，改了后片不会跟着动，故不挂旋钮。
SIZES = {"本案": geo.CASE}
NUM_KEYS = dict(BASE)

STEM = "唐圆领_本案"


def build(d, out):
    os.makedirs(out, exist_ok=True)
    pieces = geo.sheet_pieces(d)
    F = geo.full_collar_data(d)
    X = geo.xuren_data(d)
    _P, Pp = geo.neck_points(d)
    _C, r = geo.neck_circle(d)
    cl, cw = F["flat"]["length"], F["flat"]["width"]
    n_pieces = sum(p["qty"] for p in pieces)
    info = sheet.write_sheet(
        d, pieces, os.path.join(out, STEM + ".svg"),
        "唐圆领 · 裁片图 · %s" % (d.get("name") or "本案"),
        "底片＝ming-gaojiaoling 模板后片　｜　净版　mm　｜　后片不挖领",
        [
            "前片原生（中缝右边）×2：圆领＝以 PP′ 为直径的下半圆，P 沿顶边右移 %.0f，"
            "r＝%.0f；肩/袖/腋圆角/侧缝/摆沿用模板" % (d["P_SHIFT"], r),
            "前片续衽（中缝左边）×2：左缘＝过 P′(%.1f, %.1f) 的直线（倾角 %.1f°），"
            "下端＝左缘∩下摆；面积＝½∮(x dy−y dx)＝%.1f"
            % (Pp[0], Pp[1], X["tilt_deg"], X["integral"]["area"]),
            "后片（半·模板原样）×2：不挖后领，顶边到后中保持模板那条水平直线；"
            "后中缝是拼幅缝，故半片 ×2，不拼成整片",
            "领条（全衣一条）×1：长＝∫ds＝2πr+2r＝%.1f，宽＝%.0f，开放不闭合；"
            "内襟＝前片镜像、内襟续衽＝续衽镜像；共 %d 片（红线十字＝刀口，绿箭头＝直丝）"
            % (cl, cw, n_pieces),
        ])
    return dict(svg=info["svg"], pieces_json=info["side"], canvas=info["size"],
                pieces=len(info["pieces"]), n_pieces=n_pieces,
                grid=[dict(name=p["name"], qty=p["qty"],
                           w=p["w"], h=p["h"]) for p in info["pieces"]])


def main():
    ap = argparse.ArgumentParser(description="唐圆领 · studio 版型入口")
    ap.add_argument("--sex", default="—")
    ap.add_argument("--size", default="本案", choices=sorted(SIZES))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "out"))
    ap.add_argument("--params", default=None)
    ap.add_argument("--dump-params", action="store_true")
    ap.add_argument("--ease", default=None)
    ap.add_argument("--profile", default=None)
    a = ap.parse_args()

    ov = json.loads(a.params) if a.params else {}
    bad = sorted(set(ov) - set(NUM_KEYS))
    if bad:
        raise SystemExit("未知参数 %s；这个版型可用：%s"
                         % ("、".join(bad), "、".join(sorted(NUM_KEYS))))
    p = dict(NUM_KEYS)
    p.update({k: float(v) for k, v in ov.items()})
    if a.dump_params:
        print(json.dumps(dict(kind="params", sex=a.sex, size=a.size, params=p),
                         ensure_ascii=False))
        return

    d = geo.derive(SIZES[a.size])
    d.update({k: float(v) for k, v in p.items()})
    info = build(d, a.out)
    info.update(size=a.size, sex=a.sex, params=p)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
