# -*- coding: utf-8 -*-
"""试验竖领浅交襟 · 第 1 步：解析构造 P1、P2

    python pattern/step1.py
      → out/step1_P1P2.svg / .pieces.json / .json / .png

底＝hanfu-cad 厂商基准男 M（模板原衣长 770）对穿交半臂的「02 前片 ×2」，**只读**，几何一处不改。
本步只做一件事：把 P1、P2 用解析式构造出来（位置参数 a、b 待定）。
（衣长缩短 5cm 的改动已撤销，回归模板 L=770；本文件按新底同名覆盖重算，不另存副本。）
"""
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import geo
import sheet

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

TITLE = "试验竖领浅交襟 · 第 1 步 · 解析构造 P₁ / P₂"
SUBTITLE = "底＝hanfu-cad 厂商基准男 M（模板原衣长 770）「02 前片 ×2」只读　｜　净版 mm　｜　专注前片"
NOTES = [
    "P₁ = V + a·(−1,0)，a∈[0,%.0f]；P₂ = V + b·u，u=(%.0f,−%.0f)/%.2f，b∈[0,%.2f]"
    % (geo.LEN_TOP, geo.LAP_DX, geo.L, geo.LEN_LAP, geo.LEN_LAP),
    "a、b 暂不给具体位置（待定）；空心点为示意占位，非定量、不是从截图量出",
    "衣长：缩短 5cm 已撤销，回归厂商基准模板原值 L=%.0f；θ=atan(%.0f/%.0f)=%.4f°，∠V=%.4f°"
    % (geo.L, geo.LAP_DX, geo.L, geo.THETA, geo.ANGLE_V),
    "布纹仍为模板硬编码 9.3°，与门襟边不平行（叉积 %.4f）；模板既有后果，未自行修正"
    % geo.GRAIN_CROSS,
]


def selftest(pieces):
    """实测：几何未改、点落在边上、解析求交可用"""
    r = []

    def ck(name, ok, extra=""):
        r.append((name, bool(ok), extra))

    src = geo.front_piece()["cmds"]
    ck("前片 cmds 与模板逐项相同（几何未改）", src == pieces[0]["cmds"])
    ck("V = (0, L) = 模板首点", list(geo.V) == [0.0, geo.L] == src[0][1])
    ck("H = (LAP_DX, 0) = 门襟边下端", list(geo.H) == src[1][1])
    ck("S = (−X_SHLD, L) 在顶边上", geo.S[1] == geo.L and geo.S[0] == -geo.X_SHLD)
    ck("θ = atan(LAP_DX/L)",
       abs(geo.THETA - math.degrees(math.atan2(geo.LAP_DX, geo.L))) < 1e-9,
       "%.6f°" % geo.THETA)
    ck("|VH| = √(L²+LAP_DX²)",
       abs(geo.LEN_LAP - math.hypot(geo.L, geo.LAP_DX)) < 1e-9,
       "%.4f mm" % geo.LEN_LAP)
    ck("布纹与门襟边的夹角如实记录（模板本身不平行）",
       abs(geo.GRAIN_CROSS - geo._cross(geo.GRAIN, geo.U_LAP)) < 1e-12,
       "叉积 %.6f" % geo.GRAIN_CROSS)
    for a in (0.0, 100.0, geo.LEN_TOP):
        q = geo.P1(a)
        ck("P1(%.0f) 落在顶边 y=L" % a, abs(q[1] - geo.L) < 1e-9 and -geo.LEN_TOP - 1e-9 <= q[0] <= 1e-9)
    for b in (0.0, 200.0, geo.LEN_LAP):
        q = geo.P2(b)
        ck("P2(%.0f) 落在门襟边" % b,
           abs(geo._cross((q[0] - geo.V[0], q[1] - geo.V[1]), geo.U_LAP)) < 1e-9)
    t = geo.line_param((0, 0), (1, 1), (0, 2), (1, -1))
    ck("line_param 解析求交 (1,1)", t is not None and abs(t[0] - 1) < 1e-9 and abs(t[1] - 1) < 1e-9)
    c = geo.construct_from_neckline((-200.0, geo.L - 20.0), (1.0, -0.5))
    ck("construct_from_neckline 可用", c is not None and
       abs(c["P1"][1] - geo.L) < 1e-9 and
       abs(geo._cross((c["P2"][0] - geo.V[0], c["P2"][1] - geo.V[1]), geo.U_LAP)) < 1e-9,
       "a=%.2f b=%.2f" % (c["a"], c["b"]) if c else "None")
    return r


