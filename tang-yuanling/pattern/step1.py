# -*- coding: utf-8 -*-
"""唐圆领 · 第 1 步出图：只画中缝、前片顶边、领口点 P 与对称点 P'

    python pattern/step1.py            → out/step1_领口点.svg
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
L, HALF = d["L"], d["HALF"]

W, H = 1000.0, 1000.0
OX, OY = 500.0, 900.0            # 画布上 x=0 / y=0 的位置


def X(x):
    return OX + x


def Y(y):
    return OY - y


def cross(x, y, r=9.0, color=RED, w=2.0):
    return ('<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f" '
            'stroke="%s" stroke-width="%.1f" fill="none"/>'
            % (x - r, y - r, x + r, y + r, x - r, y + r, x + r, y - r, color, w))


out = os.path.join(ROOT, "out", "step1_领口点.svg")
os.makedirs(os.path.dirname(out), exist_ok=True)

s = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
     '<rect width="100%%" height="100%%" fill="#ffffff"/>']

# 中缝（x = 0）与前片顶边（y = L）
s.append('<g stroke="%s" stroke-width="2" fill="none">' % BLACK)
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(0), Y(0), X(0), Y(L)))
s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-HALF), Y(L), X(HALF), Y(L)))
s.append('</g>')

# P（中缝右边）与 P'（镜像）
s.append(cross(X(P[0]), Y(P[1])))
s.append(cross(X(Pp[0]), Y(Pp[1])))
# 对称弦
s.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="1.2" '
         'stroke-dasharray="10 6" fill="none"/>' % (X(Pp[0]), Y(Pp[1]), X(P[0]), Y(P[1]), BLUE))

s.append('<g font-family="sans-serif" fill="%s" font-size="26">' % BLACK)
s.append('  <text x="%.1f" y="%.1f">前中缝 x = 0</text>' % (X(0) + 12, Y(L) + 40))
s.append('  <text x="%.1f" y="%.1f" fill="%s">P (%.1f, %.1f)</text>'
         % (X(P[0]) + 14, Y(P[1]) - 12, RED, P[0], P[1]))
s.append('  <text x="%.1f" y="%.1f" fill="%s" text-anchor="end">P′ (%.1f, %.1f)</text>'
         % (X(Pp[0]) - 14, Y(Pp[1]) - 12, RED, Pp[0], Pp[1]))
s.append('  <text x="%.1f" y="%.1f" font-size="22" fill="%s" text-anchor="middle">'
         'P′ 关于前中缝与 P 对称：|P′x| = |Px| = NECKW/2 + 30mm = %.1f</text>'
         % (X(0), Y(L) - 60, GRAY, P[0]))
s.append('</g>')

# 100mm 校验标尺
s.append('<g stroke="%s" stroke-width="2" fill="none">' % BLACK)
for k in range(6):
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (120 + k * 100, 960, 120 + k * 100, 946))
s.append('  <path d="M 120 960 L 620 960"/>')
s.append('</g>')
s.append('<text x="120" y="990" font-family="sans-serif" font-size="22" fill="%s">'
         '100mm 校验标尺</text>' % BLACK)

s.append('</svg>')
open(out, "w", encoding="utf-8").write("\n".join(s))
print(out)
print("P  = (%.1f, %.1f)" % P)
print("P′ = (%.1f, %.1f)" % Pp)
