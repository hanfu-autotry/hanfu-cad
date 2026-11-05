# -*- coding: utf-8 -*-
"""
尺码工具 · 对穿交（男女同款）
一键把号型（或身高/净胸围）换成 build.py 的全套尺寸参数。

── 依据（信息源） ────────────────────────────────────────────────
1. GB/T 1335.1-2008 男子 / GB/T 1335.2-2008 女子《服装号型》
   · 号 = 身高，型 = 净胸围；身高 5cm 分档、胸围 4cm 分档
   · 女子中间体 160/84A，男子中间体 170/88A；A 型 = 胸腰差 14–18cm（女）
2. 汉服平裁放量（汉服制作资料，多源一致）
   · 女上装松量：4–6cm 紧身 / 8–10cm 合体 / ≥14cm 宽松
   · **男上装松量：20–22cm 为合身**（同款男装要比女装多放 ~11cm）
   · 袖根 =(净胸围+放量)/4；窄袖口 ≈(净胸围+放量)/6；领边宽 女 6–8cm
   · 衣长 ≈ 背长 + 5~14cm（短襦）

── 基准 ─────────────────────────────────────────────────────────
女 M（160/84A 合体）= 已过审的 v6 半臂：
  衣长 825 / 摆宽 1150 / 腋深 313 / 袖长 265 / 袖口 195 / 领宽 190 / 交叠 270
男女同款 → 同一套板型，靠"围度放量差"与"身高/胸围档差"分性别推档。

── 口径说明 ─────────────────────────────────────────────────────
围度类（摆宽、腋点、袖口）受两级影响：
  ① 号型档差：净胸围每 +1cm → 摆宽 +5mm（胸围档 4cm → 20mm，贴国标）
  ② 性别放量差：男装比女装多约 110mm（20–22cm vs 8–10cm 松量）
长度类（衣长、袖长、腋深）只随身高/胸围走，不受放量档影响。
"""
# ══ 最高置信度基准：厂商实物出货尺码表 —— **男装**（见 sources/vendor_尺码表/） ══
# 女装同一板型建议取小一档（厂商表未给女装数据，不做外推）
# 长袖短衫实测（cm）：小 73/53/154/15/7 ｜ 中 77/57/163/16/7 ｜ 大 81/61/172/17/7
# 列序：衣长 / 平铺胸宽(1/2胸围) / 通袖 / 袖口宽 / 领宽
VENDOR = {
    "XS":  (710, 490, 140),
    "S":   (730, 530, 150),   # 小码
    "M":   (770, 570, 160),   # 中码
    "L":   (810, 610, 170),   # 大码
    "XL":  (850, 650, 180),   # 按厂商档差外推（衣长+40 / 胸宽+40 / 袖口+10）
    "2XL": (890, 690, 190),
}
VENDOR_NOTE = "厂商实物表（最高置信度）；小/中/大 为实测，XS/XL/2XL 按同档差外推"
COL_W = 70.0          # 领缘宽（厂商实测 7cm）

BASE_H, BASE_B = 160.0, 84.0     # 女中间体（板型锚点）

BASE = dict(L=825.0, W_HEM=1150.0, Y_ARM=512.0, SLEEVE_LEN=265.0,
            CUFF=195.0, NECK=190.0, OV=270.0, HEM_RISE=60.0,
            X_ARM=411.24, X_SHLD=560.0)

GRADE = dict(
    L_per_h=4.0,        # 衣长：身高 +1cm → +4mm（国标身高档 5cm → 20mm）
    W_per_b=5.0,        # 摆宽：净胸围 +1cm → +5mm（胸围档 4cm → 20mm）
    Y_per_b=1.25,       # 腋深：胸围档 4cm → 5mm
    S_per_b=1.25,       # 袖长
    C_per_b=1.25,       # 袖口
    N_per_b=1.5,        # 领宽：胸围档 4cm → 6mm
    X_per_b=1.785,      # 腋点半宽（≈摆宽的 0.357）
    OV_per_b=1.25,
    SH_per_b=0.9,       # 肩点
)

# 性别：放量差额（mm，加到围度上）与号型序列
SEX = {
    "女": dict(extra_ease=0.0,
               sizes=[("XS", 150, 76), ("S", 155, 80), ("M", 160, 84),
                      ("L", 165, 88), ("XL", 170, 92), ("2XL", 175, 96)]),
    "男": dict(extra_ease=110.0,   # 男装松量 20–22cm 比女装 8–10cm 多约 11cm
               sizes=[("S", 165, 84), ("M", 170, 88), ("L", 175, 92),
                      ("XL", 180, 96), ("2XL", 185, 100)]),
}

# 放量档：对围度类尺寸的系数（基准 = 合体）
EASE = {"紧身": 0.94, "合体": 1.00, "宽松": 1.08}


