# -*- coding: utf-8 -*-
"""古制 · 领条算法（V1 / V2 / V3 共用，2026-11-18 统一到一处）

口径（与默认裁法的 `hanfu-zhidui` 完全一致）：

    开领  ＝ 连接**颈侧点** P(±x_cut, y_top) 与**下摆中点** Q(0, 0) 的弦（V 形，贯通到摆）
    领条  ＝ 与襟缘（弦）**平行的等宽带**，宽 ＝ collar_w
    颈口  ＝ 在肩线处转折为「前片两三角 ＋ 后片梯形」；顶半宽由 miter 闭式解出
    立起高 ≡ collar_w（带宽立起来）
    领条长 ＝ 2·|PQ| ＋ 开领宽(2·x_cut)

符号：
    x_cut  颈侧点到中缝的距离（＝开领宽 / 2）
    y_top  颈侧点的高度（＝肩线 / 对折线到摆的距离，也就是前襟的水平投影）
    n      |PQ| ＝ √(x_cut² + y_top²)
    n̂      指向领口内侧的单位法向 ＝ (−y_top, x_cut)/n
    k      顶半宽随带宽的衰减系数：顶半宽 ＝ x_cut − k·collar_w

    M ＝ (P + collar_w·n̂) 沿 û 走到 y ＝ y_top + collar_w：
        M.x ＝ x_cut − k·collar_w,
        k ＝ y_top/n − (1 − x_cut/n)·(x_cut/y_top)
"""
import math


def geom(x_cut, y_top, collar_w):
    """返回领条的全部派生量（dict）。x_cut、y_top、collar_w 单位 mm。"""
    x_cut = float(x_cut)
    y_top = float(y_top)
    collar_w = float(collar_w)
    n = math.hypot(x_cut, y_top)
    k = y_top / n - (1.0 - x_cut / n) * (x_cut / y_top)
    top_half = x_cut - k * collar_w
    if top_half <= 0.0:
        raise ValueError("领条宽 %.1f 过大：后领带顶边会反折（上限 %.2f）"
                         % (collar_w, x_cut / k))
    return dict(
        x_cut=x_cut,
        y_top=y_top,
        w=collar_w,
        neck_w=2.0 * x_cut,          # 开领宽
        edge=n,                      # 襟缘长 |PQ|
        nx=-y_top / n,               # 指向领口内侧的法向（右襟；左襟取负）
        ny=x_cut / n,
        k=k,
        top_half=top_half,           # 后领带顶半宽（M.x）
        top_w=2.0 * top_half,
        length=2.0 * n + 2.0 * x_cut,  # 领条长
        stand=collar_w,              # 立起高 ≡ 带宽
        seen=2.0 * x_cut - 2.0 * collar_w,   # 颈口中间露出后片的宽
    )


def limit(x_cut, y_top):
    """带宽上限：顶半宽 > 0 ⇒ collar_w < x_cut / k。"""
    x_cut = float(x_cut)
    y_top = float(y_top)
    n = math.hypot(x_cut, y_top)
    k = y_top / n - (1.0 - x_cut / n) * (x_cut / y_top)
    return x_cut / k
