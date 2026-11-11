# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 第 2 步：赋值 VP1 = VP2 = 5cm

    python pattern/step2.py
      → out/step2_赋值.svg / .pieces.json / .json / .png

第 1 步只给出 P1、P2 的参数化定义（a、b 待定），step1_* 产物**保持不变**。
本步只做一件事：把等距约束代入，给 a、b 赋值，得到两点的确定坐标。
前片几何依旧一处不改。
（衣长缩短 5cm 的改动已撤销，回归模板 L=770；本文件按新底同名覆盖重算，不另存副本。）
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet
from step1 import make_png

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

TITLE = "试验竖领浅交襟 · 第 2 步 · 赋值 VP₁ = VP₂ = 5cm"
SUBTITLE = "底＝hanfu-cad 厂商基准男 M（模板原衣长 770）「02 前片 ×2」只读　｜　净版 mm　｜　专注前片"
NOTES = [
    "约束（用户令）：VP₁ = VP₂ = 5cm = 50mm；e_top、u_lap 均为单位向量 ⇒ a = b = 50",
    "P₁ = V + 50·(−1,0) = (−50.00, %.2f)；P₂ = V + 50·u = (%.2f, %.2f)　单位 mm"
    % (geo.L, geo.P2(geo.R_EQUAL)[0], geo.P2(geo.R_EQUAL)[1]),
    "衣长：缩短 5cm 已撤销，回归厂商基准模板原值 L=%.0f；θ=atan(%.0f/%.0f)=%.4f°，∠V=%.4f°"
    % (geo.L, geo.LAP_DX, geo.L, geo.THETA, geo.ANGLE_V),
    "第 1 步的参数化定义与待定状态保留在 step1_*；本步只赋值，未改前片几何",
]


def selftest(pieces):
    r = []
    r_ = geo.points_resolved()

    def ck(name, ok, extra=""):
        r.append((name, bool(ok), extra))

    ck("前片 cmds 与模板逐项相同（几何未改）",
       geo.front_piece()["cmds"] == pieces[0]["cmds"])
    ck("约束 5cm 换算为 50mm", geo.R_EQUAL == 50.0)
    ck("a = b = 50", r_["a"] == r_["b"] == 50.0)
    ck("|VP₁| = 50mm", abs(math.dist(geo.V, r_["P1"]) - 50.0) < 1e-9,
       "%.6f" % math.dist(geo.V, r_["P1"]))
    ck("|VP₂| = 50mm", abs(math.dist(geo.V, r_["P2"]) - 50.0) < 1e-9,
       "%.6f" % math.dist(geo.V, r_["P2"]))
    ck("P₁ 仍在顶边 y=L 上", abs(r_["P1"][1] - geo.L) < 1e-9)
    ck("P₂ 仍在门襟边上",
       abs(geo._cross((r_["P2"][0] - geo.V[0], r_["P2"][1] - geo.V[1]), geo.U_LAP)) < 1e-9)
    ck("P₁ = 第 1 步定义的 P1(50)", r_["P1"] == geo.P1(50.0))
    ck("P₂ = 第 1 步定义的 P2(50)", r_["P2"] == geo.P2(50.0))
    ck("a、b 都落在各自取值范围内",
       0 <= r_["a"] <= geo.LEN_TOP and 0 <= r_["b"] <= geo.LEN_LAP)
    return r


