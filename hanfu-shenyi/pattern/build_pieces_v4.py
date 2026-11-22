# -*- coding: utf-8 -*-
"""深衣 V4 / V4B · 裁片组件 → 并入 pieces.json（供 export_dxf.py / 组件库）。

用法（由 hanfu-studio 的 pieces_post 机制调用，吃 HANFU_PARAMS + build_v4.py 产出的 pieces.json）：
    HANFU_PARAMS='{"NECK_MODE":"arc_po",...}' python build_v4.py   # 先出空 pieces.json
    python build_pieces_v4.py 深衣_V4_新领口.pieces.json

从 build_v4.py 产出的 params/resolved 反推裁片组件（V4 / V4B 现在同一套古制上领）：
  · 领片 = 直条 COLLAR_L × COLLAR_W（collar.py::geom 的古制平行领条展开）。
  · 续衽片已删（V4B 不再有续衽）。

坐标：cmds 用件内坐标（y 向上、原点在件左下），ox/oy 负责在预览画布摆位。
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "深衣_V4_新领口.pieces.json")
OUT = SRC if os.path.isabs(SRC) else os.path.join(HERE, SRC)
P = json.load(open(OUT, encoding="utf-8"))
Q = P["params"]
R = P["resolved"]
MODE = Q.get("NECK_MODE", "ec")

NECK_W = float(Q["NECK_W"])
A = NECK_W / 2.0                       # 半领口宽 a = SLIT_HALF
Y_FOLD = float(R["Y_FOLD"])            # 肩线布面 y
H = float(R["CLOTH_H"])
W_COLLAR = float(Q.get("COLLAR_W", 30.0))


def rect(w, h):
    return [["M", [0.0, 0.0]], ["L", [w, 0.0]], ["L", [w, h]],
            ["L", [0.0, h]], ["Z"]]


def finish(piece):
    xs = [c[1][0] for c in piece["cmds"] if c[0] in ("M", "L")]
    ys = [c[1][1] for c in piece["cmds"] if c[0] in ("M", "L")]
    piece["box"] = [min(xs), min(ys), max(xs), max(ys)]
    return piece


pieces = []

# 两种模式都用「古制通用上领算法」（collar.py），V4B 的领条沿上领路线 H→F→P′ 量长：
#   领片 = 直条 LEAD_LEN × COLLAR_W（刀口在 F 处与 P′/P 处，左右各一组）
#   续衽片 = 三角形 O–H–F（左右镜像同形，qty 2）
if MODE == "arc_po":
    lead_len = float(R["LEAD_LEN"])
    w = float(R["COLLAR_W"])
    notch = [float(v) for v in R["LEAD_NOTCH"]]
    pieces.append(finish(dict(
        name="领片（V4B·古制平行领条）", qty=1,
        ox=120.0, oy=H + 120.0,
        cmds=rect(lead_len, w), grain=[1, 0],
        notches=[[0.0, 0.0], [lead_len, 0.0]] +
                [[v, w] for v in notch] + [[lead_len - v, w] for v in notch],
        note="长＝2×(|HF|+|FP′|)+后领宽2a＝%.1f；宽＝领宽%.0f；刀口 F/ P′ 各一组" % (lead_len, w),
    )))
    # 续衽片：三角形 O(0,0)–H(H_X,0)–F(F.x,ARM_Y)
    hx = float(R["H_X"])
    arm_y = float(R["ARM_Y"])
    y_fold = float(R["Y_FOLD"])
    fpt = (arm_y / y_fold * A, arm_y)
    tri = [(0.0, 0.0), (hx, 0.0), fpt]
    xs = [p[0] for p in tri]; ys = [p[1] for p in tri]
    dx0, dy0 = min(xs), min(ys)
    tri = [(p[0] - dx0, p[1] - dy0) for p in tri]
    cmds = [["M", list(tri[0])]] + [["L", list(pt)] for pt in tri[1:]] + [["Z"]]
    pieces.append(finish(dict(
        name="续衽片（V4B·三角形 O-H-F）", qty=2,
        ox=120.0 + lead_len + 160.0, oy=H + 120.0,
        cmds=cmds, grain=[0, 1],
        notches=[list(pt) for pt in tri],
        note="O–H（下摆）%.1f、H–F %.1f、F–O %.1f；左右镜像同形，裁 2 片"
             % (abs(hx), math.dist((hx, 0.0), fpt), math.dist((0.0, 0.0), fpt)),
    )))
else:
    lead_len = float(R["COLLAR_L"])
    pieces.append(finish(dict(
        name="领片（V4·EC 矩领）", qty=1,
        ox=120.0, oy=H + 120.0,
        cmds=rect(lead_len, W_COLLAR), grain=[1, 0],
        notches=[[0.0, 0.0], [lead_len, 0.0],
                 [lead_len / 2.0 - A, W_COLLAR], [lead_len / 2.0 + A, W_COLLAR]],
        note="EC 交叉领条展开：长=%.1f（collar.py 统一算法），宽=领宽%.0f" % (lead_len, W_COLLAR),
    )))

P["pieces"] = pieces
P["title"] = "深衣 V4%s · 裁片组件" % ("B" if MODE == "arc_po" else "")
json.dump(P, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("已并入 %d 片 → %s" % (len(pieces), OUT))
for p in pieces:
    print("  %-26s box=%s  刀口 %d" % (p["name"], [round(v, 1) for v in p["box"]], len(p["notches"])))
