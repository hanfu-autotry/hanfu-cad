# -*- coding: utf-8 -*-
"""
裁片拼合成版 → 与丝博官图像素级比对
用法：python verification/overlay.py [front|back]
输出：verification/overlay_front.png / overlay_back.png + 控制台指标
"""
import sys, os, io, json, contextlib, math
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pattern"))
with contextlib.redirect_stdout(io.StringIO()):
    import build  # noqa: 触发一次 SVG 重建（幂等）

SRC = {
    "front": os.path.join(ROOT, "sources", "silk", "raw", "03_20200424163953961.jpg"),
    "back":  os.path.join(ROOT, "sources", "silk", "raw", "04_20200424163957242.jpg"),
}


# ---------- 1. 从官图提取成衣实心掩膜 ----------
def _dilate(m, it=1):
    o = m.copy()
    for _ in range(it):
        a = o.copy()
        a[1:, :] |= o[:-1, :]; a[:-1, :] |= o[1:, :]
        a[:, 1:] |= o[:, :-1]; a[:, :-1] |= o[:, 1:]
        o = a
    return o


def _erode(m, it=1):
    o = m.copy()
    for _ in range(it):
        a = o.copy()
        a[1:, :] &= o[:-1, :]; a[:-1, :] &= o[1:, :]
        a[:, 1:] &= o[:, :-1]; a[:, :-1] &= o[:, 1:]
        o = a
    return o


def garment_mask(path, thresh=0.72, close=3):
    im = Image.open(path).convert("L")
    W, H = im.size
    g = np.asarray(im, dtype=np.float32) / 255.0
    white = g >= thresh
    # 先把笔画加粗闭合 JPEG 断口，否则外部背景会漏进衣身内部
    stroke = _dilate(~white, close)
    passable = ~stroke

    Hh, Ww = passable.shape
    seen = np.zeros_like(passable, dtype=bool)
    stack = []
    for x in range(Ww):
        for y in (0, Hh - 1):
            if passable[y, x] and not seen[y, x]:
                seen[y, x] = True; stack.append((y, x))
    for y in range(Hh):
        for x in (0, Ww - 1):
            if passable[y, x] and not seen[y, x]:
                seen[y, x] = True; stack.append((y, x))
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < Hh and 0 <= nx < Ww and passable[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; stack.append((ny, nx))
    solid = _erode(~seen, close)

    # 取最大连通域（去掉尺寸文字等孤立块）
    m = solid > 0
    lab = np.zeros(m.shape, np.int32)
    best = (0, 0)
    cur = 0
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        cur += 1
        st = [(y0, x0)]
        lab[y0, x0] = cur
        n = 0
        while st:
            y, x = st.pop()
            n += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        st.append((ny, nx))
        if n > best[0]:
            best = (n, cur)
    mask = (lab == best[1])
    return mask, W, H


# ---------- 2. 裁片拼合成版 ----------
def sample_cmds(cmds, n=28):
    """把 M/L/C 命令采样为多边形点列（服饰坐标 y 向上）"""
    pts, cur = [], None
    for c in cmds:
        if c[0] == "M":
            cur = c[1]
            pts.append(cur)
        elif c[0] == "L":
            cur = c[1]
            pts.append(cur)
        elif c[0] == "Q":
            p0 = cur
            ctl, p3 = c[1], c[2]
            for i in range(1, n + 1):
                tt = i / n
                x = (1 - tt) ** 2 * p0[0] + 2 * (1 - tt) * tt * ctl[0] + tt ** 2 * p3[0]
                y = (1 - tt) ** 2 * p0[1] + 2 * (1 - tt) * tt * ctl[1] + tt ** 2 * p3[1]
                pts.append((x, y))
            cur = p3
        elif c[0] == "C":
            p0 = cur
            p1, p2, p3 = c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n
                x = ((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0]
                     + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0])
                y = ((1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1]
                     + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1])
                pts.append((x, y))
            cur = p3
    return pts


def assembly_polys(view="front"):
    polys = []
    keep = ["后片半", "接袖"] if view == "back" else ["后片半", "前片", "接袖"]
    for p in build.PIECES:
        if p["name"] not in keep:
            continue
        base = sample_cmds(p["cmds"])
        polys.append(base)
        polys.append([(-x, y) for (x, y) in base])
    if view == "front":
        # 领缘条贴缝后竖起，官图轮廓含这一段
        w, h = build.NECK / 2, 40.0
        polys.append([(-w, build.L), (w, build.L), (w, build.L + h), (-w, build.L + h)])
    return polys