def make_png(svg_path, png_path):
    """本机只有 Edge：用无头浏览器把 SVG 包进 HTML 等比缩放后截图"""
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge):
        return "跳过（未找到 Edge）"
    txt = open(svg_path, encoding="utf-8").read()
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', txt)
    if not m:
        return "跳过（SVG 无 viewBox）"
    w0, h0 = float(m.group(1)), float(m.group(2))
    W = 1800
    H = int(math.ceil(h0 * W / w0)) + 40
    html = os.path.join(OUT, "_preview.html")
    open(html, "w", encoding="utf-8").write(
        '<!doctype html><html><head><meta charset="utf-8"></head>'
        '<body style="margin:0;background:#fff">'
        '<img src="%s" style="width:%dpx;display:block">'
        '</body></html>' % (os.path.basename(svg_path), W))
    cmd = [edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--no-first-run", "--no-default-browser-check",
           "--user-data-dir=" + os.path.join(OUT, "_edgeprofile"),
           "--window-size=%d,%d" % (W, H),
           "--screenshot=" + png_path,
           "file:///" + html.replace("\\", "/")]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=90)
        return "OK" if os.path.exists(png_path) and os.path.getsize(png_path) > 1000 else \
               "失败 rc=%s %s" % (p.returncode, p.stderr.decode("utf-8", "ignore")[:200])
    except Exception as e:
        return "失败 %s" % e


def main():
    pieces, demo = geo.sheet_pieces()
    r = selftest(pieces)
    print("=== 第 1 步自检 ===")
    for name, ok, extra in r:
        print("  %s %s %s" % ("PASS" if ok else "FAIL", name, extra))
    fails = [n for n, ok, _ in r if not ok]
    if fails:
        print("!! 自检未过：", fails)
        return 1

    data = geo.step1_data()
    data["demo_placeholders"] = {"a": demo["demo_a"], "b": demo["demo_b"],
                                 "meaning": "仅用于画图示意，不是 P1/P2 的位置"}
    json.dump(data, open(os.path.join(OUT, "step1_P1P2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    params = dict(L=geo.L, LAP_DX=geo.LAP_DX, X_SHLD=geo.X_SHLD,
                  LEN_TOP=geo.LEN_TOP, LEN_LAP=round(geo.LEN_LAP, 4),
                  THETA_DEG=round(geo.THETA, 6), ANGLE_V_DEG=round(geo.ANGLE_V, 6),
                  a=None, b=None)
    svg = os.path.join(OUT, "step1_P1P2.svg")
    info = sheet.write_sheet(params, geo.sheet_pieces()[0], svg, TITLE, SUBTITLE, NOTES)
    print("\n=== 产物 ===")
    print("  ", info["svg"])
    print("  ", info["side"])
    png = os.path.join(OUT, "step1_P1P2.png")
    print("   PNG:", make_png(svg, png))
    print("   ", os.path.join(OUT, "step1_P1P2.json"))
    print("\nV=%s  S=%s  H=%s" % (geo.V, geo.S, geo.H))
    print("θ=%.6f°  |VH|=%.4f  ∠V=%.6f°" % (geo.THETA, geo.LEN_LAP, geo.ANGLE_V))
    print("P1 = V + a·(−1,0), a 待定   P2 = V + b·u, b 待定")
    return 0


if __name__ == "__main__":
    sys.exit(main())
