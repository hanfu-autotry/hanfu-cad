# -*- coding: utf-8 -*-
"""深衣（V2/V3 通用）· 裁片几何（3 片）→ 并入 pieces.json，供 export_dxf.py 出 DXF。

片（2026-11-18 古制改「裳＝左右折」后统一 3 片，V2=6 幅 / V3=4 幅）：
  ① 上衣（上衣段，水平对折成前后）2000 × 2×衣长，前中剪开＝领口宽（从折线剪到腰线）
  ② 裳（裳段，一条 N 幅带）N×500 × 裳高 —— 沿两侧（±半数幅）左右折、两端在后中相接
  ③ 领条：一条直的，长＝2·|PQ|＋领口宽，宽＝领条宽＝立起高（见 pattern/collar.py）

坐标：cmds 用"件内坐标"（y 向上、腰线在 y=0 / y=1248），ox/oy 负责摆位。
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 用法：python build_pieces_shenyi.py [pieces.json]
#   缺省 V3；跑 V2 时传 深衣_V2.pieces.json（先 HANFU_PARAMS='{"L_BODY":624,"GARMENT_L":1872}'
#   跑 build_shenyi.py 生成对应 pieces.json，再跑本脚本，最后 export_dxf.py）
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "深衣_V3_窄袖.pieces.json")
# 传 深衣_V2.pieces.json 则按 V2 的 4 片出（上/下段各 2 幅）
OUT = SRC if os.path.isabs(SRC) else os.path.join(HERE, SRC)
P = json.load(open(OUT, encoding="utf-8"))
R = P["resolved"]
Q = P["params"]
H = P["canvas"][1]

S_HALF = R["S"] / 2.0            # 1000
SEG = R["SEG_MID"]               # 中段高 = 2×衣长（对折成上衣）
SEG_S = R["SEG_OUT"]             # 裳段高（上段 / 下段）
BODY = R["L_BODY"]               # 衣长 = 袖口宽
SLIT = Q["NECK_W"] / 2.0         # 前中开口半宽（领口宽 / 2）
ARM = Q["ARMPIT"]                # 370
ARM_H = R["ARMPIT_H"]            # 随衣长等比缩
HOOK = Q["HOOK_OUT"]             # 60
COLLAR_L = R["COLLAR_L"]         # 1418.2（V2）/ 1708.3（V3）
COLLAR_W = float(Q.get("COLLAR_W", 30.0))    # 领条宽＝立起高（古制统一算法）
N_SHANG = int(Q.get("N_SHANG", 2))          # 裳幅数（与 build_shenyi 同源）
SH_HALF = Q["FAB_W"] * N_SHANG / 2.0       # 裳半宽（2 幅＝500）


def rect(w, h):
    return [["M", [0, 0]], ["L", [w, 0]], ["L", [w, h]], ["L", [0, h]], ["Z"]]


pieces = [
    # ① 上衣：整幅 2000 × 上衣段高，前中从下边剪进 160 × 衣长（剪到折线）
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
]
pieces.append(
    # ② 裳：一条 N 幅带（左右折：两侧各 ±半数幅 折、两端在后中相接＝后中缝）
    dict(
        name="裳（%d 幅·左右折）" % N_SHANG, qty=1, ox=2300 + S_HALF, oy=H,
        cmds=rect(SH_HALF * 2, SEG_S), grain=[0, 1],
        notches=[[-SH_HALF / 2, SEG_S], [0, SEG_S], [SH_HALF / 2, SEG_S],
                 [-SH_HALF / 2, 0], [0, 0], [SH_HALF / 2, 0]],
        folds=[[-SH_HALF / 2, 0, -SH_HALF / 2, SEG_S],
               [SH_HALF / 2, 0, SH_HALF / 2, SEG_S]],
        note="两侧（±半数幅）折；两端相接＝后中缝；裳前中缝＝衣身前中缝·只不缝合",
    ))
pieces.append(
    # ③ 领条：一条直的
    dict(
        name="领条", qty=1, ox=100, oy=H - 1450,
        cmds=rect(COLLAR_L, COLLAR_W), grain=[1, 0],
        notches=[[0, 0], [COLLAR_L, 0],
                 [COLLAR_L / 2 - SLIT, COLLAR_W], [COLLAR_L / 2 + SLIT, COLLAR_W]],
    ))

# V1 的 p["box"] 是 SVG 画布坐标，会与 cmds 坐标混用 → 这里统一给 cmds 包围盒
for p in pieces:
    xs = [c[1][0] for c in p["cmds"] if c[0] in "ML"]
    ys = [c[1][1] for c in p["cmds"] if c[0] in "ML"]
    p["box"] = [min(xs), min(ys), max(xs), max(ys)]

P["pieces"] = pieces
_nm = ("V2 宽袖" if abs(BODY - 624) < 1 else
       "V3 窄袖" if abs(BODY - 195) < 1 else
       "自定义（衣长 %d）" % round(BODY))
P["title"] = "深衣 %s（衣长＝袖口 %d，总长 %d）" % (_nm, round(BODY), round(BODY + SEG_S))
json.dump(P, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已并入 %d 片 → %s" % (len(pieces), OUT))
for p in pieces:
    print("  %-18s %s  刀口 %d 个" % (p["name"], p["box"], len(p["notches"])))
