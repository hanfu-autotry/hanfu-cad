# -*- coding: utf-8 -*-
"""唐圆领 · 第 6 步：镜像内襟、补后片，出平铺预览 ＋ 领子完整数据

    python pattern/step5.py
      → out/平铺预览.svg / out/平铺预览.png
      → out/领子完整数据.json

两个目的（用户 2026-11-09）：① 看整衣效果；② 出领子完整数据。
顺序：**先出平铺补后片，才能定后领段、导出完整领子**。

领子路线（用户 2026-11-09 定，三段连续、**开放不闭合**）：
  ① 外襟 P'→P（前领下半圆，πr）
  ② 外襟 P→后片→内襟 P'（后领段，2r）
  ③ 内襟 P'→P（前领下半圆，πr）
L = ∫ds = 2πr + 2r；两端为 AB（外襟 P'）与 A'B'（内襟 P），
展开是一根开放长条，**不是闭合环带**。

第 7 步小修正：续衽左缘斜率可调（--tilt 度数，不给则平行衣身左缘），
两端恒为 P' 与「左缘∩下摆」；下摆是一条简单曲线，续衽面积由
沿边界分段积分 A = ½∮(x dy − y dx) 求得 → out/续衽数据.json。

分层：后片（灰虚线，后层）→ 续衽（淡蓝填充）→ 内襟（蓝灰，外襟镜像）
      → 外襟（黑）→ 领子（橙）。
后片与前片共用坐标系（穿起来侧缝/接袖缝重合），照 ming 平铺线稿的口径叠画。

    python pattern/step5.py                 # 默认斜率（平行衣身左缘）
    python pattern/step5.py --tilt 20       # 续衽左缘与竖直夹角 20°
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo

BLACK = "#1a1a1a"
RED = "#c0392b"
BLUE = "#1f5fa8"
GRAY = "#8a8a8a"
BACK = "#c9c9c9"
INNER_C = "#7f96ab"
ORANGE = "#d97706"
FILL = "#fde9c8"
XUREN_FILL = "#eaf2f8"

ap = argparse.ArgumentParser(description="唐圆领平铺预览")
ap.add_argument("--tilt", type=float, default=None,
                help="续衽左缘与竖直方向夹角（度）；不给＝平行衣身左缘")
_args = ap.parse_args()

d = geo.derive(geo.CASE)
if _args.tilt is not None:
    d["XUREN_TILT_DEG"] = _args.tilt
TILT_DEG = math.degrees(math.atan2(geo.xuren_dir(d)[0], geo.xuren_dir(d)[1]))
P, Pp = geo.neck_points(d)
C, r = geo.neck_circle(d)
ARC = geo.neck_arc(d)
EDGE_A, EDGE_B = geo.body_left_edge(d)
Q0, Q1, V = geo.xuren_left_edge(d)
CA, CB, CAp, CBp, U0, U1 = geo.collar_points(d)
SPINE, EA, EB, LNUM, LEXACT = geo.collar_integral(d)
IG = geo.inner_geometry(d)
BACK_R, BACK_L = geo.back_halves()
CW = math.dist(CA, CB)
# 平铺补出后片后，整圈领口才完整 → 完整领子是绕整圈的一条连续带子
DATA = geo.full_collar_data(d)
FULL_LEN = DATA["flat"]["length"]
FRONT_LEN = DATA["front"]["flat"]["length"]
SEG = {s["no"]: s for s in DATA["segments"]}
S1_LEN, BACK_LEN, S3_LEN = SEG[1]["exact"], SEG[2]["exact"], SEG[3]["exact"]
XUREN = geo.xuren_data(d)
XUREN_AREA = XUREN["integral"]["area"]
L, HALF = d["L"], d["HALF"]

W, H = 1000.0, 1000.0
OX, OY = 500.0, 900.0


def X(x):
    return OX + x


def Y(y):
    return OY - y


def txt(x, y, s, size=20, color=BLACK, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="sans-serif" '
            f'font-size="{size}" fill="{color}" text-anchor="{anchor}">{s}</text>')


def polyline(pts, color, w, dash=None):
    p = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{p}" fill="none" stroke="{color}" '
            f'stroke-width="{w:.1f}" stroke-linejoin="round"{da}/>')


def line(a, b, color, w, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="M {X(a[0]):.1f} {Y(a[1]):.1f} L {X(b[0]):.1f} {Y(b[1]):.1f}" '
            f'stroke="{color}" stroke-width="{w:.1f}" fill="none"{da}/>')


def cmds_path(cmds):
    """模板后片 cmds（M/L/C/Z）→ SVG path d。"""
    parts = []
    for c in cmds:
        if c[0] in ("M", "L"):
            parts.append(f'{c[0]} {X(c[1][0]):.1f} {Y(c[1][1]):.1f}')
        elif c[0] == "C":
            parts.append("C " + " ".join(f"{X(q[0]):.1f} {Y(q[1]):.1f}" for q in c[1:4]))
        elif c[0] == "Z":
            parts.append("Z")
    return " ".join(parts)


def dot(pt, color, rad=4.5):
    return f'<circle cx="{X(pt[0]):.1f}" cy="{Y(pt[1]):.1f}" r="{rad}" fill="{color}"/>'


out = os.path.join(ROOT, "out", "平铺预览.svg")
os.makedirs(os.path.dirname(out), exist_ok=True)

s = ['<?xml version="1.0" encoding="UTF-8"?>',
     f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(W)}" height="{int(H)}" '
     f'viewBox="0 0 {int(W)} {int(H)}">',
     '<rect width="100%" height="100%" fill="#ffffff"/>']

# ── 层 1 · 后片（模板后片半 ×2，画在后层）────────────────────────
for half in (BACK_R, BACK_L):
    s.append(f'<path d="{cmds_path(half)}" stroke="{BACK}" stroke-width="1.8" '
             f'stroke-dasharray="14 10" fill="none"/>')

# ── 层 1.5 · 续衽片（分段积分定义的闭合区域，淡蓝填充）─────────
xr_pts = " ".join(f"{X(q[0]):.1f},{Y(q[1]):.1f}" for q in XUREN["outline"])
s.append(f'<polygon points="{xr_pts}" fill="{XUREN_FILL}" '
         f'fill-opacity="0.62" stroke="none"/>')
s.append(dot(Q1, BLUE, 4.5))
s.append(txt(X(Q1[0]) + 12, Y(Q1[1]) - 20, "Q 左缘∩下摆", 16, BLUE))

# ── 层 2 · 内襟（外襟关于前中缝的镜像）──────────────────────────
ig = IG
ic = INNER_C
s.append(line(ig["body_edge"][0], ig["body_edge"][1], ic, 1.6, "12 8"))
s.append(line(ig["seam"][0], ig["seam"][1], ic, 2.6))
for a, b in ig["ends"]:
    s.append(line(a, b, ic, 2.0))
for edge in ig["band"]:
    s.append(polyline(edge, ic, 1.2))

# ── 层 3 · 外襟（前几步已定的几何）──────────────────────────────
s.append(line((0, 0), (0, L), BLACK, 2.0))                 # 前中缝
s.append(line((-HALF, L), (HALF, L), BLACK, 2.0))           # 顶边 / 肩线
s.append(f'<circle cx="{X(C[0]):.1f}" cy="{Y(C[1]):.1f}" r="{r:.1f}" fill="none" '
         f'stroke="{GRAY}" stroke-width="1.4" stroke-dasharray="10 7"/>')
s.append(line(Pp, P, BLUE, 1.2, "10 6"))                   # 直径
s.append(line(EDGE_A, EDGE_B, GRAY, 1.8, "12 8"))          # 衣身左缘（参照）
s.append(line(Q0, Q1, BLACK, 3.0))                         # 续衽左缘

# ── 层 4 · 领子（定积分扫掠带子，压在最上）─────────────────────
poly = [(X(x), Y(y)) for x, y in EA] + [(X(x), Y(y)) for x, y in reversed(EB)]
s.append('<polygon points="%s" fill="%s" fill-opacity="0.82" stroke="none"/>'
         % (" ".join(f"{px:.1f},{py:.1f}" for px, py in poly), FILL))
s.append(polyline(EA, ORANGE, 1.8))
s.append(polyline(EB, ORANGE, 1.8))
# 后领段（后片顶边上 P→P'）：与前领带子接成一条连续带子
s.append(line(P, Pp, ORANGE, 3.0, "12 7"))
s.append(polyline(ARC, BLACK, 3.2))                        # 领口下半圆
for a, b in ((CA, CB), (CAp, CBp)):
    s.append(line(a, b, ORANGE, 3.6))
for pt in (P, Pp):
    s.append(f'<path d="M {X(pt[0])-8:.1f} {Y(pt[1])-8:.1f} L {X(pt[0])+8:.1f} {Y(pt[1])+8:.1f} '
             f'M {X(pt[0])-8:.1f} {Y(pt[1])+8:.1f} L {X(pt[0])+8:.1f} {Y(pt[1])-8:.1f}" '
             f'stroke="{RED}" stroke-width="2" fill="none"/>')
for pt in (CA, CB, CAp, CBp):
    s.append(dot(pt, ORANGE, 4.5))
s.append(f'<path d="M {X(C[0])-6:.1f} {Y(C[1])-6:.1f} L {X(C[0])+6:.1f} {Y(C[1])+6:.1f} '
         f'M {X(C[0])-6:.1f} {Y(C[1])+6:.1f} L {X(C[0])+6:.1f} {Y(C[1])-6:.1f}" '
         f'stroke="{GRAY}" stroke-width="1.6" fill="none"/>')

# ── 标注 ───────────────────────────────────────────────────────
s.append(txt(30, 38, "唐圆领 · 平铺预览", 22, BLACK))
s.append(txt(300, 30, f"领长 {FULL_LEN:.2f} ＝ {S1_LEN:.2f}＋{BACK_LEN:.0f}＋{S3_LEN:.2f}"
                      f"　开放长条 {FULL_LEN:.2f}×{CW:.0f}", 17, GRAY))

# 点名（只标字母，坐标在数据文件里）
for pt, lab, dx, dy, col in (
        (P, "P", 12, -12, RED), (Pp, "P′", -12, -12, RED),
        (CA, "A", -14, 18, ORANGE), (CB, "B", 12, -8, ORANGE),
        (CAp, "A′", 14, 18, ORANGE), (CBp, "B′", -12, -8, ORANGE)):
    anchor = "end" if dx < 0 else "start"
    s.append(txt(X(pt[0]) + dx, Y(pt[1]) + dy, lab, 20, col, anchor))

# 三条主线的名称
s.append(txt(30, 300, "外襟 · 续衽左缘", 18, BLACK))
s.append(f'<path d="M 175 295 L 360 305" stroke="{BLACK}" stroke-width="1.2" fill="none"/>')
s.append(txt(960, 380, "内襟 · 续衽缘（镜像）", 18, ic, "end"))
s.append(f'<path d="M 755 375 L 660 352" stroke="{ic}" stroke-width="1.2" fill="none"/>')
s.append(txt(640, 250, "领子＝连续带子（不闭合）", 20, ORANGE))
s.append(txt(640, 280, "①③ 几何重合，分属外襟／内襟两片", 16, GRAY))
s.append(txt(650, 205, f"② 后领段 = 2r = {BACK_LEN:.0f}（后片）", 18, ORANGE))
s.append(f'<path d="M 645 198 L 575 108" stroke="{ORANGE}" stroke-width="1.2" fill="none"/>')

# 图例与关键数据
s.append(txt(30, 916, "黑＝外襟　蓝灰＝内襟（镜像）　灰虚线＝后片（后层）　"
                      "橙＝领子　淡蓝＝续衽", 16, BLACK))
s.append(txt(30, 937, f"路线 ①外襟 P′→P ②后片 ③内襟 P′→P（不闭合）　"
                      f"∫ds = {FULL_LEN:.2f}　续衽面积 {XUREN_AREA:.2f}（四段积分）　"
                      f"倾角 {TILT_DEG:.2f}°", 16, GRAY))

# 100mm 校验标尺
s.append(f'<g stroke="{BLACK}" stroke-width="2" fill="none">')
for k in range(6):
    s.append(f'  <path d="M {120+k*100} 960 L {120+k*100} 946"/>')
s.append('  <path d="M 120 960 L 620 960"/>')
s.append('</g>')
s.append(txt(120, 990, "100mm 校验标尺", 20, BLACK))

s.append('</svg>')
open(out, "w", encoding="utf-8").write("\n".join(s))

# ── 领子完整数据 ───────────────────────────────────────────────
jpath = os.path.join(ROOT, "out", "领子完整数据.json")
with open(jpath, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
xpath = os.path.join(ROOT, "out", "续衽数据.json")
with open(xpath, "w", encoding="utf-8") as f:
    json.dump(XUREN, f, ensure_ascii=False, indent=2)

print(out)
print(jpath)
print(xpath)
print("续衽左缘倾角 %.2f°（%s），端点 P' %s → 左缘∩下摆 (%.2f, %.2f)"
      % (TILT_DEG, XUREN["tilt_source"], tuple(round(q, 2) for q in Q0),
         Q1[0], Q1[1]))
print("续衽面积 = %.2f mm²（沿边界四段积分 ½∮(x dy − y dx)），周长 = %.2f"
      % (XUREN_AREA, XUREN["integral"]["perimeter"]))
for seg in XUREN["segments"]:
    print("  %s：面积贡献 %.2f，弧长 %.2f" %
          (seg["name"], seg["area_contrib"], seg["length"]))
print("内襟（镜像）续衽缘：P (%g, %g) → (%.2f, %g)"
      % (P[0], P[1], ig["seam"][1][0], ig["seam"][1][1]))
print("后片：模板后片半 %d 段 ×2（右半 + 镜像左半）" % len(BACK_R))
print("领子路线（连续、**不闭合**）：")
for s in DATA["segments"]:
    print("  %d %s：%.6f" % (s["no"], s["name"], s["exact"]))
print("  ∫ds = %.6f，解析 2πr+2r = %.6f，差 %.6f；开放长条 %.2f × %.0f，"
      "两端 %s → %s"
      % (DATA["integral"]["numeric"], DATA["integral"]["exact"],
         DATA["integral"]["error"], DATA["flat"]["length"], DATA["flat"]["width"],
         DATA["flat"]["start"], DATA["flat"]["end"]))
print("  数据：积分明细 %d 段，中线/两边各 %d 点，轮廓 %d 点；"
      "另含 front 前领段独立数据"
      % (len(DATA["detail"]), len(DATA["points"]["spine"]), len(DATA["outline"])))
