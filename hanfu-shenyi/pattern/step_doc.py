# -*- coding: utf-8 -*-
"""一步一画 · 分步图（原始直领交襟衣 V1）

规矩沿用 `../ming-gaojiaoling/pattern/step_doc.py`（母本）：
  · 第 1 步＝原图（V1 现状，一处不改）；之后每步**同一张画布、同一构图改一处**；
  · 红实线＝这一步新定的线，灰虚线＋淡红填充＝这一步删掉的线／块；
  · 几何只从 `build.py` 取（`PIECES` 与常数），本文件不另算一个数。

  python step_doc.py --step 1
  python step_doc.py --step all

产物：out/doc/stepN_<名称>.svg / .png
"""
import argparse
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# build.py 一 import 就会写自己的图；给个临时出口，别动 pattern/ 下的交付物
os.environ.setdefault("HANFU_OUT", os.path.join(tempfile.gettempdir(), "_v1_step_src.svg"))

import build as B                      # noqa: E402
from docfig import Fig, INK, RED, BLUE, GRAY, LIGHT, GREEN   # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "out", "doc")
ORANGE = "#b85400"                     # 对折线（沿 build.py 的配色）

HALF_S = B.HALF_S
CLOTH_H = B.CLOTH_H
HALF_L = B.HALF_L
SLIT = B.SLIT_HALF
COLLAR_L, COLLAR_W = B.COLLAR_L, B.COLLAR_W
BODY = B.PIECES[0]["cmds"]
COLLAR = B.PIECES[1]["cmds"]

# 领条另画在布片下方（只是一张说明图，不是排料）
CY = -300.0
CX = -COLLAR_L / 2.0


def _moved(cmds, dx, dy):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
        else:
            out.append([c[0]] + [[p[0] + dx, p[1] + dy] for p in c[1:]])
    return out


# ── 第 1 步 · 原图 ─────────────────────────────────────────────────
def step1():
    f = Fig("第 1 步 · 原图（V1 现状，一处不改）",
            "四块布（每块一幅 %.0f）拼成 %d × %d · 上下对折出肩线 · 前中剪开两道 · 领条另裁"
            % (B.FAB_W, round(2 * HALF_S), round(CLOTH_H)))

    # 布片
    f.path(BODY, INK, 3.0)
    # 拼幅缝
    for k in range(1, B.N_PANEL):
        x = -HALF_S + B.FAB_W * k
        f.line((x, 0), (x, CLOTH_H), BLUE, 1.6, "26 10")
    # 上下对折线
    f.line((-HALF_S - 30, B.Y_FOLD), (HALF_S + 30, B.Y_FOLD), ORANGE, 2.6, "46 16 10 16")
    # 前中剪开（弦：颈侧点 → 下摆中点）
    for sx in (-1, 1):
        f.line((sx * SLIT, B.Y_FOLD), (0.0, 0.0), RED, 3.4)
    # 领条内缘（压边外沿，∥ 弦、内让一个带宽）
    for sx in (-1, 1):
        f.line((sx * (SLIT + B.N_X * COLLAR_W), B.Y_FOLD + B.N_Y * COLLAR_W),
               (sx * (B.N_X * COLLAR_W), B.N_Y * COLLAR_W), GREEN, 2.0, "18 12")
    # 关键点
    f.dot(-SLIT, B.Y_FOLD, "P（−%d, %d）" % (round(SLIT), round(B.Y_FOLD)), RED, -300, 46)
    f.dot(SLIT, B.Y_FOLD, "P（%d, %d）" % (round(SLIT), round(B.Y_FOLD)), RED, 20, 46)
    f.dot(0.0, 0.0, "Q（0, 0）下摆中点", RED, 26, 34)

    # 尺寸
    f.dim_h(-HALF_S, HALF_S, CLOTH_H + 95,
            "通袖 %d ＝ %d 幅 × %.0f" % (round(2 * HALF_S), B.N_PANEL, B.FAB_W), BLUE, 28, 34)
    f.dim_v(HALF_S + 130, 0, CLOTH_H, "布片高 %d" % round(CLOTH_H), BLUE, 28, 24, "start")
    f.dim_v(HALF_S + 330, 0, HALF_L, "对折后衣长 %d" % round(HALF_L), BLUE, 28, 24, "start")
    f.dim_h(-SLIT, SLIT, B.Y_FOLD + 100, "剪口 %d" % round(2 * SLIT), BLUE, 26, 34)

    # 文字注记
    f.text(-HALF_S + 20, CLOTH_H + 300, "拼幅缝 ×3（┄┄ 蓝）：4 块布拼成一片料，横为通袖", 26, BLUE)
    f.text(-HALF_S + 20, CLOTH_H + 252, "对折线（┈ 橙）：肩线是折出来的，不另裁前后片", 26, ORANGE)
    f.text(-HALF_S + 20, CLOTH_H + 204, "剪开线（— 红）：两道，从对折线剪到下摆中点，不折、靠领条压住毛边", 26, RED)
    f.text(-HALF_S + 20, CLOTH_H + 156, "领条内缘（┈ 绿）：∥ 襟缘弦、内让一个带宽 %d" % round(COLLAR_W), 26, GREEN)

    # 领条裁片
    f.path(_moved(COLLAR, CX, CY), INK, 3.0)
    f.text(CX, CY + COLLAR_W + 120,
           "④ 领条 ×1 ｜ %.1f × %d ｜ 一条直的，成型后呈倒 U：左襟 → 绕颈 → 右襟"
           % (COLLAR_L, round(COLLAR_W)), 30, INK)
    f.dim_h(CX, CX + COLLAR_L, CY - 90, "领条长 %.1f" % COLLAR_L, BLUE, 26, -16)
    f.dim_v(CX + COLLAR_L + 130, CY, CY + COLLAR_W, "宽 %d" % round(COLLAR_W), BLUE, 26, 40, "start")

    f.text(-HALF_S, CY - 230,
           "单位 mm｜净版｜x = 0 前中缝，y = 0 下摆，y 向上｜平面布片，未折、未缝", 26, GRAY)
    return f


STEPS = {1: ("原图", step1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="1", help="1 / all")
    a = ap.parse_args()
    want = sorted(STEPS) if a.step == "all" else [int(a.step)]
    for n in want:
        name, fn = STEPS[n]
        stem = os.path.join(OUT, "step%d_%s" % (n, name))
        svg, png = fn().write(stem)
        print(json_line(n, name, svg, png))


def json_line(n, name, svg, png):
    import json
    return json.dumps({"step": n, "name": name, "svg": svg, "png": png,
                       "量": {"通袖": round(2 * HALF_S), "布片高": round(CLOTH_H),
                              "对折后衣长": round(HALF_L), "剪口": round(2 * SLIT),
                              "领条": [round(COLLAR_L, 1), round(COLLAR_W)]}},
                      ensure_ascii=False)


if __name__ == "__main__":
    main()
