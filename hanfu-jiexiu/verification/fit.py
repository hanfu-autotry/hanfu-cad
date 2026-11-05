# -*- coding: utf-8 -*-
"""自动拟合：在锁定标注尺寸（通袖/摆宽/衣长/袖口）的前提下，
   调形状参数（腋点、袖底弧控制点）使与官图 IoU 最大。"""
import sys, os, io, json, random, contextlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pattern"))
sys.path.insert(0, os.path.join(ROOT, "verification"))
with contextlib.redirect_stdout(io.StringIO()):
    import build
from overlay import garment_mask, sample_cmds, SRC


def polys_now():
    ps = []
    for p in (build.back_half(), build.front_panel(), build.sleeve_piece()):
        base = sample_cmds(p["cmds"], n=16)
        ps.append(base)
        ps.append([(-x, y) for (x, y) in base])
    w = build.NECK / 2
    ps.append([(-w, build.L), (w, build.L), (w, build.L + 40), (-w, build.L + 40)])
    return ps


def apply(v):
    build.X_ARM = v[0]
    build.Y_ARM = v[1]
    build.U_P0 = (v[0], v[1])
    build.U_P1 = (v[2], v[3])
    build.U_P2 = (v[4], v[5])
    build.Y_CUFF_MID = build.sleeve_y(build.X_CUFF)
    build.Y_CUFF_TOP = build.Y_CUFF_MID + build.CUFF / 2
    build.Y_CUFF_BOT = build.Y_CUFF_MID - build.CUFF / 2
    build.U_P3 = (build.X_CUFF, build.Y_CUFF_BOT)


def raster(polys, W, H, sx, sy, cx, y0):
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        xy = [(cx + x * sx, y0 - y * sy) for (x, y) in poly]
        if len(xy) >= 3:
            d.polygon(xy, fill=255)
    return np.array(img) > 0


def norm_mask(m, NW=560, NH=None):
    """裁到外接框后统一缩放，剔除位置与整体比例，只比形状"""
    ys, xs = np.nonzero(m)
    if not len(xs):
        return np.zeros((200, NW), bool)
    sub = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = sub.shape
    NH = NH or max(1, int(round(NW * h / w)))
    im = Image.fromarray((sub * 255).astype(np.uint8)).resize((NW, NH), Image.BILINEAR)
    return np.array(im) > 127


def main():
    src, W, H = garment_mask(SRC["front"])
    ys, xs = np.nonzero(src)
    x0, x1, y0s, y1s = xs.min(), xs.max(), ys.min(), ys.max()
    sx = (x1 - x0 + 1) / 2180.0
    cx = (x0 + x1) / 2.0
    sy = sx
    y0 = float(y1s) + 2

    SRC_N = norm_mask(src, 560)
    NH = SRC_N.shape[0]

    def score(v):
        apply(v)
        m = raster(polys_now(), W, H, sx, sy, cx, y0)
        M = norm_mask(m, 560, NH)
        i = np.logical_and(SRC_N, M).sum()
        u = np.logical_or(SRC_N, M).sum()
        return i / max(u, 1)

    base = [build.X_ARM, build.Y_ARM, build.U_P1[0], build.U_P1[1], build.U_P2[0], build.U_P2[1]]
    best = (score(base), base[:])
    print("baseline IoU %.4f  %s" % best)

    random.seed(7)
    cur = best[1][:]
    for it in range(1200):
        amp = 100 * (1 - it / 1200) + 8
        cand = [cur[0] + random.uniform(-amp, amp),
                cur[1] + random.uniform(-amp, amp),
                cur[2] + random.uniform(-amp * 1.4, amp * 1.4),
                cur[3] + random.uniform(-amp, amp),
                cur[4] + random.uniform(-amp * 1.4, amp * 1.4),
                cur[5] + random.uniform(-amp, amp)]
        cand = [max(430, min(680, cand[0])), max(330, min(720, cand[1])),
                max(580, min(980, cand[2])), max(300, min(700, cand[3])),
                max(780, min(1120, cand[4])), max(300, min(760, cand[5]))]
        if cand[2] >= cand[4] - 60:      # 控制点须单调，避免 S 形拐点
            cand[2] = cand[4] - 60
        s = score(cand)
        if s > best[0]:
            best = (s, cand[:])
            cur = cand[:]
            print("  it%3d  IoU %.4f  %s" % (it, s, [round(x, 1) for x in cand]))

    print(json.dumps({"best_iou": round(best[0], 4),
                      "params": {"X_ARM": round(best[1][0], 1), "Y_ARM": round(best[1][1], 1),
                                 "U_P1": [round(best[1][2], 1), round(best[1][3], 1)],
                                 "U_P2": [round(best[1][4], 1), round(best[1][5], 1)]}},
                     ensure_ascii=False, indent=1))
    out = os.path.join(ROOT, "verification", "fit_result.json")
    json.dump({"best_iou": best[0], "vec": best[1]}, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
