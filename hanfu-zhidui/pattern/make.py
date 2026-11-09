# -*- coding: utf-8 -*-
"""直领对襟 · studio 版型入口（patterns.json 里 run.kind=make）。

    python pattern/make.py --sex — --size 本案 --out <dir> [--params '{"NECK_W":180}']
    python pattern/make.py --sex — --size 本案 --dump-params

产物：<out>/直领对襟_本案.svg（三片裁片图 1:1）＋ 同名 .pieces.json。
几何全部来自 geo.py（模板只读 + 原始直领 V1 的 _DEF），这里只打包，不改版型。
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

SIZES = {"本案": geo.params()}
NUM_KEYS = dict(geo.DEFAULTS)
STEM = "直领对襟_本案"


def build(q, out):
    os.makedirs(out, exist_ok=True)
    grid = geo.sheet_pieces(geo.step2_pieces(q), step=2, q=q)
    CL, CW = geo.collar_size(q)
    FL = geo.neck_cut_len(q)
    show_back = q["NECK_W"] - q["LAPEL_FOLD"] * 2
    info = sheet.write_sheet(
        q, grid, os.path.join(out, STEM + ".svg"),
        "直领对襟 · 裁片图 · 本案",
        "底＝hanfu-cad 对穿交半臂的后片（只读）　｜　领襟口径＝通裁·原始直领交襟衣 V1"
        "　｜　净版 mm",
        [
            "开领宽 %.0f：前片沿中缝侧全高切掉 %.0f，前襟边 %.1f；开领宽＝两条剪口线间距"
            % (q["NECK_W"], q["NECK_W"] / 2.0, FL),
            "领条（全衣一条）×1：长 %.1f ＝ 2×前襟 %.1f ＋ 后领段 %.0f（＝开领宽），"
            "宽 %.0f；两条 notch ＝ 后领段两端" % (CL, FL, q["NECK_W"], CW),
            "装领条：压在剪口线上，每边可见 %.0f，中间露出后片 %.0f；"
            "后领由领条立起 %.0f" % (q["LAPEL_FOLD"], show_back, q["NECK_H"]),
            "后片＝模板后片半原样 ×2（不挖领）；内襟/外襟不做，对襟左右各一片前片",
        ])
    return dict(svg=info["svg"], pieces_json=info["side"], canvas=info["size"],
                pieces=len(info["pieces"]),
                n_pieces=sum(p["qty"] for p in grid),
                grid=[dict(name=p["name"], qty=p["qty"], w=p["w"], h=p["h"])
                      for p in info["pieces"]])


def main():
    ap = argparse.ArgumentParser(description="直领对襟 · studio 版型入口")
    ap.add_argument("--sex", default="—")
    ap.add_argument("--size", default="本案", choices=sorted(SIZES))
    ap.add_argument("--out", default=os.path.join(ROOT, "out"))
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
    q = geo.params(ov)
    if a.dump_params:
        print(json.dumps(dict(kind="params", sex=a.sex, size=a.size, params=q),
                         ensure_ascii=False))
        return

    info = build(q, a.out)
    info.update(size=a.size, sex=a.sex, params=q)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
