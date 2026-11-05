# -*- coding: utf-8 -*-
"""
一键换码出图：号型 → SVG + DXF

用法：
  python make.py --sex 女 --size M                 # 单码
  python make.py --sex 男 --size 175/92A --ease 宽松
  python make.py --sex 女 --all                    # 整档 6 个码
  python make.py --sex 女 --height 163 --bust 86   # 直接给净尺寸
产物：out/<码>/ 下 SVG + DXF，以及 out/尺码表.md
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sizing

PY = sys.executable
# DXF 需要 ezdxf，装在专用 venv 里；用 HANFU_PY 指定，否则按本机惯例路径猜，最后退回当前解释器
_VENV = os.environ.get("HANFU_PY") or os.path.join(
    os.path.expanduser("~"), ".workbuddy", "binaries", "python", "envs", "hanfu",
    "Scripts", "python.exe")
PY_DXF = _VENV if os.path.exists(_VENV) else PY
BUILD = os.path.join(HERE, "build.py")
DXF = os.path.join(HERE, "export_dxf.py")


def one(sex, size, ease, outdir, height=None, bust=None, profile="vendor"):
    p = sizing.params(sex=sex, size=size, height=height, bust=bust, ease=ease, profile=profile)
    tag = size if size else "%dx%d" % (height, bust)
    d = os.path.join(outdir, "%s_%s_%s" % (profile, sex, tag.replace("/", "-")))
    os.makedirs(d, exist_ok=True)
    svg = os.path.join(d, "对穿交_接袖_%s_%s.svg" % (sex, tag.replace("/", "-")))
    env = dict(os.environ)
    env["HANFU_PARAMS"] = json.dumps(p, ensure_ascii=False)
    env["HANFU_OUT"] = svg
    r = subprocess.run([PY, BUILD], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, "SVG 生成失败：%s" % (r.stderr[-400:] if r.stderr else r.stdout[-400:])
    side = svg.rsplit(".", 1)[0] + ".pieces.json"
    dxf = svg.rsplit(".", 1)[0] + ".dxf"
    r2 = subprocess.run([PY_DXF, DXF, side, dxf], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r2.returncode != 0:
        return None, "DXF 生成失败：%s" % (r2.stderr[-400:] if r2.stderr else r2.stdout[-400:])
    return {"code": tag, "sex": sex, "params": p, "svg": svg, "dxf": dxf}, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sex", default="男", choices=["女", "男"], help="厂商基准表为男装，默认男")
    ap.add_argument("--size", default=None)
    ap.add_argument("--height", type=float, default=None)
    ap.add_argument("--bust", type=float, default=None)
    ap.add_argument("--ease", default="合体", choices=list(sizing.EASE))
    ap.add_argument("--all", action="store_true", help="整档生成")
    ap.add_argument("--profile", default=None, choices=list(sizing.PROFILES),
                    help="不填则按性别自动：女=artifact(原版) / 男=vendor(厂商表)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "out"))
    a = ap.parse_args()
    if a.profile is None:
        a.profile = "artifact" if a.sex == "女" else "vendor"

    if a.all:
        jobs = [(c, None, None) for c, _, _ in sizing.SEX[a.sex]["sizes"]]
    else:
        if a.size:
            jobs = [(a.size, None, None)]
        elif a.height and a.bust:
            jobs = [(None, a.height, a.bust)]
        else:
            ap.error("需要 --size，或 --height/--bust，或 --all")

    rows, errs = [], []
    for size, h, b in jobs:
        rec, err = one(a.sex, size, a.ease, a.out, h, b, a.profile)
        if err:
            errs.append((size or "%s/%s" % (h, b), err))
        else:
            rows.append(rec)
            print("  ✓ %-6s %s" % (rec["code"], sizing.summary(rec["params"])))

    if rows:
        md = ["# 尺码表 · 对穿交接袖版（%s装 · 放量档 %s · 基准 %s）\n" % (a.sex, a.ease, a.profile),
              "> 由 `pattern/make.py` 自动生成。尺寸单位 mm，净版。\n",
              "| 码 | 衣长 | 平铺摆宽 | 单边摆宽 | 交叠 | 腋深 | 衣身袖 | 接袖 | 袖根 | 腕口 | 领宽 | 通袖 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            p = r["params"]
            half = p["W_HEM"] / 2
            js = p.get("JS", 0.0)
            md.append("| %s | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f |" % (
                r["code"], p["L"], p["W_HEM"], half + p["OV"] / 2, p["OV"],
                p["L"] - p["Y_ARM"], p["SLEEVE_LEN"], js, sizing.sleeve_root(p),
                p.get("WRIST", p["CUFF"]), p["NECK"],
                2 * (p["X_SHLD"] + p["SLEEVE_LEN"] + js)))
        md.append("\n> 档差依据 GB/T 1335（身高 5cm / 胸围 4cm）；放量档系数见 `pattern/sizing.py`，"
                  "数值来源与置信度见 `verification/尺码资料核验.md`。")
        fn = os.path.join(a.out, "尺码表_%s_%s装.md" % (a.profile, a.sex))
        open(fn, "w", encoding="utf-8").write("\n".join(md))
        print("已写 %s" % fn)

    for code, e in errs:
        print("  ✗ %s  %s" % (code, e))
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
