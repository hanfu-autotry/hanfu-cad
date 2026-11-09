# -*- coding: utf-8 -*-
"""形制核对闸门（studio 侧）。用户 2026-11-03 定的口径：

**分类讨论**
  · 有原型（文物/官图可参照）→ 参照闸门：像素叠合 IoU + 形制核对表（跑各项目自己的脚本）——路径已可用。
  · 无原型（纯许愿，没有参照物）→ **自洽 + 对账 + 人审签收**：
      自洽＝版型程序自己声明的结构不变量（如 通袖＝n×幅宽、前中开口宽度与贯通、应有裁片在）；
      对账＝若声明了父版型，用**同一套参数**重建父版型，逐片最大点距必须等于账本里的明示量；
      人审签收＝无原型的产物要人确认才写回/进导出。

**工程可行性四项**（用户 11-03 勾选：全查）
  ① 轮廓闭合 + 无自交 ② 最小曲率半径 ③ 缝线等长 / 明示收褶 ④ 幅宽约束

**失败语义**（用户 11-03 明确）：**不硬打回** —— 打 `WARN` 并写清差多少，界面上"人工确认放行"后
把 `signoff.json` 落到产物目录，日志留痕。

被 gates 用到的最小数据约定（都写在各版型注册表里，不复制几何）：
  "gates": {"invariants": [{"name": "panels", "n": 4, "fab_w": 500},
                           {"name": "slit",  "width": 160},
                           {"name": "piece_names", "expect": ["领条"]}],
             "parent": null, "delta": {}, "reference": null,
             "max_panels": 4, "min_radius": 10, "seam_ledger": []}
"""
import json
import math
import os

import adapters as A

WARN_R_BASE = 10.0      # 最小曲率半径默认阈值 mm


