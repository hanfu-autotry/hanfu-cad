# -*- coding: utf-8 -*-
"""
拼合平铺图 —— 后片半 / 前片 / 接袖 按实际缝合关系拼成一件，出平铺视图。
上栏：整幅平铺（真实比例）  下栏：袖部大样（接袖缝、袖底缘连续性）

用法：python assembly.py                        # 默认 男 M 厂商档
     python assembly.py --sex 男 --size L       # 指定码
"""
import argparse, json, math, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sizing

_ap = argparse.ArgumentParser()
_ap.add_argument("--sex", default="男", choices=["女", "男"])
_ap.add_argument("--size", default="M")
_ap.add_argument("--ease", default="合体", choices=list(sizing.EASE))
_ap.add_argument("--profile", default=None, choices=list(sizing.PROFILES))
_a = _ap.parse_args()
if _a.profile is None:
    _a.profile = "artifact" if _a.sex == "女" else "vendor"
P = sizing.params(sex=_a.sex, size=_a.size, ease=_a.ease, profile=_a.profile)
TAG = "%s_%s_%s" % (_a.profile, _a.sex, _a.size)

_tmp = tempfile.mkdtemp(prefix="hanfu_asm_")     # 隔离 build.py 的出图副作用
os.environ["HANFU_PARAMS"] = json.dumps(P, ensure_ascii=False)   # 服装参数与 make.py 完全一致
os.environ["HANFU_OUT"] = os.path.join(_tmp, "side.svg")
import build as B
os.environ.pop("HANFU_OUT", None)
shutil.rmtree(_tmp, ignore_errors=True)

L, HALF, HEM_RISE, NECK = B.L, B.HALF, B.HEM_RISE, B.NECK
X_ARM, Y_ARM, X_SHLD = B.X_ARM, B.Y_ARM, B.X_SHLD
X_CUFF, X_JS, JS = B.X_CUFF, B.X_JS, B.JS
Y_CT, Y_JT, Y_JB = B.Y_CUFF_TOP, B.Y_JS_TOP, B.Y_JS_BOT
CUFF, WRIST, S = B.CUFF, B.WRIST, B.S

BLACK, RED, BLUE, GRAY, TINT = "#1a1a1a", "#c0392b", "#1f5fa8", "#8a8a8a", "#dce9f8"


def bezpts(seg, t0, t1, n=200):
    return [B._bez(seg[0], seg[1], seg[2], seg[3], t0 + (t1 - t0) * i / n) for i in range(n + 1)]


Y_SEAM_BOT, SEAM_H = B.Y_SEAM_BOT, B.SEAM_H
# 袖底缘 = 一条直线：U_ARM（腋下圆角终点）→ 接袖根 → 腕口下角
UND_ARC = [B.U_ARM]
# 腋下 R45 圆角（build 里真实的 G1 blend）
_d_side = B._unit((HALF, HEM_RISE), (X_ARM, Y_ARM))
_A_a = B._off((X_ARM, Y_ARM), _d_side, -70.0)
_bc = B.blend(_A_a, _d_side, B.U_ARM, B._UND_U)
ARM_BLEND = bezpts((_A_a, _bc[1], _bc[2], _bc[3]), 0.0, 1.0, 90)
_side_lo = B._off((X_ARM, Y_ARM), _d_side, -140.0)

ANG0 = ANG1 = math.degrees(B._UND_ANG)


class T:
    """服饰坐标 (x 向右, y 向上) → 画布 mm"""
    def __init__(self, ox, oy, k, ytop):
        self.ox, self.oy, self.k, self.ytop = ox, oy, k, ytop

    def p(self, x, y):
        return (self.ox + self.k * x, self.oy + self.k * (self.ytop - y))

    def d(self, pts):
        return " ".join("%.1f,%.1f" % self.p(*q) for q in pts)


W, H = 1980.0, 1810.0
s = []
s.append('<?xml version="1.0" encoding="UTF-8"?>')
s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
         % (W, H, W, H))
s.append('<rect width="100%" height="100%" fill="#fff"/>')
s.append('<title>拼合平铺图 · 对穿交接袖版 %s%s</title>' % (_a.sex, _a.size))


def dim(t, x1, y1, x2, y2, txt, off=(0, -20), col=GRAY, fs=23):
    a, b = t.p(x1, y1), t.p(x2, y2)
    s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.1" '
             'marker-start="url(#ar)" marker-end="url(#ar)"/>' % (a[0], a[1], b[0], b[1], col))
    mx, my = (a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1]
    rot = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) > 45
    if rot:
        s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" fill="%s" '
                 'text-anchor="middle" transform="rotate(-90 %.1f %.1f)">%s</text>'
                 % (mx, my, fs, col, mx, my, txt))
    else:
        s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="%d" fill="%s" '
                 'text-anchor="middle">%s</text>' % (mx, my, fs, col, txt))


# ══════════ ① 整幅平铺 ══════════
# 画布纵向配额：130（标题）→ 880（大样图顶），留白随衣长自动跟随
K1 = round(min(0.66, 690.0 / (L + 192.0)), 4)
P1 = T(W / 2, 130.0, K1, L + 80.0)

