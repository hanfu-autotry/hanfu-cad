# -*- coding: utf-8 -*-
"""无界面批量生成（不依赖 tkinter，供脚本/CI/素材包清单用）。

用法：
    python batch_cli.py banbi              # 每模式取中码
    python batch_cli.py banbi --all        # 每模式全码
    python batch_cli.py all                # 四个版型依次跑
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adapters as A


def run(pid, all_sizes=False):
    r = A.generate_batch(pid, all_sizes=all_sizes)
    print("%-8s %2d 组 ｜ 成功 %d ｜ 失败 %d ｜ %s"
          % (pid, r["total"], r["ok"], r["total"] - r["ok"], r["dir"]))
    for x in r["rows"]:
        if not x.get("ok"):
            print("   失败 %s：%s" % (x["tag"], x.get("err", "")))
    return r["ok"] == r["total"]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    all_sizes = "--all" in sys.argv
    pids = args[0] if args else "all"
    if pids == "all":
        pids = [p["id"] for p in A.registry()["patterns"]]
    else:
        pids = [pids]
    bad = 0
    for pid in pids:
        if not run(pid, all_sizes):
            bad += 1
    print("全部完成：%d 个版型，%d 个有失败项" % (len(pids), bad))
    sys.exit(1 if bad else 0)
