# -*- coding: utf-8 -*-
"""SVG → PNG 预览（Edge 无头；临时 HTML 只在本目录，用完即删）

用法：
  python preview.py 男 M            # 出 该码 的 拼合平铺图 + 裁片图 两张 PNG
  python preview.py 男 M --scale 1  # 指定缩放
"""
import argparse, os, re, subprocess, tempfile, uuid

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def render(svg, png, scale=1.0):
    src = open(svg, encoding="utf-8").read()
    src = re.sub(r"<\?xml.*?\?>", "", src, flags=re.S).strip()
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', src)
    W, H = int(float(vb.group(1)) * scale), int(float(vb.group(2)) * scale)
    src = re.sub(r'\swidth="[\d.]+mm"\sheight="[\d.]+mm"',
                 ' width="%d" height="%d"' % (W, H), src, count=1)
    tmp = os.path.join(tempfile.gettempdir(),
                       "_preview_%d_%s.html" % (os.getpid(), uuid.uuid4().hex[:8]))
    open(tmp, "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0;background:#fff}svg{display:block}</style>' + src)
    if os.path.exists(png):
        os.remove(png)
    _prof = os.path.join(tempfile.gettempdir(), "hanfu_edge_profile")   # 独立 profile；放系统临时目录，别把 Cookies 留在仓里
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--user-data-dir=" + _prof,
                    "--default-background-color=FFFFFFFF",
                    "--screenshot=" + os.path.abspath(png),
                    "--window-size=%d,%d" % (W, H),
                    "file:///" + tmp.replace("\\", "/")],
                   check=True, capture_output=True, timeout=180)
    try:
        os.remove(tmp)
    except OSError:
        pass
    print("  %s %-28s %dx%d" % ("✓" if os.path.exists(png) else "✗",
                                os.path.basename(png), W, H))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sex", nargs="?", default="男")
    ap.add_argument("size", nargs="?", default="M")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    d = os.path.join(ROOT, "out", "vendor_%s_%s" % (a.sex, a.size))
    render(os.path.join(d, "拼合平铺图.svg"), os.path.join(d, "预览_拼合平铺图.png"), a.scale)
    cut = os.path.join(d, "对穿交_接袖_%s_%s.svg" % (a.sex, a.size))
    if os.path.exists(cut):
        render(cut, os.path.join(d, "预览_裁片图.png"), a.scale * 0.85)


if __name__ == "__main__":
    main()
