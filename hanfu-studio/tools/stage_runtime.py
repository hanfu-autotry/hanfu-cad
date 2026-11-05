# -*- coding: utf-8 -*-
"""准备"随包 Python 运行时"（dist/runtime/）——换台电脑不装 Python 也能出图。

为什么需要：子程序是源码（每版型一种程序），运行必须有解释器；借本机 WorkBuddy 的 venv
换机就没了。所以把解释器 + 需要的第三方包一起放进发行包。

做法（确定性）：
  1) 取 **embeddable** 包（~11MB，只有标准库）解到 dist/runtime/
  2) 把实测需要的第三方包从本机 venv 拷进 runtime/Lib/site-packages
     （ezdxf 出 DXF、Pillow 出预览、numpy、shapely 排料、pyparsing/typing_extensions 是依赖）
  3) 在 runtime/python3XX._pth 里加 Lib\\site-packages（embeddable 默认不带）

用法：python tools/stage_runtime.py [目标目录，默认 dist/runtime]
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.dirname(HERE)
HOME = os.path.expanduser("~")
VENV_SP = os.path.join(HOME, ".workbuddy", "binaries", "python", "envs", "hanfu",
                       "Lib", "site-packages")

PKGS = ["ezdxf", "PIL", "numpy", "numpy.libs", "shapely", "shapely.libs",
        "pyparsing", "typing_extensions.py", "fontTools"]
NEED = "import ezdxf, numpy, PIL, shapely, pyparsing; print('deps ok')"
URLS = ["https://registry.npmmirror.com/-/binary/python/3.13.12/python-3.13.12-embed-amd64.zip",
        "https://www.python.org/ftp/python/3.13.12/python-3.13.12-embed-amd64.zip"]


def clean_env():
    """验证必须用干净环境：本机 shell 的 PYTHONPATH 会把 site-packages 顶掉。"""
    env = dict(os.environ)
    for k in ("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"):
        env.pop(k, None)
    return env


def run(py, code):
    r = subprocess.run([py, "-c", code], capture_output=True, text=True, timeout=240,
                       env=clean_env(),
                       creationflags=0x08000000 if os.name == "nt" else 0)
    return r.returncode == 0, ((r.stdout or "") + (r.stderr or "")).strip()


def fetch_embed(target):
    import urllib.request
    import zipfile
    zpath = target + ".zip"
    for url in URLS:
        try:
            print("  下载", url)
            with urllib.request.urlopen(url, timeout=120) as r, open(zpath, "wb") as fh:
                shutil.copyfileobj(r, fh)
            if os.path.getsize(zpath) < 5 * 1048576:
                raise IOError("包不完整")
            if os.path.isdir(target):
                shutil.rmtree(target, ignore_errors=True)
            os.makedirs(target, exist_ok=True)
            with zipfile.ZipFile(zpath) as z:
                z.extractall(target)
            os.remove(zpath)
            return True
        except Exception as e:
            print("   失败：%s: %s" % (type(e).__name__, e))
            if os.path.exists(zpath):
                os.remove(zpath)
    return False


def install_pkgs(target):
    sp = os.path.join(target, "Lib", "site-packages")
    os.makedirs(sp, exist_ok=True)
    if not os.path.isdir(VENV_SP):
        # venv 已被清理（本项目就是这么做的）：改用 tools/wheels/ 里的离线轮子
        wheels = os.path.join(HERE, "wheels")
        if os.path.isdir(wheels):
            import zipfile
            n = 0
            for whl in sorted(os.listdir(wheels)):
                if whl.endswith(".whl"):
                    with zipfile.ZipFile(os.path.join(wheels, whl)) as z:
                        z.extractall(sp)
                    n += 1
            print("  从 tools/wheels 装包：%d 个轮子" % n)
            return ["(wheels×%d)" % n]
        print("  !! 找不到包来源：%s 也不存在，且没有 tools/wheels/" % VENV_SP)
        print("    补法：pip download --only-binary :all: --platform win_amd64 "
              "--python-version 3.13 -d tools/wheels ezdxf numpy pillow shapely fonttools pyparsing")
        return []
    got = []
    for name in PKGS:
        src = os.path.join(VENV_SP, name)
        if not os.path.exists(src):
            print("   （缺包，跳过）", name)
            continue
        dst = os.path.join(sp, name)
        if os.path.exists(dst):
            shutil.rmtree(dst, ignore_errors=True) if os.path.isdir(dst) else os.remove(dst)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)
        got.append(name)

    for pth in glob.glob(os.path.join(target, "python*._pth")):
        lines = [x.rstrip("\n") for x in open(pth, encoding="utf-8")]
        if not any("site-packages" in x for x in lines):
            lines.insert(1, "Lib\\site-packages")
            if not any(x.strip().lower() == "import site" for x in lines):
                lines.append("import site")
            open(pth, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            print("  _pth 已加 Lib\\site-packages：", os.path.basename(pth))
    return got


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(STUDIO, "dist", "runtime")
    py = os.path.join(target, "python.exe")

    if os.path.exists(py):
        ok, ver = run(py, "import sys;print(sys.version.split()[0])")
        okd, msg = run(py, NEED)
        if ok and okd:
            print("runtime 已就绪：%s（Python %s，含第三方包）" % (py, ver))
            return 0
        print("现有 runtime 不完整（%s），重建" % (msg.splitlines()[-1] if msg else "?"))

    if not fetch_embed(target):
        print("!! 没能取到 embeddable 包（离线且无缓存）")
        return 1
    got = install_pkgs(target)

    ok, ver = run(py, "import sys;print(sys.version.split()[0])")
    okd, msg = run(py, NEED)
    size = sum(os.path.getsize(os.path.join(d, f))
               for d, _x, fs in os.walk(target) for f in fs) / 1048576.0
    print("runtime：%s（Python %s，%.0f MB）" % (py, ver, size))
    print("第三方包：%s" % ("、".join(got) or "无"))
    print("依赖验证：%s" % msg)
    return 0 if okd else 1


if __name__ == "__main__":
    sys.exit(main())
