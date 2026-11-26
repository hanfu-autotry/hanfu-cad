# -*- coding: utf-8 -*-
"""分步图（文档用）渲染器：只负责「把已有 cmds 画成一张说明图」

口径：
  · 不产生几何——所有 `cmds` 都来自 `geo.pieces()` / `flat.collar_band()`，本文件只做排版与着色；
  · 坐标复用 `sheet.path_d()`（服装 y 向上 → 页面 y 向下），与裁片图同一套；
  · 输出 SVG + PNG（Edge 无头截图，同 `hanfu-jiexiu/pattern/preview.py` 的做法）。

用法（由 `step_doc.py` 调）：
  from docfig import Fig
  f = Fig("第 1 步 · 骨架", "直领对襟底子：后片半 + 前片 + 竖直前中缝")
  f.path(cmds, "#1a1a1a", 2.6)
  f.text(600, 860, "肩点 570", 30)
  f.write("out/doc/step1_骨架")
"""
import math
import os
import re
import subprocess
import tempfile
import uuid

import sheet

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

INK = "#1a1a1a"
RED = "#c0392b"
BLUE = "#1f5fa8"
GRAY = "#9aa0a6"
LIGHT = "#c9c9c9"
GREEN = "#1e7a4a"

PAD = 110.0          # 图形四周留白（mm）
HEAD = 170.0         # 顶部标题区
FOOT = 90.0          # 底部注记区


class Fig:
    def __init__(self, title, subtitle=""):
        self.title, self.sub = title, subtitle
        self.paths = []      # (cmds, color, width, dash, fill)
        self.texts = []      # (x, y, s, size, color, anchor)
        self.dots = []       # (x, y, label, color, dx, dy)
        self._pts = []

    # ---- 图元（全部用服装坐标，y 向上）----
    def path(self, cmds, color=INK, width=2.4, dash="", fill="none", fop=1.0):
        self.paths.append((cmds, color, width, dash, fill, fop))
        self._pts += sheet.sample(cmds, 12)
        return self

    def line(self, a, b, color=INK, width=1.8, dash=""):
        self.path([["M", list(a)], ["L", list(b)]], color, width, dash)
        self._pts += [tuple(a), tuple(b)]
        return self

    def text(self, x, y, s, size=30, color=INK, anchor="start"):
        self.texts.append((x, y, s, size, color, anchor))
        return self

    def dot(self, x, y, label="", color=RED, dx=14, dy=-16, size=28):
        self.dots.append((x, y, label, color, dx, dy, size))
        self._pts.append((x, y))
        return self

    def dim_h(self, x1, x2, y, label, color=BLUE, size=26, dy=-14):
        """水平尺寸线（两端短竖线当箭头）"""
        self.line((x1, y), (x2, y), color, 1.2)
        for x in (x1, x2):
            self.line((x, y - 22), (x, y + 22), color, 1.2)
        self.text((x1 + x2) / 2.0, y + dy, label, size, color, "middle")
        return self

    def dim_v(self, x, y1, y2, label, color=BLUE, size=26, dx=-16, anchor="end"):
        self.line((x, y1), (x, y2), color, 1.2)
        for y in (y1, y2):
            self.line((x - 22, y), (x + 22, y), color, 1.2)
        self.text(x + dx, (y1 + y2) / 2.0, label, size, color, anchor)
        return self

    # ---- 出图 ----
    def write(self, stem, scale=0.8):
        xs = [p[0] for p in self._pts]
        ys = [p[1] for p in self._pts]
        for (x, y, s, size, *_rest) in self.texts:
            xs += [x - len(s) * size * 0.55, x + len(s) * size * 0.55]
            ys += [y - size, y + size]
        x0, x1 = min(xs) - PAD, max(xs) + PAD
        y0, y1 = min(ys) - PAD, max(ys) + PAD
        W, H = x1 - x0, y1 - y0 + HEAD + FOOT
        ox, oy = -x0, y1 + HEAD               # 服装 (x0,y1) → 页面 (0, HEAD)

        s = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %.0f %.0f">'
             % (round(W), round(H), W, H),
             '<rect x="0" y="0" width="%.0f" height="%.0f" fill="#ffffff"/>' % (W, H)]
        s.append('<text x="60" y="90" font-family="sans-serif" font-size="46" font-weight="600" fill="%s">%s</text>'
                 % (INK, _esc(self.title)))
        if self.sub:
            s.append('<text x="60" y="146" font-family="sans-serif" font-size="28" fill="#555">%s</text>'
                     % _esc(self.sub))
        for cmds, color, width, dash, fill, fop in self.paths:
            s.append('<path d="%s" stroke="%s" stroke-width="%.1f" fill="%s" fill-opacity="%.2f"%s '
                     'stroke-linejoin="round"/>'
                     % (sheet.path_d(cmds, ox, oy), color, width, fill, fop,
                        (' stroke-dasharray="%s"' % dash) if dash else ""))
        for x, y, lab, color, dx, dy, size in self.dots:
            s.append('<circle cx="%.1f" cy="%.1f" r="7" fill="%s"/>' % (x + ox, oy - y, color))
            if lab:
                s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" fill="%s">%s</text>'
                         % (x + ox + dx, oy - y + dy, size, color, _esc(lab)))
        for x, y, txt, size, color, anchor in self.texts:
            s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" fill="%s" '
                     'text-anchor="%s">%s</text>'
                     % (x + ox, oy - y, size, color, anchor, _esc(txt)))
        s.append('</svg>')
        os.makedirs(os.path.dirname(stem), exist_ok=True)
        svg = stem + ".svg"
        open(svg, "w", encoding="utf-8").write("\n".join(s))
        png = stem + ".png"
        _render(svg, png, scale)
        return svg, png


def _esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _render(svg, png, scale):
    src = open(svg, encoding="utf-8").read()
    src = re.sub(r"<\?xml.*?\?>", "", src, flags=re.S).strip()
    vb = re.search(r'viewBox="([-\d. ]+)"', src)
    vx, vy, vw, vh = [float(q) for q in vb.group(1).split()]
    W, H = int(vw * scale), int(vh * scale)
    src = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', 'width="%d" height="%d"' % (W, H), src, count=1)
    tmp = os.path.join(tempfile.gettempdir(),
                       "_docfig_%d_%s.html" % (os.getpid(), uuid.uuid4().hex[:8]))
    open(tmp, "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0;background:#fff}svg{display:block}</style>' + src)
    if os.path.exists(png):
        os.remove(png)
    prof = os.path.join(tempfile.gettempdir(), "hanfu_edge_profile")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--user-data-dir=" + prof, "--default-background-color=FFFFFFFF",
                    "--screenshot=" + os.path.abspath(png),
                    "--window-size=%d,%d" % (W, H),
                    "file:///" + tmp.replace("\\", "/")],
                   check=True, capture_output=True, timeout=180)
    try:
        os.remove(tmp)
    except OSError:
        pass
    print("  %s %-34s %dx%d" % ("OK" if os.path.exists(png) else "!!", os.path.basename(png), W, H))