def resolve(sex="女", size=None, height=None, bust=None):
    sex = sex if sex in SEX else "女"
    if size:
        key = str(size).upper().replace(" ", "")
        for code, h, b in SEX[sex]["sizes"]:
            if code == key:
                return float(h), float(b)
        if "/" in key:                         # 形如 170/88A
            h, b = key.split("/")[0], key.split("/")[1].rstrip("ABCYabcy ")
            return float(h), float(b)
        raise ValueError("未知号型：%s（%s装可用：%s）" % (
            size, sex, "、".join(c for c, _, _ in SEX[sex]["sizes"])))
    if height and bust:
        return float(height), float(bust)
    raise ValueError("需要 size，或 height+bust")


"""profile:
  vendor   = 厂商实物表（默认，最高置信度）
  artifact = 文物复原版（衣长 825 / 平铺胸宽 822 / 领缘 40），即已过审的 v6 基版
"""
PROFILES = ("vendor", "artifact")


def params(sex="女", size=None, height=None, bust=None, ease="合体", profile="vendor"):
    if profile == "vendor":
        return _vendor_params(sex, size, ease)
    return _artifact_params(sex, size, height, bust, ease)


def _vendor_params(sex="女", size="M", ease="合体"):
    key = str(size or "M").upper().replace(" ", "")
    alias = {"小": "S", "小码": "S", "中": "M", "中码": "M", "大": "L", "大码": "L"}
    key = alias.get(str(size), key)
    if key not in VENDOR:
        key = "M"
    L, w, cuff = VENDOR[key]
    k = EASE.get(ease, 1.00)
    x_arm = w / 2.0 * k                    # 平铺胸宽的一半 = 腋点/肩点
    return {
        "L": float(L), "W_HEM": round(2 * x_arm * 1.40, 1), "EASE": 1.0,
        "X_ARM": round(x_arm, 1), "Y_ARM": round(L * 0.64, 1), "X_SHLD": round(x_arm, 1),
        "SLEEVE_LEN": 265.0, "CUFF": float(cuff), "NECK": 190.0,
        "OV": 270.0, "HEM_RISE": 60.0, "TILT_DEG": 0.8, "COL_W": COL_W,
    }


def _artifact_params(sex="女", size=None, height=None, bust=None, ease="合体"):
    """返回 build.py 可用的参数字典（mm）"""
    sex = sex if sex in SEX else "女"
    h, b = resolve(sex, size, height, bust)
    k = EASE.get(ease, 1.00)
    ex = SEX[sex]["extra_ease"]
    dh, db = h - BASE_H, b - BASE_B

    W = BASE["W_HEM"] + dh * 0 + db * GRADE["W_per_b"] + ex
    X = BASE["X_ARM"] + db * GRADE["X_per_b"] + ex * 0.357
    C = BASE["CUFF"] + db * GRADE["C_per_b"] + ex * 0.0
    OV = BASE["OV"] + db * GRADE["OV_per_b"] + ex * 0.12

    p = {
        "COL_W": 40.0,
        "L": round(BASE["L"] + dh * GRADE["L_per_h"], 1),
        "W_HEM": round(W * k, 1),
        "EASE": 1.0,
        "X_ARM": round(X * k, 1),
        "Y_ARM": round(BASE["Y_ARM"] + db * GRADE["Y_per_b"] + ex * 0.25, 1),
        "X_SHLD": round(BASE["X_SHLD"] + db * GRADE["SH_per_b"], 1),
        "SLEEVE_LEN": round(BASE["SLEEVE_LEN"] + db * GRADE["S_per_b"], 1),
        "CUFF": round(C, 1),
        "NECK": round(BASE["NECK"] + db * GRADE["N_per_b"], 1),
        "OV": round(OV * k, 1),
        "HEM_RISE": BASE["HEM_RISE"],
        "TILT_DEG": 0.8,
    }
    return p


def summary(p):
    half = p["W_HEM"] / 2 * p["EASE"]
    return ("衣长 %.0f ｜ 摆宽 %.0f ｜ 单边 %.0f ｜ 交叠 %.0f ｜ 腋深 %.0f ｜ "
            "袖长 %.0f ｜ 袖口 %.0f ｜ 领宽 %.0f ｜ 通袖 %.0f"
            % (p["L"], p["W_HEM"], half + p["OV"] / 2, p["OV"],
               p["L"] - p["Y_ARM"], p["SLEEVE_LEN"], p["CUFF"], p["NECK"],
               2 * (p["X_SHLD"] + p["SLEEVE_LEN"])))


if __name__ == "__main__":
    for sex in ("女", "男"):
        print("【%s装】" % sex)
        for code, h, b in SEX[sex]["sizes"]:
            print("  %-4s %-9s %s" % (code, "%d/%dA" % (h, b), summary(params(sex=sex, size=code))))
