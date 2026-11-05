# -*- coding: utf-8 -*-
"""深衣型矩领 V2 · 裁片几何（4 片）→ 并入 pieces.json，供 export_dxf.py 出 DXF。

片：
  ① 上衣（中段，对折成前后）2000 × 1248，前中剪开 160 × 624（剪到折线）
  ② 裳·后（上段）2000 × 1248
  ③ 裳·前（下段）2000 × 1248
  ④ 领条 3904 × 95（一条直的，成型后呈倒 U：左襟 → 绕颈 → 右襟）

坐标：cmds 用"件内坐标"（y 向上、腰线在 y=0 / y=1248），ox/oy 负责摆位。
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "深衣型矩领_V2.pieces.json")
P = json.load(open(os.path.join(OUT), encoding="utf-8"))
R = P["resolved"]
Q = P["params"]
H = P["canvas"][1]

S_HALF = R["S"] / 2.0            # 1000
SEG = 1248.0                     # 段高（对折后＝衣长 624）
SLIT = Q["SLIT_HALF"]            # 80
ARM = Q["ARMPIT"]                # 370
ARM_H = Q["ARMPIT_H"]            # 200
HOOK = Q["HOOK_OUT"]             # 60
COLLAR_L = R["COLLAR_L"]         # 3904
COLLAR_W = 95.0


def rect(w, h):
    return [["M", [0, 0]], ["L", [w, 0]], ["L", [w, h]], ["L", [0, h]], ["Z"]]


pieces = [
    # ① 上衣：整幅 2000 × 1248，前中从下边剪进 160 × 624（剪到折线 y=624）
    dict(
        name="上衣（中段·对折）", qty=1, ox=100 + S_HALF, oy=H,
        cmds=[["M", [-S_HALF, 0]], ["L", [-SLIT, 0]], ["L", [-SLIT, SEG / 2]],
              ["L", [SLIT, SEG / 2]], ["L", [SLIT, 0]], ["L", [S_HALF, 0]],
              ["L", [S_HALF, SEG]], ["L", [-S_HALF, SEG]], ["Z"]],
        grain=[0, 1],
        notches=[[-SLIT, 0], [SLIT, 0],
                 [-ARM, ARM_H], [-ARM, SEG - ARM_H], [ARM, ARM_H], [ARM, SEG - ARM_H],
                 [-ARM - HOOK, 0], [ARM + HOOK, 0],
                 [-ARM - HOOK, SEG], [ARM + HOOK, SEG],
                 [-S_HALF, SEG / 2], [0, SEG / 2], [S_HALF, SEG / 2]],
    ),
    # ② 裳·后（上段）：4 幅整幅
    dict(
        name="裳·后（上段）", qty=1, ox=2300 + S_HALF, oy=H,
        cmds=rect(S_HALF * 2, SEG), grain=[0, 1],
        notches=[[-ARM, SEG], [0, SEG], [ARM, SEG], [-ARM, 0], [0, 0], [ARM, 0]],
    ),
    # ③ 裳·前（下段）：4 幅整幅
    dict(
        name="裳·前（下段）", qty=1, ox=4500 + S_HALF, oy=H,
        cmds=rect(S_HALF * 2, SEG), grain=[0, 1],
        notches=[[-ARM, SEG], [0, SEG], [ARM, SEG], [-ARM, 0], [0, 0], [ARM, 0]],
    ),
    # ④ 领条：一条直的
    dict(
        name="领条", qty=1, ox=100, oy=H - 1450,
        cmds=rect(COLLAR_L, COLLAR_W), grain=[1, 0],
        notches=[[0, 0], [COLLAR_L, 0],
                 [COLLAR_L / 2 - SLIT, COLLAR_W], [COLLAR_L / 2 + SLIT, COLLAR_W]],
    ),
]

# V1 的 p["box"] 是 SVG 画布坐标，会与 cmds 坐标混用 → 这里统一给 cmds 包围盒
for p in pieces:
    xs = [c[1][0] for c in p["cmds"] if c[0] in "ML"]
    ys = [c[1][1] for c in p["cmds"] if c[0] in "ML"]
    p["box"] = [min(xs), min(ys), max(xs), max(ys)]

P["pieces"] = pieces
P["title"] = "深衣型矩领 V2"
json.dump(P, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已并入 %d 片 → %s" % (len(pieces), OUT))
for p in pieces:
    print("  %-18s %s  刀口 %d 个" % (p["name"], p["box"], len(p["notches"])))
