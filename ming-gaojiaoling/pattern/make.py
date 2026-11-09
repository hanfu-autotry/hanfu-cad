# -*- coding: utf-8 -*-
"""
明制高交领（横卧领）· 一键出图

  python make.py --size 本案 --out ../out
  python make.py --sex 女 --size 本案 --out out/本案

产物（写进 --out 目录）：
  明制高交领_<size>.svg          裁片图（1:1，mm）
  明制高交领_<size>.pieces.json  几何侧车（studio 读它做排料/DXF）
  明制高交领_<size>.dxf          裁片 DXF
  拼合平铺图.svg                 前视交襟 + 后视平铺（studio 会跳过这个名字）
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import assembly
import geo
import sheet
import flat
import geo as _g

TP = _g.TPL["params"]

SIZES = {"本案": geo.CASE}

# 可被 --params 覆盖的键＝CASE 里的数值项（TIE_L 这类元组不在此列）
NUM_KEYS = {k: v for k, v in geo.CASE.items() if isinstance(v, (int, float))}


def dxf_python():
    """找一个装了 ezdxf 的解释器：环境变量 → 自己 → 随包 runtime → envs/default"""
    cands = [os.environ.get("HANFU_PY"), sys.executable,
             os.path.join(os.path.dirname(HERE), "..", "hanfu-studio", "dist", "runtime", "python.exe"),
             os.path.join(os.path.expanduser("~"), ".workbuddy", "binaries", "python",
                          "envs", "default", "Scripts", "python.exe")]
    for c in cands:
        if not c or not os.path.exists(c):
            continue
        try:
            r = subprocess.run([c, "-c", "import ezdxf"], capture_output=True, timeout=60)
            if r.returncode == 0:
                return c
        except Exception:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sex", default="女")
    ap.add_argument("--size", default="本案")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "out"))
    ap.add_argument("--no-dxf", action="store_true")
    ap.add_argument("--asm", action="store_true", help="连拼合平铺图一起出（裁片核对通过后再用）")
    ap.add_argument("--params", default=None,
                    help='旋钮覆盖（JSON），如 \'{"L":860,"JS":300}\'；在 CASE 上覆写')
    ap.add_argument("--dump-params", action="store_true",
                    help="只打印当前 CASE（JSON，供界面滑杆取基准），不出图")
    a = ap.parse_args()

    case = dict(SIZES.get(a.size, geo.CASE))
    case["name"] = a.size
    ov = json.loads(a.params) if a.params else {}
    bad = sorted(set(ov) - set(NUM_KEYS))
    if bad:
        raise SystemExit("未知参数 %s；这个版型可用：%s"
                         % ("、".join(bad), "、".join(sorted(NUM_KEYS))))
    case.update({k: float(v) for k, v in ov.items()})
    d = geo.derive(case)
    if a.dump_params:
        print(json.dumps(dict(kind="params", sex=a.sex, size=a.size,
                              params={k: case[k] for k in NUM_KEYS}), ensure_ascii=False))
        return 0
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, "明制高交领_%s" % a.size)

    sheet_data = geo.pieces(d)
    info = sheet.write_sheet(
        d, sheet_data, stem + ".svg",
        "明制高交领 · 裁片图 · %s" % a.size,
        "底片＝jiexiu 模板后片　｜　净版　mm　｜　%s装"
        % a.sex,
        ["前片（中缝右边）×1：左缘＝中缝；领口宽 %.0f ／ 深 %.0f；肩/袖/侧缝/摆沿用模板" % (_g.FRONT_NECK_W, _g.FRONT_NECK_D),
         "后片（半·模板原样）×2：jiexiu 原样复制",
         "续衽（中缝左边）×1：外缘 摆角→P2→P'2→l'→P'1，右缘＝中缝",
         "领缘条（高交领·全衣一条）×1：长方形，长由领口 L 弧＋后领段反推；宽＝AA′＝PB＝97.1（B 重合）",
         "接袖、三角拼接、系带、下摆绢衬条已删除；本版共 6 片"])

    asm = assembly.write(d, os.path.join(a.out, "拼合平铺图.svg")) if a.asm else None
    flatfig, collar_svg, collar_len = flat.write(d, os.path.join(a.out, "平铺线稿.svg"))

    dxf = None
    py = None if a.no_dxf else dxf_python()
    if py:
        dxf = stem + ".dxf"
        r = subprocess.run([py, os.path.join(HERE, "export_dxf.py"), info["side"], dxf],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("  ! DXF 失败：%s" % (r.stderr or r.stdout)[-300:])
            dxf = None

    print(json.dumps(dict(size=a.size, sex=a.sex, svg=info["svg"], pieces_json=info["side"],
                          dxf=dxf, assembly=asm, canvas=info["size"],
                          pieces=info["pieces"]), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
