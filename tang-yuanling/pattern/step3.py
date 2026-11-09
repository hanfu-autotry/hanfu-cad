# -*- coding: utf-8 -*-
"""唐圆领 · 第 4 步出图：过 P' 作外襟·续衽片左缘（直线，∥ 衣身左缘）

    python pattern/step3.py            → out/step3_续衽左缘.svg

口径：前片（前身）含内襟与外襟，**本图只画外襟**，内襟不画、不镜像。
外襟 = 中缝右边的衣身 ＋ 越过中缝拼在左边的续衽。

延续前几步：前中缝 x=0、顶边 y=L、P/P'、整圆、下半圆领口。
本步只加：衣身左缘（灰虚线，方向参照）、过 P' 且与之平行的续衽左缘（实线）。
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo

BLACK, RED, BLUE, GRAY = "#1a1a1a", "#c0392b", "#1f5fa8", "#8a8a8a"

d = geo.derive(geo.CASE)
P, Pp = geo.neck_points(d)
C, r = geo.neck_circle(d)
ARC = geo.neck_arc(d)
EDGE_A, EDGE_B = geo.body_left_edge(d)          # 衣身左缘（模板侧缝镜像）
Q0, Q1, V = geo.xuren_left_edge(d)              # 外襟续衽左缘：过 P'，∥ 衣身左缘
TILT = math.degrees(math.atan2(V[0], V[1]))
L, HALF = d["L"], d["HALF"]

W, H = 1000.0, 1000.0
OX, OY = 500.0, 900.0            # 画布上 x=0 / y=0 的位置（与第 1 步一致，1:1）


def X(x):
    return OX + x


def Y(y):
    return OY - y


def cross(x, y, size=9.0, color=RED, w=2.0):
    return (f'<path d="M {x-size:.1f} {y-size:.1f} L {x+size:.1f} {y+size:.1f} '
            f'M {x-size:.1f} {y+size:.1f} L {x+size:.1f} {y-size:.1f}" '
            f'stroke="{color}" stroke-width="{w:.1f}" fill="none"/>')


def circle(cx, cy, rad, color=GRAY, w=1.6, dash="10 7"):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="{w:.1f}" stroke-dasharray="{dash}"/>')


def polyline(pts, color, w, dash=None):
    p = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{p}" fill="none" stroke="{color}" '
            f'stroke-width="{w:.1f}" stroke-linejoin="round"{da}/>')


def txt(x, y, s, size=26, color=BLACK, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="sans-serif" '
            f'font-size="{size}" fill="{color}" text-anchor="{anchor}">{s}</text>')


out = os.path.join(ROOT, "out", "step3_续衽左缘.svg")
os.makedirs(os.path.dirname(out), exist_ok=True)

s = ['<?xml version="1.0" encoding="UTF-8"?>',
     f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(W)}" height="{int(H)}" '
     f'viewBox="0 0 {int(W)} {int(H)}">',
     '<rect width="100%" height="100%" fill="#ffffff"/>']

# ── 主图（1:1，与第 1 步同一坐标系）──────────────────────────────
# 中缝与前片顶边
s.append(f'<g stroke="{BLACK}" stroke-width="2" fill="none">')
s.append(f'  <path d="M {X(0):.1f} {Y(0):.1f} L {X(0):.1f} {Y(L):.1f}"/>')
s.append(f'  <path d="M {X(-HALF):.1f} {Y(L):.1f} L {X(HALF):.1f} {Y(L):.1f}"/>')
s.append('</g>')

# 整圆（辅助）＋ 直径 P'P
s.append(circle(X(C[0]), Y(C[1]), r))
s.append(f'<path d="M {X(Pp[0]):.1f} {Y(Pp[1]):.1f} L {X(P[0]):.1f} {Y(P[1]):.1f}" '
         f'stroke="{BLUE}" stroke-width="1.2" stroke-dasharray="10 6" fill="none"/>')

# 衣身左缘（辅助虚线，只作方向参照）＋ 外襟续衽左缘（过 P' 的平行直线）
s.append(f'<path d="M {X(EDGE_A[0]):.1f} {Y(EDGE_A[1]):.1f} '
         f'L {X(EDGE_B[0]):.1f} {Y(EDGE_B[1]):.1f}" '
         f'stroke="{GRAY}" stroke-width="2" stroke-dasharray="12 8" fill="none"/>')
s.append(f'<path d="M {X(Q0[0]):.1f} {Y(Q0[1]):.1f} L {X(Q1[0]):.1f} {Y(Q1[1]):.1f}" '
         f'stroke="{BLACK}" stroke-width="3.2" fill="none"/>')

# 领口 = 下半圆
s.append(polyline([(X(x), Y(y)) for x, y in ARC], BLACK, 3.4))

# P、P'、圆心 C
s.append(cross(X(P[0]), Y(P[1])))
s.append(cross(X(Pp[0]), Y(Pp[1])))
s.append(cross(X(C[0]), Y(C[1]), size=6.0, color=GRAY, w=1.6))

s.append(txt(X(P[0]) + 14, Y(P[1]) - 14, f"P ({P[0]:.1f}, {P[1]:.1f})", 26, RED))
s.append(txt(X(Pp[0]) - 14, Y(Pp[1]) - 14, f"P′ ({Pp[0]:.1f}, {Pp[1]:.1f})", 26, RED, "end"))
s.append(txt(X(0) + 90, Y(L) + 70, "下半圆 ＝ 领口", 26, BLACK))
s.append(f'<path d="M {X(0)+84:.1f} {Y(L)+64:.1f} L {X(0)+8:.1f} {Y(L)+r-4:.1f}" '
         f'stroke="{BLACK}" stroke-width="1.4" fill="none"/>')
s.append(txt(30, 38, "第 4 步 · 外襟续衽左缘", 22, BLACK))
s.append(txt(700, 38, f"整圆 r = {r:.1f}（辅助虚线）", 22, GRAY))

# 两条平行线的标注
s.append(txt(30, 500, "衣身左缘", 20, GRAY))
s.append(txt(30, 524, "模板侧缝镜像", 17, GRAY))
s.append(f'<path d="M 115 495 L 182 500" stroke="{GRAY}" stroke-width="1.2" fill="none"/>')
s.append(txt(30, 305, "外襟·续衽片左缘", 22, BLACK))
s.append(txt(30, 330, "过 P′，∥ 衣身左缘", 18, GRAY))
s.append(f'<path d="M 235 298 L 368 312" stroke="{BLACK}" stroke-width="1.2" fill="none"/>')

# 数据说明放在放大框下方的空白区，避免压到两条斜线
for yy, line in zip((758, 783, 808, 833, 858, 883), (
        "本图 = 外襟（内襟不画）",
        f"P ({P[0]:.0f}, {P[1]:.0f})　P′ ({Pp[0]:.0f}, {Pp[1]:.0f})",
        f"C ({C[0]:.0f}, {C[1]:.0f})　r = {r:.0f}　领口最低 y = {C[1]-r:.0f}",
        f"衣身左缘 v = ({V[0]:.2f}, {V[1]:.2f})",
        f"续衽左缘 ∥ 衣身左缘，偏竖直 {TILT:.2f}°",
        f"续衽左缘下端 ({Q1[0]:.1f}, {Q1[1]:.0f})",
)):
    s.append(txt(638, yy, line, 17, GRAY))

# ── 局部放大（倍率随 r 自适应），把领口圆画清楚 ────────────────
BX, BY = 810.0, 520.0               # 放大框内：CAD 圆心 C 的屏幕位置
K = 150.0 / r                        # 倍率自适应，让放大框里的圆半径恒为 150px


def X2(x):
    return BX + K * x


def Y2(y):
    return BY - K * (y - C[1])


s.append(f'<rect x="630" y="345" width="360" height="375" fill="#ffffff" '
         f'stroke="{GRAY}" stroke-width="1.6"/>')
s.append(txt(640, 335, f"领口局部 · {K:.2f}×（粗实线为领口）", 22, BLACK))
# 中缝短段（到圆底稍下即止，避免穿过框底标注）、顶边短段
s.append(f'<g stroke="{BLACK}" stroke-width="2" fill="none">')
s.append(f'  <path d="M {X2(0):.1f} 350 L {X2(0):.1f} 680"/>')
s.append(f'  <path d="M 635 {Y2(L):.1f} L 985 {Y2(L):.1f}"/>')
s.append('</g>')
s.append(circle(X2(C[0]), Y2(C[1]), K * r, w=2.0, dash="14 10"))
s.append(f'<path d="M {X2(Pp[0]):.1f} {Y2(Pp[1]):.1f} L {X2(P[0]):.1f} {Y2(P[1]):.1f}" '
         f'stroke="{BLUE}" stroke-width="1.6" stroke-dasharray="12 8" fill="none"/>')
s.append(polyline([(X2(x), Y2(y)) for x, y in ARC], BLACK, 4.0))
s.append(cross(X2(P[0]), Y2(P[1]), size=11.0, color=RED, w=2.4))
s.append(cross(X2(Pp[0]), Y2(Pp[1]), size=11.0, color=RED, w=2.4))
s.append(cross(X2(C[0]), Y2(C[1]), size=7.0, color=GRAY, w=1.8))
s.append(txt(X2(P[0]) - 12, Y2(P[1]) - 14, "P", 24, RED, "end"))
s.append(txt(X2(Pp[0]) + 12, Y2(Pp[1]) - 14, "P′", 24, RED))
s.append(txt(X2(C[0]) + 14, Y2(C[1]) - 12, "C", 22, GRAY))
s.append(txt(645, 705, f"直径 PP′ = {2*r:.1f}　/　r = {r:.1f}", 22, BLUE))

# 100mm 校验标尺
s.append(f'<g stroke="{BLACK}" stroke-width="2" fill="none">')
for k in range(6):
    s.append(f'  <path d="M {120+k*100} 960 L {120+k*100} 946"/>')
s.append('  <path d="M 120 960 L 620 960"/>')
s.append('</g>')
s.append(txt(120, 990, "100mm 校验标尺", 22, BLACK))

s.append('</svg>')
open(out, "w", encoding="utf-8").write("\n".join(s))
print(out)
print(f"P  = ({P[0]:.1f}, {P[1]:.1f})")
print(f"P′ = ({Pp[0]:.1f}, {Pp[1]:.1f})")
print(f"C  = ({C[0]:.1f}, {C[1]:.1f})   r = {r:.1f}   |PP′| = {2*r:.1f}")
print(f"领口弧：{len(ARC)} 点，最低点 ({ARC[len(ARC)//2][0]:.1f}, {ARC[len(ARC)//2][1]:.1f})")
print(f"衣身左缘 A = ({EDGE_A[0]:.1f}, {EDGE_A[1]:.1f}) → B = ({EDGE_B[0]:.1f}, {EDGE_B[1]:.1f})")
print(f"方向 v = ({V[0]:.2f}, {V[1]:.2f})，偏竖直 {TILT:.2f}°")
print(f"外襟续衽左缘：P′ ({Q0[0]:.1f}, {Q0[1]:.1f}) → ({Q1[0]:.1f}, {Q1[1]:.1f})，与衣身左缘平行")