def raster(polys, W, H, sx, sy, cx, y0):
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        xy = [(cx + x * sx, y0 - y * sy) for (x, y) in poly]
        if len(xy) >= 3:
            d.polygon(xy, fill=255)
    return np.array(img) > 0


# ---------- 3. 比对 ----------
def register(src, polys, W, H, sx_fix=None):
    """配准：横向由 通袖 2180 锁定 sx；纵向 sy / 平移 cx,y0 由 IoU 最大化求取"""
    ys, xs = np.nonzero(src)
    x0, x1, y0s, y1s = xs.min(), xs.max(), ys.min(), ys.max()
    src_w = x1 - x0 + 1
    sx = sx_fix if sx_fix else src_w / 2180.0
    cx0 = (x0 + x1) / 2.0

    best = (-1, None)
    for k in range(21):                      # 纵向尺度：0.88 ~ 1.16 × sx
        sy = sx * (0.88 + 0.014 * k)
        for dy0 in range(-14, 15, 2):        # 下摆基线微调
            for dcx in (-4, -2, 0, 2, 4):
                m = raster(polys, W, H, sx, sy, cx0 + dcx, y1s + dy0)
                i = np.logical_and(src, m).sum()
                u = np.logical_or(src, m).sum()
                iou = i / max(u, 1)
                if iou > best[0]:
                    best = (iou, (sx, sy, cx0 + dcx, y1s + dy0))
    return best


def run(view="front"):
    src, W, H = garment_mask(SRC[view])
    polys = assembly_polys(view)
    iou, prm = register(src, polys, W, H)
    sx, sy, cx, y0 = prm

    ys, xs = np.nonzero(src)
    x0, x1, y0s, y1s = xs.min(), xs.max(), ys.min(), ys.max()
    model = raster(polys, W, H, sx, sy, cx, y0)
    inter = np.logical_and(src, model).sum()
    union = np.logical_or(src, model).sum()
    prec = inter / max(model.sum(), 1)
    rec = inter / max(src.sum(), 1)

    devs_top, devs_bot = [], []
    for x in range(W):
        a = np.nonzero(src[:, x])[0]
        b = np.nonzero(model[:, x])[0]
        if a.size and b.size:
            devs_top.append(abs(int(a.min()) - int(b.min())))
            devs_bot.append(abs(int(a.max()) - int(b.max())))
    devs_top = np.array(devs_top) if devs_top else np.array([0])
    devs_bot = np.array(devs_bot) if devs_bot else np.array([0])

    stats = {
        "view": view,
        "src_bbox": [int(x0), int(x1), int(y0s), int(y1s)],
        "src_w_px": int(x1 - x0 + 1), "src_h_px": int(y1s - y0s + 1),
        "reg_sx": round(sx, 6), "reg_sy": round(sy, 6),
        "anisotropy_pct": round(abs(sx - sy) / max(sx, sy) * 100, 2),
        "mm_per_px_x": round(1 / sx, 3), "mm_per_px_y": round(1 / sy, 3),
        "area_src": int(src.sum()), "area_model": int(model.sum()),
        "iou": round(float(inter / max(union, 1)), 4),
        "precision": round(float(prec), 4), "recall": round(float(rec), 4),
        "top_dev_mean_px": round(float(devs_top.mean()), 2),
        "top_dev_p95_px": round(float(np.percentile(devs_top, 95)), 2),
        "bot_dev_mean_px": round(float(devs_bot.mean()), 2),
        "bot_dev_p95_px": round(float(np.percentile(devs_bot, 95)), 2),
    }

    ov = np.full((H, W, 3), 255, np.uint8)
    ov[src & ~model] = [220, 60, 60]
    ov[model & ~src] = [60, 110, 220]
    ov[src & model] = [150, 120, 190]
    out = Image.fromarray(ov).resize((W * 2, H * 2), Image.NEAREST)
    fp = os.path.join(ROOT, "verification", "overlay_%s.png" % view)
    out.save(fp)
    stats["overlay"] = fp
    return stats


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    for v in (args or ["front"]):
        print(json.dumps(run(v), ensure_ascii=False, indent=1))
