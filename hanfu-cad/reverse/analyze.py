import bpy, json, sys
from collections import deque
import numpy as np

def load_gray(path):
    img = bpy.data.images.load(path)
    try:
        img.colorspace_settings.name = 'Non-Color'
    except Exception:
        pass
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    a = buf.reshape(h, w, 4)[::-1]
    g = a[:, :, :3].mean(axis=2)
    bpy.data.images.remove(img)
    return g, w, h

def dilate(m, it=1):
    out = m.copy()
    for _ in range(it):
        a = out.copy()
        a[1:, :] |= out[:-1, :]
        a[:-1, :] |= out[1:, :]
        a[:, 1:] |= out[:, :-1]
        a[:, :-1] |= out[:, 1:]
        out = a
    return out

def largest_component(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    cur = 0
    best = (0, 0)
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        cur += 1
        q = deque([(y0, x0)])
        lab[y0, x0] = cur
        n = 0
        while q:
            y, x = q.popleft()
            n += 1
            for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = cur
                    q.append((ny, nx))
        if n > best[0]:
            best = (n, cur)
    return lab == best[1], cur, best[0]

def analyze(path, name):
    g, w, h = load_gray(path)
    raw = g < 0.72
    mask = dilate(raw, 2)
    comp, ncomp, npix = largest_component(mask)
    ys, xs = np.nonzero(comp)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    out = {"file": name, "w": w, "h": h, "dark_px": int(raw.sum()),
           "components_after_dilate": int(ncomp), "main_px": int(npix),
           "bbox": [x0, x1, y0, y1], "bbox_w": x1-x0, "bbox_h": y1-y0}

    def col(x):
        c = np.nonzero(comp[:, x])[0]
        return [int(c.min()), int(c.max()), int(c.size)] if c.size else None

    def row(y):
        r = np.nonzero(comp[y, :])[0]
        return [int(r.min()), int(r.max()), int(r.size)] if r.size else None

    step = max(1, (x1 - x0) // 30)
    out["cols"] = {int(x): col(x) for x in range(x0, x1 + 1, step)}
    stepy = max(1, (y1 - y0) // 22)
    out["rows"] = {int(y): row(y) for y in range(y0, y1 + 1, stepy)}

    runs = {}
    for frac in (0.03, 0.08, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95):
        y = int(y0 + (y1 - y0) * frac)
        r = comp[y, :].astype(np.int8)
        d = np.diff(np.concatenate([[0], r, [0]]))
        st = np.nonzero(d == 1)[0]
        en = np.nonzero(d == -1)[0] - 1
        runs["y%d_%.2f" % (y, frac)] = [[int(a), int(b)] for a, b in zip(st, en)]
    out["runs"] = runs
    return out

res = [analyze(sys.argv[-2], "front"), analyze(sys.argv[-1], "back")]
print("<<<JSON>>>")
print(json.dumps(res, ensure_ascii=False))
print("<<<END>>>")