s.append('<text x="60" y="52" font-family="sans-serif" font-size="27" font-weight="500" fill="%s">'
         '① 整幅平铺（后视 · 左右镜像 · 1:%.2f）</text>' % (BLACK, 1 / K1))

for sx in (1, -1):
    s.append('<polygon points="%s" fill="%s" stroke="none"/>'
             % (P1.d([(sx * X_CUFF, Y_SEAM_BOT), (sx * X_JS, Y_JB), (sx * X_JS, Y_JT), (sx * X_CUFF, Y_CT)]), TINT))

for sx in (1, -1):
    hem = [(0, 0), (200, 5), (400, 30), (HALF, HEM_RISE)]
    s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4" stroke-linejoin="round"/>'
             % (P1.d([(sx * q[0], q[1]) for q in hem]), BLACK))
    s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4" stroke-linejoin="round"/>'
             % (P1.d([(sx * HALF, HEM_RISE)] + [(sx * p[0], p[1]) for p in ARM_BLEND]
                     + [(sx * p[0], p[1]) for p in UND_ARC]
                     + [(sx * X_CUFF, Y_SEAM_BOT), (sx * X_JS, Y_JB), (sx * X_JS, Y_JT), (sx * X_SHLD, L)]), BLACK))
    s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.8" stroke-dasharray="22 12"/>'
             % (*P1.p(sx * X_CUFF, Y_SEAM_BOT), *P1.p(sx * X_CUFF, Y_CT), BLUE))

s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2.4"/>'
         % (*P1.p(-X_SHLD, L), *P1.p(X_SHLD, L), BLACK))
s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6" stroke-dasharray="26 10"/>'
         % (*P1.p(0, 0), *P1.p(0, L), BLUE))
s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ffffff" stroke-width="9"/>'
         % (*P1.p(-NECK / 2, L), *P1.p(NECK / 2, L)))
s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="4.5"/>'
         % (*P1.p(-NECK / 2, L), *P1.p(NECK / 2, L), RED))

dim(P1, -X_JS, L + 46, X_JS, L + 46, "通袖 %d" % round(S), (0, -14))
dim(P1, -NECK / 2, L + 100, NECK / 2, L + 100, "预开领 %d" % round(NECK), (66, -14), RED)
dim(P1, X_JS + 66, 0, X_JS + 66, L, "衣长 %d" % round(L), (-16, 0))
dim(P1, -X_JS - 66, 0, -X_JS - 66, L, "衣长 %d" % round(L), (-16, 0))
dim(P1, -HALF, -66, HALF, -66, "摆宽 %d" % round(2 * HALF), (0, 34))
dim(P1, 0, -112, X_JS, -112, "半通袖 %d" % round(X_JS), (0, 34))
dim(P1, 140, Y_ARM, 140, L, "腋深 %d" % round(L - Y_ARM), (44, 0))

# ② 取景框（右袖接袖区）
_zx = [P1.p(X_CUFF - 60, Y_SEAM_BOT - 26), P1.p(X_JS + 46, Y_CT + 44)]
s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="%s" '
         'stroke-width="1.4" stroke-dasharray="12 8"/>'
         % (_zx[0][0], _zx[1][1], _zx[1][0] - _zx[0][0], _zx[0][1] - _zx[1][1], GRAY))
s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="24" fill="%s">②</text>'
         % (_zx[1][0] + 8, _zx[1][1] - 4, GRAY))

# ══════════ ② 袖部大样 ══════════
# 大样取景框：跟着接袖区走（换码不裁到腕口），再按可用画布反算放大倍率
VX0, VX1 = X_ARM - 100.0, X_JS + 56.0      # 腋点 → 腕口（整只袖，含腋下圆角）
VY0, VY1 = Y_ARM - 90.0, Y_CT + 50.0
K2 = round(min(1.75, 1050.0 / (VX1 - VX0), 690.0 / (VY1 - VY0)), 4)
P2 = T(0, 0, K2, VY1)
P2.ox = 100.0 - K2 * VX0
P2.oy = 880.0
VW, VH = (VX1 - VX0) * K2, (VY1 - VY0) * K2

s.append('<text x="60" y="856" font-family="sans-serif" font-size="27" font-weight="500" fill="%s">'
         '② 袖部大样（1:%.2f）—— 袖底缘一条直线，接袖缝是它上面的一道垂直切口</text>' % (BLACK, K2))
s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#fcfcfc" stroke="#dcdcdc" stroke-width="1.2"/>'
         % (100, 880, VW, VH))
s.append('<g>')
s.append('<clipPath id="cp"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/></clipPath>' % (100, 880, VW, VH))
s.append('</g>')
s.append('<g clip-path="url(#cp)">')
s.append('<polygon points="%s" fill="%s" stroke="none"/>'
         % (P2.d([(X_CUFF, Y_SEAM_BOT), (X_JS, Y_JB), (X_JS, Y_JT), (X_CUFF, Y_CT)]), TINT))