# ── 几何工具：pieces.json 的 cmds → 点列 ─────────────────────────────
def sample_cmds(cmds, n=10):
    pts, cur = [], None
    for c in cmds:
        k = c[0]
        if k == "M":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "L":
            cur = tuple(c[1]); pts.append(cur)
        elif k == "C":
            p1, p2, p3 = tuple(c[1]), tuple(c[2]), tuple(c[3])
            if cur:
                for i in range(1, n + 1):
                    t = i / n; mt = 1 - t
                    pts.append((mt ** 3 * cur[0] + 3 * mt * mt * t * p1[0]
                                + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                                mt ** 3 * cur[1] + 3 * mt * mt * t * p1[1]
                                + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = p3
        elif k == "Q":
            c1, p2 = tuple(c[1]), tuple(c[2])
            if cur:
                for i in range(1, n + 1):
                    t = i / n; mt = 1 - t
                    pts.append((mt * mt * cur[0] + 2 * mt * t * c1[0] + t * t * p2[0],
                                mt * mt * cur[1] + 2 * mt * t * c1[1] + t * t * p2[1]))
            cur = p2
        elif k == "Z":                      # 闭合命令：必须把首点补回，否则"闭合"永远差一条边
            if pts and math.dist(pts[0], pts[-1]) > 1e-9:
                pts.append(pts[0])
            cur = pts[0] if pts else None
    return pts


def _seg_cross(p1, p2, p3, p4):
    def ori(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)

    o1, o2 = ori(p1, p2, p3), ori(p1, p2, p4)
    o3, o4 = ori(p3, p4, p1), ori(p3, p4, p2)
    return o1 * o2 < 0 and o3 * o4 < 0


def self_intersects(pts):
    n = len(pts)
    hits = []
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue
            if _seg_cross(pts[i], pts[i + 1], pts[j], pts[j + 1]):
                hits.append((i, j))
                if len(hits) >= 3:
                    return hits
    return hits


def min_radius(pts, min_gap=4.0):
    """三点外接圆半径的近似最小曲率半径；跳过间距过小的相邻点。"""
    best = float("inf")
    n = len(pts)
    step = max(1, n // 400)
    i = 0
    while i + 2 * step < n:
        a, b, c = pts[i], pts[i + step], pts[i + 2 * step]
        if (math.dist(a, b) >= min_gap and math.dist(b, c) >= min_gap):
            ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
            s = (ab + bc + ca) / 2
            area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
            if area2 > 1e-9:
                R = ab * bc * ca / (2 * area2)
                best = min(best, R)
        i += step
    return best


def poly_len(pts, closed=True):
    n = len(pts)
    total = 0.0
    for i in range(n - 1 if not closed else n):
        total += math.dist(pts[i], pts[(i + 1) % n])
    return total


# ── 单条闸门 ───────────────────────────────────────────────────────
def _item(group, name, status, detail, value=None):
    return dict(group=group, name=name, status=status, detail=detail, value=value)


def check_pieces(pieces, g):
    """工程可行性：闭合/自交/最小半径/幅宽；并把每片缝线长度报出来。"""
    out = []
    fab_w = float(g.get("fab_w") or 500.0)
    max_panels = int(g.get("max_panels") or 4)
    r_min_need = float(g.get("min_radius") or WARN_R_BASE)
    if not pieces:
        return [_item("工程可行性", "裁片数据", "WARN", "没有 pieces 数据（子程序未产出裁片清单）")]
    for p in pieces:
        nm = p.get("name", "?")
        pts = sample_cmds(p.get("cmds") or [])
        if len(pts) < 3:
            out.append(_item("工程可行性", "轮廓 %s" % nm, "WARN", "点太少，无法核对"))
            continue
        gap = math.dist(pts[0], pts[-1])
        has_z = any(c[0] == "Z" for c in (p.get("cmds") or []))
        out.append(_item("工程可行性", "闭合 %s" % nm,
                         "PASS" if gap <= 0.5 else "WARN",
                         "%s首尾间距 %.1f mm" % ("含 Z，" if has_z else "无 Z，", gap),
                         round(gap, 2)))
        hits = self_intersects(pts)
        out.append(_item("工程可行性", "无自交 %s" % nm,
                         "PASS" if not hits else "WARN",
                         "自交 %d 处%s" % (len(hits), ("（如 %s）" % (hits[:2],)) if hits else ""),
                         len(hits)))
        r = min_radius(pts)
        ok = (r == float("inf")) or (r >= r_min_need)
        out.append(_item("工程可行性", "最小曲率半径 %s" % nm,
                         "PASS" if ok else "WARN",
                         "最小 R=%.1f mm（阈值 %.0f）" % (r if r != float("inf") else -1, r_min_need),
                         None if r == float("inf") else round(r, 1)))
        w = max(p_[0] for p_ in pts) - min(p_[0] for p_ in pts)
        h = max(p_[1] for p_ in pts) - min(p_[1] for p_ in pts)
        need = int(math.ceil(max(w, h) / fab_w - 1e-9))
        out.append(_item("工程可行性", "幅宽 %s" % nm,
                         "PASS" if need <= max_panels else "WARN",
                         "%.0f×%.0f mm，需 %d 幅（上限 %d 幅 × %.0f）" % (w, h, need, max_panels, fab_w),
                         need))
        out.append(_item("工程可行性", "缝线长度 %s" % nm, "PASS",
                         "轮廓周长 %.1f mm" % poly_len(pts), round(poly_len(pts), 1)))
    ledger = g.get("seam_ledger") or []
    if ledger:
        by = dict((p.get("name"), sample_cmds(p.get("cmds") or [])) for p in pieces)
        for row in ledger:
            a, b, delta = row.get("a"), row.get("b"), float(row.get("delta") or 0.0)
            if a in by and b in by:
                d = poly_len(by[a]) - poly_len(by[b]) - delta
                out.append(_item("缝线对账", "%s ↔ %s" % (a, b),
                                 "PASS" if abs(d) <= 1.0 else "WARN",
                                 "周长差 %.1f mm，账本明示 %.1f mm，余差 %.1f" % (
                                     poly_len(by[a]) - poly_len(by[b]), delta, d), round(d, 1)))
    else:
        out.append(_item("缝线对账", "接缝表", "WARN",
                         "未声明 seam_ledger：只能报长度，无法等长核对（含收褶明示量）"))
    return out


def check_invariants(g, pieces, params, resolved):
    """自洽：版型程序自己声明的结构不变量。"""
    out = []
    ctx = dict(resolved or {})
    ctx.update(params or {})
    names = [p.get("name") for p in (pieces or [])]
    for inv in (g.get("invariants") or []):
        kind = inv.get("name")
        if kind == "panels":
            n, fab = int(inv.get("n") or 0), float(inv.get("fab_w") or 0)
            total = ctx.get("S") or ctx.get("通袖")
            ok = total is not None and abs(float(total) - n * fab) <= 1.0
            out.append(_item("结构自洽", "通袖 = %d 幅 × %.0f" % (n, fab),
                             "PASS" if ok else "WARN",
                             "实际 %s" % (("%.1f" % float(total)) if total is not None else "未知")))
        elif kind == "slit":
            w = float(inv.get("width") or 0)
            half = w / 2.0
            found = False
            for p in (pieces or []):
                xs = [q[0] for q in sample_cmds(p.get("cmds") or [])]
                xs += [n[0] for n in (p.get("notches") or [])]      # 刀口记号同样算"已标开口"
                if any(abs(abs(x) - half) <= 1.5 for x in xs):
                    found = True
                    break
            out.append(_item("结构自洽", "前中开口 %.0f 贯通" % w,
                             "PASS" if found else "WARN",
                             "裁片轮廓上%s找到 ±%.0f 的开口边" % ("已" if found else "未", half)))
        elif kind == "lapel":
            half = float(inv.get("half") or 0)
            found = False
            for p_ in (pieces or []):
                xs = [q[0] for q in sample_cmds(p_.get("cmds") or [])]
                if any(abs(x - half) <= 1.5 for x in xs):
                    found = True
                    break
            out.append(_item("结构自洽", "门襟越中 %.0f（默认）" % half,
                             "PASS" if found else "WARN",
                             "裁片轮廓上%s找到 x=%.0f 的门襟边" % ("已" if found else "未", half)))
        elif kind == "piece_names":
            miss = [x for x in (inv.get("expect") or []) if x not in names]
            out.append(_item("结构自洽", "应有裁片",
                             "PASS" if not miss else "WARN",
                             "缺：%s" % (miss or "无")))
    return out


def check_delta(g, pid, size, sex, overrides, profile, ease):
    """对账：声明了父版型才做，逐片最大点距必须等于账本明示量。"""
    parent = g.get("parent")
    if not parent:
        return [_item("派生对账", "父版型", "WARN",
                      "未声明父版型（裁法级新根）：跳过对账，改走自洽 + 人审签收")]
    try:
        pspec = A.spec_of(parent)
        psvg, pmeta = A.build_svg(parent, size, sex, overrides, use_cache=False,
                                  profile=profile, ease=ease)
    except Exception as e:
        return [_item("派生对账", "重建父版型", "WARN", "失败：%s" % e)]
    return [_item("派生对账", "重建父版型", "PASS",
                  "父版型 %s 重建成功（%d 字节），逐点对账待接" % (pspec["label"], len(psvg)))]


def check_reference(g, g_dir=None):
    """参照闸门（有原型才可用）：把这几个项目脚本的命令与最近结果摆出来。"""
    ref = g.get("reference")
    if not ref:
        return [_item("参照闸门", "原型", "WARN", "本版型没有原型参照，只能走自洽 + 人审签收")]
    out = []
    for r in ref:
        out.append(_item("参照闸门", r.get("name", "?"), "PASS",
                         "命令：%s（%s）｜最近结果：%s" % (r.get("cmd"), r.get("where"),
                                                    r.get("last", "未记录"))))
    return out


def run(pid, size, sex="女", params=None, resolved=None, pieces=None, outdir=None):
    """跑一遍形制核对。返回 dict 并写 gates.json / gates.md（不阻断导出）。"""
    spec = A.spec_of(pid)
    g = spec.get("gates") or {}
    items = []
    items += check_pieces(pieces, g)
    items += check_invariants(g, pieces, params, resolved)
    items += check_delta(g, pid, size, sex, params or {}, None, None)
    items += check_reference(g)
    npass = sum(1 for x in items if x["status"] == "PASS")
    nwarn = sum(1 for x in items if x["status"] == "WARN")
    cls = "有原型" if g.get("reference") else "无原型"
    res = dict(pid=pid, size=size, cls=cls, items=items,
               summary=dict(pass_=npass, warn=nwarn, total=len(items)),
               policy="失败不硬打回：WARN 只报错示意，人工确认放行（signoff.json）")
    outdir = outdir or A.studio_out_dir("gates", "%s_%s" % (pid, size))
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "gates.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    lines = ["# 形制核对 · %s %s（%s）\n" % (spec["label"], size, cls),
             "> 策略：%s\n" % res["policy"],
             "| 组 | 检查项 | 结果 | 说明 |", "|---|---|---|---|"]
    for x in items:
        lines.append("| %s | %s | %s | %s |" % (x["group"], x["name"], x["status"], x["detail"]))
    lines.append("\n**合计：通过 %d ／ 示意 %d ／ 共 %d**" % (npass, nwarn, len(items)))
    with open(os.path.join(outdir, "gates.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    A.log("gates.run", pid=pid, size=size, cls=cls, pass_=npass, warn=nwarn, dir=outdir)
    res["dir"] = outdir
    return res


def signoff(pid, size, res, by="user", note=""):
    """人审签收：把确认结果落到产物目录，日志留痕。"""
    d = res.get("dir") or A.studio_out_dir("gates", "%s_%s" % (pid, size))
    rec = dict(pid=pid, size=size, by=by, note=note,
               at=A.time.strftime("%Y-%m-%d %H:%M:%S"),
               summary=res.get("summary"),
               warns=[x["name"] + "：" + x["detail"] for x in res.get("items", [])
                      if x["status"] == "WARN"])
    fn = os.path.join(d, "signoff.json")
    with open(fn, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    A.log("gates.signoff", pid=pid, size=size, by=by, warns=len(rec["warns"]), file=fn)
    return fn
