# -*- coding: utf-8 -*-
"""打包成 exe（必须在**带 tkinter 的**解释器上跑）。

本机可用的那个：~/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe

    "<上面那个python>" build_exe.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "hanfu-studio",
        "--add-data", os.path.join(HERE, "patterns.json") + os.pathsep + ".",
        "--add-data", os.path.join(HERE, "config.json") + os.pathsep + ".",
        "--hidden-import", "gates",
        "--add-data", os.path.join(HERE, "layout_dxf.py") + os.pathsep + ".",
        "--add-data", os.path.join(HERE, "dxf_io.py") + os.pathsep + ".",
        os.path.join(HERE, "studio.py"),
    ]
    print(" ".join(args))
    # 先语法检查：PyInstaller 遇到语法错只会留一个旧 exe，很容易误判成"打包成功"
    import py_compile
    for src in ("studio.py", "svgview.py", "adapters.py", "layout_dxf.py", "dxf_io.py"):
        py_compile.compile(os.path.join(HERE, src), doraise=True)
    print("语法检查通过")
    r = subprocess.run(args, cwd=HERE)
    exe = os.path.join(HERE, "dist", "hanfu-studio.exe")
    if r.returncode != 0:
        print("!! 打包失败（PyInstaller 返回 %d）——现有 exe 可能是旧的，别当成新包" % r.returncode)
        return r.returncode
    if not os.path.exists(exe):
        print("!! 打包结束但没有产物：", exe)
        return 2
    print("产物：%s（%.1f MB）" % (exe, os.path.getsize(exe) / 1048576.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ── 随包运行时：dist/runtime/（换台电脑不装 Python 也能出图）──────────
def stage_runtime():
    tool = os.path.join(HERE, "tools", "stage_runtime.py")
    if not os.path.exists(tool):
        print("!! 缺 tools/stage_runtime.py，跳过随包运行时")
        return False
    print("-- 准备随包运行时 --")
    r = subprocess.run([sys.executable, tool], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print((r.stdout or "") + (r.stderr or ""))
    return r.returncode == 0


if __name__ == "__main__":
    ok = main()
    if ok:
        stage_runtime()
