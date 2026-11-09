# -*- coding: utf-8 -*-
"""唐圆领 · 第 2 步出图：以 PP' 为直径画圆，取下半圆为领口

    python pattern/step2.py            → out/step2_领口圆.svg

延续第 1 步：前中缝 x=0、前片顶边 y=L、P 与 P'。
本步只加：整圆（辅助虚线）、直径 P'P、下半圆弧（领口，实线）。
"""
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


out = os.path.join(ROOT, "out", "step2_领口圆.svg")
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
s.append(txt(30, 38, "第 2 步 · 下半圆为领口", 22, BLACK))
s.append(txt(700, 38, f"整圆 r = {r:.1f}（辅助虚线）", 22, GRAY))
s.append(txt(30, 225, f"P 右移 30mm → P ({P[0]:.1f}, {P[1]:.1f})　P′ ({Pp[0]:.1f}, {Pp[1]:.1f})　"
                      f"圆心 C ({C[0]:.1f}, {C[1]:.1f}) 不动", 22, GRAY))
s.append(txt(30, 255, f"直径 |PP′| = {2*r:.1f}　r = {r:.1f}　领口最低点 y = {C[1]-r:.1f}", 22, GRAY))

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
