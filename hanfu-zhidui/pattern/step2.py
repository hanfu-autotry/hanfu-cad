# -*- coding: utf-8 -*-
"""直领对襟 · 第 2 步：开领宽 + 装领条（完全参照 通裁·原始直领）

    python pattern/step2.py
      → out/step2_开领宽与装领条.svg / .pieces.json
      → out/平铺预览.svg（顺带，见 flat.py：正面线稿）

口径全部来自 `hanfu-shenyi/pattern/build.py`（原始直领交襟衣 V1）的 `_DEF`：
  开领宽 160（SLIT_HALF 80×2）／领条宽 95（COLLAR_W）／压边可见 40（LAPEL_FOLD）／
  后领折转 底 160 → 顶 89（NECK_TOP_HALF 44.5×2）、露出 77（NECK_H）。
领条按 V1 的**产物关系**重算，不再沿用模板那条 1850×40：
  长 ＝ 2 × 前襟剪口边长 ＋ 后领段（＝开领宽）。
本步只改前片与领条：前片沿中缝侧全高切掉 80；后片几何未动。
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

Q = geo.params()
grid = geo.sheet_pieces(geo.step2_pieces(Q), step=2, q=Q)
CL, CW = geo.collar_size(Q)
FL = geo.neck_cut_len(Q)
SHOW_BACK = Q["NECK_W"] - Q["LAPEL_FOLD"] * 2           # 中间露出后片的宽

info = sheet.write_sheet(
    geo.PARAMS, grid, os.path.join(OUT, "step2_开领宽与装领条.svg"),
    "直领对襟 · 第 2 步 · 开领宽 + 装领条",
    "口径 100% 照 通裁·原始直领交襟衣 V1（hanfu-shenyi/pattern/build.py 的 _DEF）"
    "　｜　净版 mm",
    [
        "开领宽 %.0f ＝ 2×%.0f（V1 SLIT_HALF）：前片沿中缝侧全高切掉 %.0f，前襟边 %.1f"
        % (Q["NECK_W"], Q["NECK_W"] / 2.0, Q["NECK_W"] / 2.0, FL),
        "领条长 %.1f ＝ 2×前襟 %.1f ＋ 后领段 %.0f（＝开领宽）；宽 %.0f（V1 COLLAR_W），"
        "两条 notch 就是后领段两端" % (CL, FL, Q["NECK_W"], CW),
        "装领条：压在剪口线上，每边可见 %.0f（V1 LAPEL_FOLD），中间露出后片 %.0f"
        % (Q["LAPEL_FOLD"], SHOW_BACK),
        "后领：领条在领口立起露出 %.0f（带宽 %.0f 立起来），顶边 %.0f 比底 %.0f 短"
        % (Q["NECK_H"], CW, geo.NECK_TOP_HALF * 2, Q["NECK_W"]),
    ])

print(info["svg"])
print(info["side"])
for p in info["pieces"]:
    print("  %s ×%d：%.1f × %.1f mm" % (p["name"], p["qty"], p["w"], p["h"]))
print("开领宽 %.0f ｜ 领条 %.1f×%.0f ｜ 前襟 %.1f ｜ 压边 %.0f ｜ 露出后片 %.0f"
      % (Q["NECK_W"], CL, CW, FL, Q["LAPEL_FOLD"], SHOW_BACK))

# 顺带出一张平铺线稿（flat.py 是脚本式模块，import 即出图）
import flat  # noqa: E402,F401