def make_zoom():
    """V 附近局部放大（纯读图辅助，不含任何新几何）：
    把第 2 步的两条 50mm 线段放大画清，主图上它们只占 40 多像素。"""
    k, x0, y0 = 3.2, 60.0, 60.0

    def X(dx):
        return (dx + 140.0) * k + x0

    def Y(dy):
        return (80.0 - dy) * k + y0

    r_ = geo.points_resolved()
    d1 = (r_["P1"][0] - geo.V[0], r_["P1"][1] - geo.V[1])   # (−50, 0)
    d2 = (r_["P2"][0] - geo.V[0], r_["P2"][1] - geo.V[1])   # P₂−V（数值随底变）
    Vx, Vy = X(0.0), Y(0.0)
    P1x, P1y = X(d1[0]), Y(d1[1])
    P2x, P2y = X(d2[0]), Y(d2[1])
    Ex, Ey = X(140.0 * geo.U_LAP[0]), Y(140.0 * geo.U_LAP[1])   # 门襟边画到画面底部

    RED, INK, GRAY = "#c0392b", "#1a1a1a", "#8a8a8a"
    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="860" viewBox="0 0 900 860">',
         '<title>第 2 步 · V 附近局部放大</title>',
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         '<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" '
         'markerHeight="7" orient="auto-start-reverse">'
         '<path d="M1 1L9 5L1 9" fill="none" stroke="%s" stroke-width="1.4"/></marker></defs>' % RED,
         '<text x="60" y="40" font-family="sans-serif" font-size="30" font-weight="600" '
         'fill="%s">第 2 步 · V 附近局部放大（3.2×）</text>' % INK]

    # 两条已有的边（顶边 / 门襟边），只截取靠近 V 的一段
    s.append('<g stroke="%s" stroke-width="3.2" fill="none">' % INK)
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (X(-140.0), Y(0.0), Vx, Vy))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f"/>' % (Vx, Vy, Ex, Ey))
    s.append('</g>')
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="22" fill="%s">'
             '顶边（肩线）</text>' % (X(-138.0), Y(0.0) - 16, GRAY))
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="22" fill="%s">'
             '门襟边</text>' % (Ex + 16, Ey - 30, GRAY))

    # VP1 = 50mm：尺寸线抬到顶边上方，带引出线
    oy = Vy - 34.0
    s.append('<g stroke="%s" stroke-width="1.6" fill="none">' % RED)
    s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
             % (Vx, Vy, Vx, oy, P1x, P1y, P1x, oy))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-start="url(#ar)" marker-end="url(#ar)"/>'
             % (Vx, oy, P1x, oy))
    s.append('</g>')
    s.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="sans-serif" '
             'font-size="24" font-weight="600" fill="%s">VP₁ = 50mm</text>'
             % ((Vx + P1x) / 2, oy - 12, RED))

    # VP2 = 50mm：尺寸线沿 VP2 向右法向偏移，带引出线
    n = math.hypot(d2[0], d2[1])
    nx, ny = d2[1] / n, -d2[0] / n          # 法向（指向右侧）
    off = 34.0
    V2x, V2y = Vx + nx * off, Vy - ny * off
    Q2x, Q2y = P2x + nx * off, P2y - ny * off
    s.append('<g stroke="%s" stroke-width="1.6" fill="none">' % RED)
    s.append('  <path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"/>'
             % (Vx, Vy, V2x, V2y, P2x, P2y, Q2x, Q2y))
    s.append('  <path d="M %.1f %.1f L %.1f %.1f" marker-start="url(#ar)" marker-end="url(#ar)"/>'
             % (V2x, V2y, Q2x, Q2y))
    s.append('</g>')
    s.append('<text x="%.1f" y="%.1f" font-family="sans-serif" font-size="24" '
             'font-weight="600" fill="%s">VP₂ = 50mm</text>' % (Q2x + 18, (V2y + Q2y) / 2, RED))

    # 三个点
    s.append('<g stroke="%s" stroke-width="2.4" fill="#ffffff">' % RED)
    for px, py in ((Vx, Vy), (P1x, P1y), (P2x, P2y)):
        s.append('  <circle cx="%.1f" cy="%.1f" r="9"/>' % (px, py))
    s.append('</g>')
    s.append('<g font-family="sans-serif" font-size="26" font-weight="600" fill="%s">' % RED)
    s.append('  <text x="%.1f" y="%.1f">V</text>' % (Vx + 16, Vy - 16))
    s.append('  <text x="%.1f" y="%.1f">P₁</text>' % (P1x - 46, P1y + 38))
    s.append('  <text x="%.1f" y="%.1f">P₂</text>' % (P2x + 16, P2y + 34))
    s.append('</g>')

    s.append('<text x="60" y="790" font-family="sans-serif" font-size="20" fill="%s">'
             'θ = atan(%.0f/%.0f) = %.4f°　｜　∠V = %.4f°　｜　单位 mm</text>'
             % (GRAY, geo.LAP_DX, geo.L, geo.THETA, geo.ANGLE_V))
    s.append('<text x="60" y="822" font-family="sans-serif" font-size="20" fill="%s">'
             '仅放大重画已有线段，无新几何</text>' % GRAY)
    s.append('</svg>')

    svg = os.path.join(OUT, "step2_局部放大.svg")
    open(svg, "w", encoding="utf-8").write("\n".join(s))
    png = os.path.join(OUT, "step2_局部放大.png")
    return svg, png, make_png(svg, png)


def main():
    pieces = geo.sheet_pieces_step2()
    print("=== 第 2 步自检 ===")
    fails = []
    for name, ok, extra in selftest(pieces):
        print("  %s %s %s" % ("PASS" if ok else "FAIL", name, extra))
        if not ok:
            fails.append(name)
    if fails:
        print("!! 自检未过：", fails)
        return 1

    r_ = geo.points_resolved()
    data = {
        "step": 2,
        "action": "赋值",
        "constraint": r_["constraint"],
        "implies": {
            "a": r_["a"], "b": r_["b"],
            "why": "E_TOP 与 U_LAP 均为单位向量，故 |VP1|=a、|VP2|=b；等距 ⇒ a=b=50mm",
        },
        "points": {
            "P1": {"xy": list(r_["P1"]), "on": "顶边（肩线）", "param": "a", "value": r_["a"]},
            "P2": {"xy": list(r_["P2"]), "on": "门襟边", "param": "b", "value": r_["b"]},
        },
        "checks": {
            "VP1_mm": round(math.dist(geo.V, r_["P1"]), 6),
            "VP2_mm": round(math.dist(geo.V, r_["P2"]), 6),
            "geometry_changed": False,
        },
        "note": "第 1 步 step1_* 的参数化定义与待定状态保持不变；本步只代入取值。",
    }
    json.dump(data, open(os.path.join(OUT, "step2_赋值.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    params = dict(L=geo.L, LAP_DX=geo.LAP_DX, X_SHLD=geo.X_SHLD,
                  LEN_TOP=geo.LEN_TOP, LEN_LAP=round(geo.LEN_LAP, 4),
                  THETA_DEG=round(geo.THETA, 6),
                  VP1=geo.R_EQUAL, VP2=geo.R_EQUAL, a=geo.R_EQUAL, b=geo.R_EQUAL)
    svg = os.path.join(OUT, "step2_赋值.svg")
    info = sheet.write_sheet(params, geo.sheet_pieces_step2(), svg, TITLE, SUBTITLE, NOTES)
    print("\n=== 产物 ===")
    print("  ", info["svg"])
    print("  ", info["side"])
    png = os.path.join(OUT, "step2_赋值.png")
    print("   PNG:", make_png(svg, png))
    zsvg, zpng, zres = make_zoom()
    print("   局部放大:", zsvg, "|", zpng, "|", zres)
    print("   ", os.path.join(OUT, "step2_赋值.json"))
    print("\nV=%s" % (geo.V,))
    print("P₁ = %s  |VP₁| = %.2f mm" % (r_["P1"], math.dist(geo.V, r_["P1"])))
    print("P₂ = %s  |VP₂| = %.2f mm" % (r_["P2"], math.dist(geo.V, r_["P2"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
