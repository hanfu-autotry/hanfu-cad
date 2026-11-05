# -*- coding: utf-8 -*-
"""
接袖版专项自检 —— 只读 out/ 下的 .pieces.json（不依赖 build.py 内部变量），
全部指标从几何反测，再与规格常量比对：
  接袖长（随码）/ 预开领 100 / 领缘宽 70 / 腕口（随码） / 通袖 2×(肩点+衣身袖+接袖)
另验证：袖底缘三点共线、接缝边垂直无圆角、接缝零转折、前片镜像、排料不重叠。

用法：python verify_接袖.py [pieces.json]
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEF = os.path.join(ROOT, "out", "vendor_男_M", "对穿交_接袖_男_M.pieces.json")
FP = sys.argv[1] if len(sys.argv) > 1 else DEF

J = json.load(open(FP, encoding="utf-8"))
R, P = J["resolved"], J["params"]
PIECES = {p["name"]: p for p in J["pieces"]}

SPEC_NECK, SPEC_COLW = 100.0, 70.0
SPEC_BODY_SL = 0.377      # 衣身袖长 / (通袖半 − 肩点)，接袖缝位置比例
FAILS, OKS = [], []


def chk(name, cond, detail=""):
    (OKS if cond else FAILS).append(name)
    print("  %s %-42s %s" % ("✓" if cond else "✗", name, detail))


def sample(cmds, n=60):
    pts, segs, cur = [], [], None
    for c in cmds:
        if c[0] == "M":
            cur = tuple(c[1]); pts.append(cur)
        elif c[0] == "L":
            q = tuple(c[1])
            for i in range(1, 13):
                u = i / 12.0
                pts.append((cur[0] + (q[0]-cur[0])*u, cur[1] + (q[1]-cur[1])*u))
            segs.append(("L", cur, q)); cur = q
        elif c[0] == "C":
            p1, p2, p3 = (tuple(x) for x in c[1:4])
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append((mt**3*cur[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0],
                            mt**3*cur[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]))
            segs.append(("C", cur, p3, p1, p2)); cur = p3
    return pts, segs


def verts(pc):
    return [tuple(c[1]) for c in pc["cmds"] if c[0] in "ML"]


SAMP = {k: sample(v["cmds"], 300) for k, v in PIECES.items()}
print("自检：%s\n" % os.path.basename(FP).replace(".pieces.json", ""))

# ── 几何反测 ──────────────────────────────────────────────
ext = verts(PIECES["接袖"])
x_root = min(v[0] for v in ext); x_wrist = max(v[0] for v in ext)
js_len = x_wrist - x_root
root_ys = [v[1] for v in ext if abs(v[0]-x_root) < .01]
wrist_ys = [v[1] for v in ext if abs(v[0]-x_wrist) < .01]
root_h = max(root_ys) - min(root_ys)
wrist_h = max(wrist_ys) - min(wrist_ys)

bk = SAMP["后片半"][0]
Lm = max(p[1] for p in bk)
x_arm = R["X_ARM"]
x_seam = max(p[0] for p in bk)
sleeve_body = x_seam - x_arm
armpit_depth = Lm - R["Y_ARM"]

ft = SAMP["前片"][0]
neck_half = max(p[0] for p in ft if abs(p[1] - Lm) < 0.6)
col = verts(PIECES["领缘条"])
col_w = max(v[1] for v in col) - min(v[1] for v in col)
col_len = max(v[0] for v in col) - min(v[0] for v in col)

ka = math.tan(math.radians(R["UND_ANG"]))
und_y = lambda x: R["Y_ARM"] + (x - R["X_ARM"]) * ka

print("[1] 关键尺寸（几何反测 → 规格）")
chk("通袖 = 2×(肩点+衣身袖+接袖)", abs(2*x_wrist - 2*(x_arm + sleeve_body + js_len)) < 0.01,
    "%.0f" % (2*x_wrist))
chk("接袖长 = 通袖半 − 肩点 − 衣身袖", abs(js_len - (x_wrist - x_arm - sleeve_body)) < 0.01, "%.2f" % js_len)
chk("衣身袖 = %.3f×(通袖半−肩点)（接袖缝位置）" % SPEC_BODY_SL,
    abs(sleeve_body - SPEC_BODY_SL*(x_wrist - x_arm)) < 1.2,
    "%.1f（应为 %.1f）" % (sleeve_body, SPEC_BODY_SL*(x_wrist-x_arm)))
chk("袖根 = 接袖根边高（派生）", abs(root_h - R["SEAM_H"]) < 0.01, "%.2f" % root_h)
chk("腕口 = 接袖腕边高", abs(wrist_h - P["WRIST"]) < 0.01, "%.2f" % wrist_h)
kt = math.tan(math.radians(P["TILT_DEG"]))
chk("袖根 = 腕口 + 接袖长·(tan袖底角+tan落肩)", abs(root_h - (wrist_h + js_len*(ka+kt))) < 0.05,
    "%.2f vs %.2f" % (root_h, wrist_h + js_len*(ka+kt)))
chk("预开领 = 2×前片内端让口", abs(2*neck_half - SPEC_NECK) < 0.01,
    "%.2f（单侧 %.1f）" % (2*neck_half, neck_half))
chk("领缘宽 = 70", abs(col_w - SPEC_COLW) < 0.01, "%.1f" % col_w)
chk("腋深 = 0.36×(衣长−30)（厂商规则）", abs(armpit_depth - 0.36*(Lm-30)) < 0.6,
    "%.1f（衣长 %.0f）" % (armpit_depth, Lm))

print("\n[2] 袖底缘（本版核心）")
dev = max(abs(R["U_ARM"][1] - und_y(R["U_ARM"][0])),
          abs(R["Y_SEAM_BOT"] - und_y(R["X_CUFF"])),
          abs(R["Y_JS_BOT"] - und_y(R["X_JS"])))
chk("腋下圆角终点/接袖根/腕口下角 三点共线", dev < 0.05,
    "偏离 %.5f mm（直线角 %.2f°）" % (dev, R["UND_ANG"]))
chk("腋下圆角 R = 45（衣身原样）", abs(R["R_ARM_F"] - 45.0) < 0.01, "%.0f" % R["R_ARM_F"])
pts_und = [p for p in bk if p[0] >= R["U_ARM"][0] - 0.01 and R["Y_ARM"] - 50 <= p[1] <= R["Y_SEAM_BOT"] + 0.5]
mono = all(pts_und[i+1][0] >= pts_und[i][0] - 1e-6 for i in range(len(pts_und)-1))
chk("袖底缘 x 单调（无回折）", mono, "n=%d" % len(pts_und))

print("\n[3] 接袖片（×4）")
chk("包围盒 = 接袖长 × 袖根",
    abs((max(v[0] for v in ext)-min(v[0] for v in ext)) - js_len) < 0.01
    and abs((max(v[1] for v in ext)-min(v[1] for v in ext)) - root_h) < 0.01,
    "%.1f × %.1f" % (js_len, root_h))
chk("数量 ×4（前后片各一）", PIECES["接袖"]["qty"] == 4, "qty=%d" % PIECES["接袖"]["qty"])
chk("轮廓全直线（无圆角）", sum(1 for c in PIECES["接袖"]["cmds"] if c[0] in ("C", "Q")) == 0,
    "4 顶点 / 0 曲线段")
chk("根边垂直（x 恒定）", abs(max(v[0] for v in ext if abs(v[1]-min(root_ys)) < .01) -
                            min(v[0] for v in ext if abs(v[1]-min(root_ys)) < .01)) < 0.01,
    "x=%.2f" % x_root)
chk("腕口垂直（x 恒定）", abs(max(v[0] for v in ext if abs(v[1]-min(wrist_ys)) < .01) -
                            min(v[0] for v in ext if abs(v[1]-min(wrist_ys)) < .01)) < 0.01,
    "x=%.2f" % x_wrist)
ang = []
for i in range(4):
    a, b, c = ext[i], ext[(i+1) % 4], ext[(i+2) % 4]
    v1 = (b[0]-a[0], b[1]-a[1]); v2 = (c[0]-b[0], c[1]-b[1])
    cs = (v1[0]*v2[0] + v1[1]*v2[1]) / (math.hypot(*v1)*math.hypot(*v2))
    ang.append(math.degrees(math.acos(max(-1, min(1, cs)))))
want = sorted([90 - R["UND_ANG"], 90 - P["TILT_DEG"], 90 + P["TILT_DEG"], 90 + R["UND_ANG"]])
chk("四角尖角、角度 = 90°±斜度", all(abs(a-w) < 0.05 for a, w in zip(sorted(ang), want)),
    "/".join("%.2f" % a for a in ang))

print("\n[4] 衣身接缝边")
vb = verts(PIECES["后片半"])
vseam = [(vb[i], vb[i+1]) for i in range(len(vb)-1)
         if abs(vb[i][0]-x_seam) < 0.01 and abs(vb[i+1][0]-x_seam) < 0.01]
chk("接缝边为一条直线段（无圆角）", len(vseam) == 1 and
    abs(abs(vseam[0][0][1]-vseam[0][1][1]) - root_h) < 0.01,
    "%.2f 长" % (abs(vseam[0][0][1]-vseam[0][1][1]) if vseam else -1))
if vseam:
    lo = min(vseam[0][0][1], vseam[0][1][1])
    chk("接缝下角落在袖底线上（袖底连续无台阶）", abs(lo - und_y(x_seam)) < 0.01, "y=%.2f" % lo)
for nm in ("后片半", "前片"):
    sm = [p for p in SAMP[nm][0] if abs(abs(p[0]) - x_seam) < 0.5 and p[1] > 0.6*Lm]
    chk("%s 接缝边垂直" % nm,
        len(sm) >= 2 and max(p[0] for p in sm) - min(p[0] for p in sm) < 0.01,
        "x=%.2f，高 %.2f" % (sm[0][0], max(p[1] for p in sm)-min(p[1] for p in sm)))

print("\n[5] 接缝零转折 / 前后镜像")
pf_ = [p for p in SAMP["前片"][0] if p[0] <= -x_arm + 0.01 and p[1] >= R["Y_ARM"] - 50]
pb_ = [p for p in bk if p[0] >= x_arm - 0.01 and p[1] >= R["Y_ARM"] - 50]
dmax = max(min(math.hypot(p[0]+q[0], p[1]-q[1]) for q in pb_) for p in pf_) if pf_ and pb_ else 9e9
chk("前片袖部与后片镜像重合", dmax < 1.0, "最大偏差 %.3f mm" % dmax)
near = [p for p in bk if 20 < abs(p[0]-x_seam) < 40 and R["Y_ARM"] <= p[1] <= R["Y_SEAM_BOT"] + 10]
dline = max(abs(p[1] - und_y(p[0])) for p in near)
chk("接缝±40mm 内袖底缘同一直线（折角 0°）", dline < 0.01, "最大偏离 %.5f mm" % dline)

print("\n[6] 领缘条")
lapel = math.hypot(Lm, R["LAP_DX"] - neck_half)
need = 2*lapel + 2*neck_half
chk("长度 ≥ 2×门襟斜边 + 后领口", col_len >= need,
    "%.0f ≥ %.0f（余量 %.0f）" % (col_len, need, col_len-need))

print("\n[7] 排料")
ov = []
bs = [(p["name"], p["box"]) for p in J["pieces"]]
for i in range(len(bs)):
    for j in range(i+1, len(bs)):
        a, b = bs[i][1], bs[j][1]
        if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
            ov.append((bs[i][0], bs[j][0]))
chk("裁片包围盒互不重叠", not ov, str(ov))
body_w = {p["name"]: p["box"][2]-p["box"][0] for p in J["pieces"]
          if p["name"] in ("后片半", "前片", "接袖")}
chk("衣身三片 ≤ 110cm 门幅可整幅裁", max(body_w.values()) <= 1100,
    " / ".join("%s %.0f" % (k, v) for k, v in body_w.items()))

print("\n%s   通过 %d / 失败 %d" % (
    "✅ 全部通过" if not FAILS else "❌ 存在失败项", len(OKS), len(FAILS)))
sys.exit(0 if not FAILS else 1)
