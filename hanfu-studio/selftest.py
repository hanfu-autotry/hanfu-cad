# -*- coding: utf-8 -*-
"""软件自检：把界面会走的每条路都走一遍（与界面同一套 adapters 函数），
   过程与失败全部写进**软件日志**；跑完直接读 logs/studio-*.log 就能看到问题在哪。

用法：
    python selftest.py            # 全量（4 个版型 × 全部号型 × 全部产物）
    python selftest.py banbi      # 只跑某版型
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adapters as A


def main(only=None):
    t0 = time.time()
    A.log("selftest.start", only=only or "all", py=sys.executable, log=A.log_path())
    reg = A.registry()
    fails = 0
    for p in reg["patterns"]:
        pid = p["id"]
        if only and pid != only:
            continue
        for sex, sizes in p["sizes"].items():
            for size in sizes:
                try:
                    svg, meta = A.build_svg(pid, size, sex)
                    if not svg or "<svg" not in svg:
                        raise RuntimeError("SVG 内容异常")
                    A.log("selftest.svg", pid=pid, size=size, sex=sex,
                          bytes=len(svg), ms=meta.get("ms"))
                except Exception as e:
                    fails += 1
                    A.log_exc("selftest.fail", e, pid=pid, size=size, sex=sex, stage="build")
        first_sizes = list(p["sizes"].values())[0]
        for ex in p.get("extras", []):
            for size in first_sizes:
                try:
                    r = A.run_extra(pid, ex["id"], size, {})
                    if not r["files"]:
                        raise RuntimeError("脚本没有产出图片")
                    A.log("selftest.extra", pid=pid, extra=ex["id"], size=size,
                          files=len(r["files"]))
                except Exception as e:
                    fails += 1
                    A.log_exc("selftest.fail", e, pid=pid, extra=ex["id"], size=size, stage="extra")
        for size in first_sizes:
            try:
                r = A.export(pid, size)
                A.log("selftest.export", pid=pid, size=size, files=len(r["files"]), dxf=r["dxf"])
            except Exception as e:
                fails += 1
                A.log_exc("selftest.fail", e, pid=pid, size=size, stage="export")
    A.log("selftest.end", fails=fails, sec=round(time.time() - t0, 1))
    print("FAILS: %d ｜ 日志：%s" % (fails, A.log_path()))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else None) else 0)
