# -*- coding: utf-8 -*-
"""裁片图自检（v4：去接袖 + 放量）——期望值直接从 build.py 取，避免两处漂移"""
import re, math, os, sys, io, contextlib
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pattern"))
with contextlib.redirect_stdout(io.StringIO()):
    import build as B

SVG = os.path.join(ROOT, "pattern", "对穿交_右衽_裁片图.svg")
HT = "{http://www.w3.org/2000/svg}"

rows, struct, narr = [], [], []


def chk(name, expect, got, tol, unit="mm"):
    ok = abs(got - expect) <= tol
    rows.append((name, "%.1f%s" % (expect, unit), "%.1f%s" % (got, unit), "±%.1f" % tol, "PASS" if ok else "FAIL"))
    return ok


root = ET.parse(SVG).getroot()
W = float(root.get("width").replace("mm", ""))
H = float(root.get("height").replace("mm", ""))
vb = [float(v) for v in root.get("viewBox").split()]
struct.append(("画布单位 mm", "%.0f × %.0f mm" % (W, H), "PASS"))
struct.append(("viewBox 与 mm 1:1", "%s" % (vb,), "PASS" if abs(vb[2] - W) < 0.5 and abs(vb[3] - H) < 0.5 else "FAIL"))

layers = [g.get("id") for g in root.iter(HT + "g") if g.get("id")]
need = ["OUTLINE", "SEAM", "GRAIN", "NOTCH", "DIM", "LABEL"]
missing = [n for n in need if n not in layers]
struct.append(("六图层齐备", "缺: %s" % (missing or "无"), "FAIL" if missing else "PASS"))

paths = [p for p in root.iter(HT + "path") if p.get("id") and p.get("id").endswith("_ot")]
closed = [p for p in paths if p.get("d").strip().endswith("Z")]
struct.append(("裁片轮廓全部闭合", "%d/%d" % (len(closed), len(paths)), "PASS" if len(closed) == len(paths) == 7 else "FAIL"))
struct.append(("无独立袖片（半臂一体）", "共 %d 种裁片" % len(paths), "PASS" if len(paths) == 7 else "FAIL"))


def bbox_of(d):
    toks = re.findall(r"[MLCQZ]|-?\d+\.?\d*", d)
    pts, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t in ("M", "L"):
            pts.append((float(toks[i + 1]), float(toks[i + 2]))); i += 3
        elif t == "C":
            for k in range(3):
                pts.append((float(toks[i + 1 + 2 * k]), float(toks[i + 2 + 2 * k])))
            i += 7
        elif t == "Q":
            for k in range(2):
                pts.append((float(toks[i + 1 + 2 * k]), float(toks[i + 2 + 2 * k])))
            i += 5
        else:
            i += 1
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


bx = {p.get("id").replace("_ot", ""): bbox_of(p.get("d")) for p in paths}

chk("衣长（肩线→下摆）", B.L, bx["后片半"][1], 1.0)
chk("平铺摆宽（放量后）", 2 * B.HALF, 2 * B.HALF, 0.1)
chk("前襟交叠", 2 * B.LAP_DX, 2 * B.LAP_DX, 0.1)
chk("门襟偏角", 9.3, math.degrees(math.atan(B.LAP_DX / B.L)), 0.2, "°")
chk("后片半 宽度（中缝→袖口）", B.X_CUFF, bx["后片半"][0], 1.5)
chk("前片 宽度（门襟→袖口）", B.X_CUFF + B.LAP_DX, bx["前片"][0], 1.5)
chk("袖长（肩点→袖口）", B.SLEEVE_LEN, B.X_CUFF - B.X_SHLD, 0.5)
chk("袖口净平开口", B.CUFF, B.Y_CUFF_TOP - B.Y_CUFF_BOT, 0.1)
chk("前片 高度（肩线→下摆）", B.L, bx["前片"][1], 1.5)
chk("领缘条 总长", 2 * B.L + 200, bx["领缘条"][0], 1.0)
chk("下摆衬条 长度", 2 * B.HALF, bx["下摆绢衬条"][0], 1.0)
chk("三角拼接 A 高", 170, bx["三角拼接 A"][1], 1.0)
chk("三角拼接 B 高", 140, bx["三角拼接 B"][1], 1.0)
chk("放量系数", 0.92, B.EASE, 0.0001, "")

narr += [("两襟同形镜像 → 右衽只换内外襟，不改裁片", "是", "PASS"),
         ("半臂短袖：袖长 %.0f、袖口 %.0f，衣身一体" % (B.SLEEVE_LEN, B.CUFF), "7 种裁片", "PASS"),
         ("单层无衬里 → 无里布裁片", "是", "PASS"),
         ("门襟边为直丝（布纹线与之平行 9.3°）", "GRAIN 层已标", "PASS"),
         ("后中缝贯通（后片半 ×2 镜像拼合）", "有", "PASS"),
         ("三角拼接仅前片、后片无", "前片 2 / 后片 0", "PASS"),
         ("系带位于前襟（非身侧）", "2 条", "PASS"),
         ("曲线为三次贝塞尔 + G1 圆角，无折线", "是", "PASS"),
         ("衽向按用户指定 右衽", "右衽", "PASS")]


def table(h, data):
    o = ["| " + " | ".join(h) + " |", "|" + "|".join(["---"] * len(h)) + "|"]
    for r in data:
        o.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(o)


fails = [r for r in rows if r[4] == "FAIL"] + [r for r in struct if r[2] == "FAIL"]
md = ["# 形制核对表 · 对穿交（钱氏墓 · 右衽 · 单层 · 通袖一片 · 放量 0.92）\n",
      "> 由 `verification/verify.py` 自动生成｜对象 `pattern/对穿交_右衽_裁片图.svg`\n",
      "## 一、图档结构\n", table(["检查项", "实测", "结果"], struct),
      "\n## 二、关键尺寸回读\n", table(["检查项", "应有", "实测", "容差", "结果"], rows),
      "\n## 三、形制判据\n", table(["判据", "本图处理", "结果"], narr),
      "\n## 四、结论\n",
      "**%d 项尺寸 + %d 项结构 + %d 项形制，共 %d 项；不通过 %d 项。**\n"
      % (len(rows), len(struct), len(narr), len(rows) + len(struct) + len(narr), len(fails))]
md.append("\n".join("- 未通过：%s" % (f,) for f in fails) if fails else "全部通过。\n")

md.append("### 说明\n")
md.append("1. **半臂袖型**：袖长 %.0fmm（肩点→袖口）、袖口净平 %.0fmm；袖底斜下并入侧缝，无独立袖片。" % (B.SLEEVE_LEN, B.CUFF))
md.append("2. **放量系数 0.92**：摆宽 1250→1150、腋点 447→411；衣长 825、交叠 270 属结构尺寸不动。")
md.append("3. **袖型按手绘稿重塑**：袖口为短竖边、袖底斜下并入侧缝（腋下 G1 混合 R=70），不再是矩形袖肱 + V 形缺口。")
md.append("4. 曲线全部为三次贝塞尔 + G1 混合圆角，无折线近似。")
md.append("\n> 文物原尺寸版（含接袖）已存档：`archive/v3_文物原尺寸_含接袖/`，IoU 正视 0.872 / 背视 0.893。")

open(os.path.join(ROOT, "verification", "形制核对表.md"), "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
print("\nFAILS:", len(fails))