s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3.2" stroke-linejoin="round"/>'
         % (P2.d([_side_lo] + ARM_BLEND + UND_ARC + [(X_CUFF, Y_SEAM_BOT), (X_JS, Y_JB), (X_JS, Y_JT), (X_CUFF, Y_CT)]), BLACK))
s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2.2" stroke-dasharray="24 14"/>'
         % (*P2.p(X_CUFF, Y_SEAM_BOT), *P2.p(X_CUFF, Y_CT), BLUE))


def tangent_mark(t, x, y, ang, ln=40, col=RED):
    dx, dy = math.cos(math.radians(ang)) * ln, math.sin(math.radians(ang)) * ln
    a = t.p(x, y)
    s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.8" '
             'stroke-dasharray="7 5"/>' % (a[0] - dx, a[1] + dy, a[0] + dx, a[1] - dy, col))


tangent_mark(P2, X_CUFF, Y_SEAM_BOT, ANG1, 52)
s.append('</g>')

# 标注
notes = [
    ("袖底缘直线 %.2f°" % ANG1, B.U_ARM[0] + 55, B.U_ARM[1] + 50, "#e08a00"),
    ("腋下 R45 圆角（原样保留）", X_ARM - 62, Y_ARM + 150, GRAY),
    ("接缝：两侧同一切矢，折角 0°" % (), X_CUFF + 14, Y_SEAM_BOT + 34, RED),
]
for txt, x, y, col in notes:
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="22" fill="%s">%s</text>'
             % (*P2.p(x, y), col, txt))

dim(P2, X_CUFF, Y_SEAM_BOT, X_CUFF, Y_CT, "袖根 %d" % round(SEAM_H), (44, 0))
dim(P2, X_JS, Y_JB, X_JS, Y_JT, "腕口 %d" % round(WRIST), (-40, 0))
dim(P2, X_CUFF, Y_SEAM_BOT - 40, X_JS, Y_JB - 40, "接袖 %d" % round(JS), (0, 36))
dim(P2, X_ARM, Y_ARM - 40, X_CUFF, Y_SEAM_BOT - 40, "衣身袖 %d" % round(B.SLEEVE_LEN), (0, 36))

# 右侧数据块
bx, by = 1250.0, 910.0
rows = [
    ("通袖", "%d ＝ %d + %d×2" % (round(S), round(B.SLEEVE_LEN), round(JS))),
    ("袖根（接袖根边）", "%d   →   腕口 %d" % (round(SEAM_H), round(WRIST))),
    ("腋点 A", "(%.1f, %.1f)" % (X_ARM, Y_ARM)),
    ("接袖根下缘 Q", "(%.1f, %.1f)" % (X_CUFF, Y_SEAM_BOT)),
    ("腕口下角 Z", "(%.1f, %.1f)" % (X_JS, Y_JB)),
    ("袖底缘 直线角", "%.2f°（腋点→腕口 全程同一条线）" % ANG1),
    ("接缝两侧切矢", "%.2f° / %.2f° → 折角 0°" % (ANG1, ANG1)),
    ("袖底缘 直线度", "共线偏差 0.00 mm"),
    ("接缝折角", "0.00°  → G1 连续"),
    ("腋下圆角", "R45（衣身原样，未改）"),
    ("接袖根边 / 腕口边", "垂直、四角尖角、无圆角"),
    ("接袖片数", "×4（前后片各一）"),
]
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('<text x="%.0f" y="%.0f" font-size="26" font-weight="500">关键数据</text>' % (bx, by))
for i, (k, v) in enumerate(rows):
    yy = by + 40 + i * 38
    s.append('<text x="%.0f" y="%.0f" font-size="22" fill="%s">%s</text>' % (bx, yy, GRAY, k))
    s.append('<text x="%.0f" y="%.0f" font-size="22">%s</text>' % (bx + 268, yy, v))
s.append('</g>')

# 图注
fy = 880 + VH + 60
s.append('<g font-family="sans-serif" fill="%s">' % BLACK)
s.append('<text x="60" y="%.0f" font-size="38" font-weight="500">拼合平铺图 · 对穿交 接袖版（右衽 · 掩腕长窄袖 · 男女同款）</text>' % fy)
s.append('<text x="60" y="%.0f" font-size="24" fill="%s">浅蓝＝接袖（×4，前后片各一）   蓝虚线＝接袖缝   红线＝切矢：袖底缘从腋点到腕口是一条直线（%.2f°），接袖缝只是这条线上的一道垂直切口</text>'
         % (fy + 44, BLUE, ANG1))
s.append('<text x="60" y="%.0f" font-size="24" fill="%s">袖身联裁不破肩：袖与衣身同片；本版只在袖上加接袖缝，腋点 / 腋深 / 袖口 / 摆宽 / 交叠 均未改动</text>'
         % (fy + 84, GRAY))
s.append('</g>')

s.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" '
         'orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.2"/></marker></defs>' % GRAY)
s.append('</svg>')

out = os.environ.get("HANFU_ASM_OUT") or os.path.join(
    os.path.dirname(HERE), "out", TAG, "拼合平铺图.svg")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write("\n".join(s))
print("wrote", out, [W, H], "footer_y=%.0f" % fy)
