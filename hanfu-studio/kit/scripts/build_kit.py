# -*- coding: utf-8 -*-
"""生成 harness 素材包（hanfu-studio/kit）里"能自动派生"的那部分。

只读各项目、只写 kit：
  01-版型清单.md / patterns/<pid>.json / gates/<pid>.md / projects/<proj>/INDEX.md
  sources/（按「参考对象 → 类型」两级分门别类，每份留出处）/ sources-索引.md
手写的那几份（README / 02 许愿 / 03 逆向 / 04 口径 / 05 接口）不在这里生成，避免被覆盖。

素材库的**对象清单**可编辑：`kit/sources/subjects.json`。
新建了版型时本脚本会自动补一个对象目录（"新建的归新建"）；
你只要给该对象加匹配规则，或把图投到 `sources/intake/`。

用法：python kit/scripts/build_kit.py
"""
import csv
import json
import os
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # hanfu-studio/kit
STUDIO = os.path.dirname(KIT)                                          # hanfu-studio
PATTERNS = os.path.join(STUDIO, "patterns.json")

DEFAULT_SUBJECTS = [
    dict(id="01-无锡钱樟夫妇墓_对穿交",
         note="默认根：半臂(banbi) 与 接袖(jiexiu) 的官图、放码依据、他人打版记录",
         feeds=["banbi", "jiexiu"],
         rules=["silk/raw", "vendor", "尺码", "weibo"]),
    dict(id="02-深衣_古制",
         note="古制：深衣 V2 宽袖 / V3 窄袖 的剪裁图与平铺图",
         feeds=["shenyi"],
         rules=["fig_深衣", "fig_窄袖深衣"]),
    dict(id="03-原始直领交襟衣_古制",
         note="古制：原始直领交襟衣 V1 的三步图",
         feeds=["zhiling"],
         rules=["fig_原始直领交襟衣"]),
    dict(id="04-直交一体_术语证据",
         note="跨版型的术语口径证据：交叠量 → 直领 / v / y / x 四形态",
         feeds=["banbi", "jiexiu", "shenyi", "zhiling"],
         rules=["直交一体", "谱系"]),
]

TYPE_NOTE = {
    "官图": ("YES", "形制线稿、带尺寸链；量通袖/衣长/摆宽/交叠/袖口/腋深，做叠合配准"),
    "号型放码": ("YES", "厂商号型表；vendor 档放码基准（不是文物，别把文物价挪用）"),
    "打版草稿": ("NO", "他人打版过程/手绘；只作方法参考，作者自注数据不可当锚定"),
    "剪裁与平铺": ("PARTIAL", "剪裁图/平铺图；量幅数与幅宽、前中开口、领条、腰线"),
    "三步图": ("PARTIAL", "材料→对折→剪开→压边→平铺 的顺序图；量开口贯通与领条走向"),
    "证据": ("NO", "支撑口径判断（不是量尺寸用）；引用时写明是哪条口径的证据"),
    "待考": ("NO", "来源未核实；用前先核，不得用于交付"),
}
TYPE_OF = [("silk/raw", "官图"), ("官图", "官图"), ("vendor", "号型放码"),
           ("尺码", "号型放码"), ("weibo", "打版草稿"), ("草稿", "打版草稿"),
           ("剪裁", "剪裁与平铺"), ("平铺", "剪裁与平铺"), ("三步", "三步图"),
           ("拼缝", "剪裁与平铺"), ("上身形态", "证据"),
           ("直交一体", "证据"), ("谱系", "证据"), ("形态", "证据")]
PENDING = "99-来历待考"



def rel_ws(path, ws):
    """把仓内绝对路径写成相对路径（kit 里不写本机绝对路径）。"""
    try:
        return os.path.relpath(path, ws).replace("\\", "/")
    except Exception:
        return path.replace("\\", "/")


def load():
    d = json.load(open(PATTERNS, encoding="utf-8"))
    ws = d.get("workspace") or ".."
    if not os.path.isabs(ws):                       # 相对：相对 studio 目录（patterns.json 所在处）
        ws = os.path.abspath(os.path.join(STUDIO, ws))
    return d, ws


def ensure(*parts):
    p = os.path.join(KIT, *parts)
    os.makedirs(p, exist_ok=True)
    return p


def _sha1(path, n=12):
    import hashlib
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:n]


def load_subjects(pats):
    """对象清单（`kit/subjects.json`，可编辑）；新注册的版型自动补一个对象。
    注意：清单放在 kit/ 根下、**不在 sources/ 里**——否则重建 sources 时会把它连同 intake 一起冲掉。"""
    fp = os.path.join(KIT, "subjects.json")
    if os.path.isfile(fp):
        subj = json.load(open(fp, encoding="utf-8"))
    else:
        subj = [dict(x) for x in DEFAULT_SUBJECTS]
    covered = set()
    for x in subj:
        covered.update(x.get("feeds") or [])
    added = []
    for p in pats:
        if p["id"] in covered:
            continue
        n = len([x for x in subj if str(x["id"])[:2].isdigit()]) + 1
        sid = "%02d-%s_%s" % (n, p["label"], p["cut"])
        subj.append(dict(id=sid, feeds=[p["id"]], rules=[],
                         note="新建版型 %s（%s）的素材：补 rules 或把图投到 intake/" % (p["label"], p["id"])))
        added.append(sid)
    json.dump(subj, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return subj, added


def classify(subjects, rel):
    r = rel.replace("\\", "/")
    low = r.lower()
    for s in subjects:
        for key in (s.get("rules") or []):
            if key.lower() in low or key in r:
                typ = next((t for k, t in TYPE_OF if k.lower() in low or k in r), "待考")
                return s["id"], typ
    typ = next((t for k, t in TYPE_OF if k.lower() in low or k in r), "待考")
    return PENDING, typ


def sync_sources(ws, pats, subjects):
    import shutil
    root = ensure("sources")
    for s in subjects:
        os.makedirs(os.path.join(root, s["id"]), exist_ok=True)
    os.makedirs(os.path.join(root, PENDING), exist_ok=True)
    os.makedirs(os.path.join(root, "intake"), exist_ok=True)
    rows = [("subject", "type", "file", "project", "origin_path", "note", "anchor_ok", "kb", "sha1")]
    tree = {}
    total = 0
    for proj in sorted(set(p["project"] for p in pats)):
        src = os.path.join(ws, proj, "sources")
        if not os.path.isdir(src):
            continue
        for dirpath, _dirs, files in os.walk(src):
            for f in sorted(files):
                sp = os.path.join(dirpath, f)
                rel = os.path.relpath(sp, src)
                ext = os.path.splitext(f)[1].lower()
                if ext not in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".pdf"):
                    d = ensure("sources", "_来源清单", proj)
                    dp = os.path.join(d, f)
                    if (not os.path.exists(dp) or os.path.getsize(dp) != os.path.getsize(sp)
                            or os.path.getmtime(dp) < os.path.getmtime(sp)):
                        shutil.copy2(sp, dp)
                    total += 1
                    rows.append(("_来源清单", "清单/说明", f, proj, rel_ws(sp, ws),
                                 "项目自带的来源清单与说明（不是素材本体）", "META",
                                 "%.0f" % (os.path.getsize(sp) / 1024.0), _sha1(sp)))
                    continue
                sid, typ = classify(subjects, rel)
                d = ensure("sources", sid, typ)
                dp = os.path.join(d, f)
                if (not os.path.exists(dp) or os.path.getsize(dp) != os.path.getsize(sp)
                        or os.path.getmtime(dp) < os.path.getmtime(sp)):
                    shutil.copy2(sp, dp)
                total += 1
                anchor, note = TYPE_NOTE.get(typ, ("NO", ""))
                tree.setdefault(sid, {}).setdefault(typ, []).append(
                    (f, proj, rel.replace("\\", "/"), anchor))
                rows.append((sid, typ, f, proj, rel_ws(sp, ws), note, anchor,
                             "%.0f" % (os.path.getsize(sp) / 1024.0), _sha1(sp)))

    for s in subjects:
        sid = s["id"]
        d = os.path.join(root, sid)
        L = ["# %s" % sid, "",
             "- 这个参考是什么：%s" % s.get("note", ""),
             "- 喂给哪些版型：%s" % ("、".join("`%s`" % x for x in (s.get("feeds") or []) or ["—"])),
             "- 归到本对象的匹配规则：%s" % ("、".join(s.get("rules") or []) or "（无——投 intake/ 或补 rules）"),
             ""]
        if not tree.get(sid):
            L.append("（暂无素材）")
        for typ in sorted(tree.get(sid, {})):
            items = tree[sid][typ]
            anchor, note = TYPE_NOTE.get(typ, ("NO", ""))
            L += ["## %s（%d 个）" % (typ, len(items)), "",
                  "- 能否当锚定：**%s** ｜ 用法：%s" % (anchor, note), "",
                  "| 文件 | 来自 | 原始路径 |", "|---|---|---|"]
            for f, proj, rel, _a in items:
                L.append("| `%s/%s` | %s | `%s/sources/%s` |" % (typ, f, proj, proj, rel))
            L.append("")
        L.append("> 出处与 sha1：`../MANIFEST.csv`；投放新素材：`../intake/README.md`")
        open(os.path.join(d, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L))

    alive = set(p["id"] for p in pats)
    L = ["# 素材库（按参考对象分门别类 · harness 看图与放素材的地方）", "",
         "> 两级结构：**`<对象>/<类型>/`**。对象＝这是哪件衣/哪座墓的参考；类型＝官图/剪裁与平铺/号型放码/…",
         "> 每份素材都留出处（项目 + 原始路径 + sha1），并标注能不能当锚定。全量清单：`MANIFEST.csv`。", "",
         "| 对象 | 是什么 | 喂给 | 类型与数量 |", "|---|---|---|---|"]
    for s in subjects:
        sid = s["id"]
        parts = ["%s(%d)" % (t, len(v)) for t, v in sorted(tree.get(sid, {}).items())]
        dead = bool(s.get("feeds")) and not any(f in alive for f in s["feeds"])
        tag = " ｜ **版型已注销**（空对象，可手工删）" if (dead and not parts) else ""
        L.append("| `%s/` | %s | %s | %s%s |"
                 % (sid, s.get("note", ""), "、".join(s.get("feeds") or []) or "—",
                    "、".join(parts) or "暂无", tag))
    pend = len([f for f in os.listdir(os.path.join(root, PENDING))
                if not f.endswith(".md")]) if os.path.isdir(os.path.join(root, PENDING)) else 0
    L.append("| `%s/` | 来源未核实（不得用于交付） | — | %d |" % (PENDING, pend))
    L += ["| `_来源清单/` | 项目自带的 csv/md/html | — | 查出处用，不当素材 |",
          "| `intake/` | **harness 投放口** | — | 新素材放这里并登记一行 |", "",
          "## 规矩（四条）", "",
          "1. **先归对象**：这张图是哪件衣/哪座墓的参考？新建的版型就新建一个对象（`subjects.json` 加一条）。",
          "2. **再归类型**：官图 / 剪裁与平铺 / 三步图 / 号型放码 / 打版草稿 / 证据。",
          "3. **必须登记**：`MANIFEST.csv` 加一行；能直接量锚定的写 `YES`，只能定性的写 `NO`。",
          "4. **不覆盖**：同名加 `_v2` 并列；重跑 `build_kit.py` 只重建 INDEX，**不清空 intake/**。"]
    open(os.path.join(root, "README.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    intake = "\n".join([
        "# intake · harness 投放口", "",
        "新素材放这里；确认对象后挪进 `<对象>/<类型>/`。", "",
        "必须同时登记一行（否则不算「有根据的素材」）：", "",
        "```",
        "subject,type,file,project,origin_path,note,anchor_ok,kb,sha1",
        "02-深衣_古制,剪裁与平铺,新图.jpg,<项目>,<来源URL或路径>,量幅数与开口,PARTIAL,120,<sha1>",
        "```", "",
        "规则：",
        "1. 先想「这是哪件衣/哪座墓的参考」，再想类型；分不清对象就放 `99-来历待考/`。",
        "2. 说清「能用它量什么」；只能定性写 `anchor_ok=NO`。",
        "3. 不覆盖同名旧素材（同名加 `_v2`）。",
        "4. 重跑 `build_kit.py` 只重建 INDEX，不清空 intake/。",
    ]) + "\n"
    open(os.path.join(root, "intake", "README.md"), "w", encoding="utf-8").write(intake)

    with open(os.path.join(root, "MANIFEST.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(rows)
    return total, tree


def side_scripts(ws, proj):
    out = {"pattern": [], "verification": []}
    for k in out:
        d = os.path.join(ws, proj, k)
        if os.path.isdir(d):
            out[k] = sorted(f for f in os.listdir(d) if f.endswith(".py"))
    return out


def docs_of(ws, proj):
    d = os.path.join(ws, proj)
    out = []
    for dirpath, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in ("out", "__pycache__", ".git", "sources")]
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.relpath(os.path.join(dirpath, f), d).replace("\\", "/"))
    return sorted(out)[:20]


def newest_gates_json(ws, pid):
    root = os.path.join(ws, "hanfu-studio", "out")
    cands = []
    for dirpath, _dirs, files in os.walk(root):
        if "gates.json" in files and pid in dirpath:
            cands.append(os.path.join(dirpath, "gates.json"))
    return max(cands, key=os.path.getmtime) if cands else None


def main():
    d, ws = load()
    pats = d["patterns"]
    subjects, added = load_subjects(pats)

    lines = ["# 01 版型清单（自动生成 · 勿手改）", "",
             "> 由 `kit/scripts/build_kit.py` 从 `hanfu-studio/patterns.json` 派生。",
             "> 只登记「已有的版型程序」，**不含任何源码/几何**。生成时间：%s"
             % time.strftime("%Y-%m-%d %H:%M"), "",
             "| id | 名称 | 裁法 | 项目 | 脚本 | 接口 | 可复用模式 | 产物 |",
             "|---|---|---|---|---|---|---|---|"]
    for p in pats:
        run = p.get("run") or {}
        kind = run.get("kind")
        iface = run.get("argstyle") or ("fixtures：" + ",".join((run.get("fixtures") or {}).keys())
                                        if kind == "params" else "号型表")
        modes = "、".join("%s(%s)" % (m["label"], m["id"]) for m in (p.get("modes") or [])) or "—"
        extras = "、".join(e["id"] for e in (p.get("extras") or [])) or "—"
        lines.append("| `%s` | %s | %s | %s | `%s` | %s | %s | %s |"
                     % (p["id"], p["label"], p["cut"], p["project"], p["script"], iface, modes, extras))
    lines += ["", "## 每个版型的可跑命令（在对应项目目录下执行）", ""]
    for p in pats:
        run = p.get("run") or {}
        lines += ["### %s（`%s`）" % (p["label"], p["id"]), "",
                  "- 项目：`%s`（相对仓根）" % rel_ws(os.path.join(ws, p["project"]), ws),
                  "- 主脚本：`%s`" % p["script"]]
        if run.get("kind") == "make":
            for sex, sizes in (p.get("sizes") or {}).items():
                lines.append("- 号型（%s）：%s" % (sex, "、".join(sizes)))
            lines.append("- 出图：`python %s %s`"
                         % (p["script"], (run.get("argstyle") or "").format(
                             sex="女", size="M", out="out/x", profile="artifact", ease="合体")))
        else:
            for mid, fx in (run.get("fixtures") or {}).items():
                lines.append("- 模式 `%s`：`HANFU_PARAMS='%s' python %s`"
                             % (mid, json.dumps(fx, ensure_ascii=False), p["script"]))
        for e in (p.get("extras") or []):
            lines.append("- 产物 `%s`：`python %s`" % (e["id"], e["script"]))
        lines.append("")
    open(os.path.join(KIT, "01-版型清单.md"), "w", encoding="utf-8").write("\n".join(lines))

    pdir = ensure("patterns")
    for p in pats:
        proj_dir = os.path.join(ws, p["project"])
        rec = dict(id=p["id"], label=p["label"], cut=p["cut"], project=p["project"],
                   project_dir=rel_ws(proj_dir, ws), script=p["script"],
                   script_exists=os.path.isfile(os.path.join(proj_dir, p["script"])),
                   run=p.get("run") or {}, modes=p.get("modes") or [],
                   mode_kind=p.get("mode_kind"), ease=p.get("ease"), knobs=p.get("knobs") or [],
                   extras=[e["id"] for e in (p.get("extras") or [])],
                   gates=p.get("gates") or {},
                   scripts=side_scripts(ws, p["project"]), docs=docs_of(ws, p["project"]),
                   subject=next((s["id"] for s in subjects if p["id"] in (s.get("feeds") or [])), None))
        json.dump(rec, open(os.path.join(pdir, "%s.json" % p["id"]), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    gdir = ensure("gates")
    for p in pats:
        g = p.get("gates") or {}
        L = ["# 闸门 · %s（`%s`）" % (p["label"], p["id"]), "", "## 分类", ""]
        if g.get("reference"):
            L.append("**有原型**：先跑参照闸门，再跑自洽/对账。")
            for r in g["reference"]:
                L.append("- %s：`%s`（在 `%s`）｜最近结果：%s"
                         % (r.get("name"), r.get("cmd"), r.get("where"), r.get("last")))
        else:
            L.append("**无原型**：走 自洽（结构不变量）+ 对账（父版型）+ 人审签收。")
        sizes = list((p.get("sizes") or {"—": ["?"]}).values())[0]
        L += ["", "## 跑什么", "", "```bash",
              "cd hanfu-studio",
              "python - <<'PY'", "import adapters as A",
              "r = A.generate_all('%s', '%s')" % (p["id"], sizes[-1]),
              "print(r['gates']['summary'])", "PY", "```"]
        latest = newest_gates_json(ws, p["id"])
        if latest:
            try:
                res = json.load(open(latest, encoding="utf-8"))
                sm = res.get("summary") or {}
                L += ["", "## 最近一次实测（%s）"
                      % time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(latest))), "",
                      "通过 %s ／ 示意 %s ／ 共 %s" % (sm.get("pass_"), sm.get("warn"), sm.get("total")), "",
                      "| 组 | 检查项 | 结果 | 说明 |", "|---|---|---|---|"]
                for x in res.get("items", []):
                    L.append("| %s | %s | %s | %s |" % (x["group"], x["name"], x["status"], x["detail"]))
                L += ["", "> 原始：`%s`" % latest.replace(ws, "<ws>").replace("\\", "/")]
            except Exception as e:
                L += ["", "（读最近结果失败：%s）" % e]
        else:
            L += ["", "（还没有实测记录：先在 studio 里跑一次「一键生成」）"]
        L += ["", "> 口径：**失败不硬打回**——WARN 只报错示意，人工确认后写 `signoff.json`。"]
        open(os.path.join(gdir, "%s.md" % p["id"]), "w", encoding="utf-8").write("\n".join(L))

    for proj in sorted(set(p["project"] for p in pats)):
        pd = ensure("projects", proj)
        mine = [p for p in pats if p["project"] == proj]
        sc = side_scripts(ws, proj)
        L = ["# %s（素材索引 · 不复制源码）" % proj, "",
             "- 目录：`%s`（相对仓根）" % rel_ws(os.path.join(ws, proj), ws),
             "- 本包内登记的版型：%s" % "、".join("`%s`" % p["id"] for p in mine),
             "", "## 能跑的脚本（只列名字）", "", "| 用途 | 脚本 |", "|---|---|"]
        for f in sc["pattern"]:
            L.append("| 版型/出图 | `%s/pattern/%s` |" % (proj, f))
        for f in sc["verification"]:
            L.append("| 闸门 | `%s/verification/%s` |" % (proj, f))
        docs = docs_of(ws, proj)
        if docs:
            L += ["", "## 项目自带文档", ""] + ["- `%s/%s`" % (proj, x) for x in docs]
        open(os.path.join(pd, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L))

    sd = ensure("projects", "hanfu-studio")
    tools = [("界面/父程序", "studio.py"), ("矢量预览（SVG→Canvas）", "svgview.py"),
             ("适配层（唯一接口）", "adapters.py"), ("形制核对闸门", "gates.py"),
             ("CAD 协同 DXF 读写", "dxf_io.py"), ("排料 DXF", "layout_dxf.py"),
             ("全链路自检", "selftest.py"), ("按窗口截图（自检用）", "shot.py"),
             ("打包", "build_exe.py"), ("素材包生成", "kit/scripts/build_kit.py")]
    L = ["# hanfu-studio（父程序 · 壳里没有几何）", "",
         "- 目录：`%s`（相对仓根）" % rel_ws(STUDIO, ws),
         "- 出图/导出**一律调各项目自己的脚本**；壳只认「脚本 + 参数 + 产物」。", "",
         "## 工具", "", "| 用途 | 文件 |", "|---|---|"]
    for k, f in tools:
        L.append("| %s | `%s` |" % (k, f))
    L += ["", "## 命令行自检（打包版）", "", "```bash",
          "hanfu-studio.exe --check-library            # 共享库",
          "hanfu-studio.exe --check-projects           # 项目管理",
          "hanfu-studio.exe --check-cad <样例.dxf>     # CAD 协同", "```",
          "", "## 日志", "",
          "- `logs/studio-YYYY-MM-DD.log`（打包后 `%LOCALAPPDATA%/hanfu-studio/logs`）",
          "- 出图/产物/导出/异常各一行；脚本失败连 stderr 全文。**排查先读它。**"]
    open(os.path.join(sd, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L))

    n_src, tree = sync_sources(ws, pats, subjects)
    L = ["# 参考素材索引（按参考对象分）", "",
         "> 素材本体：`kit/sources/<对象>/<类型>/`；每份留出处，全量见 `kit/sources/MANIFEST.csv`。",
         "> 量法与标定见 `03-逆向手册.md`；口径见 `04-口径清单.md`；投放规矩见 `kit/sources/intake/README.md`。", ""]
    for s in subjects:
        sid = s["id"]
        parts = ["%s %d 个" % (t, len(v)) for t, v in sorted(tree.get(sid, {}).items())]
        L += ["## %s" % sid, "",
              "- %s" % s.get("note", ""),
              "- 喂给：%s" % ("、".join(s.get("feeds") or []) or "—"),
              "- 类型：%s" % ("；".join(parts) or "暂无")]
        if sid in added:
            L.append("- **新建：请补规则或往 intake/ 投放素材**")
        L.append("")
    open(os.path.join(KIT, "sources-索引.md"), "w", encoding="utf-8").write("\n".join(L))

    ensure("out")
    print(json.dumps({"kit": KIT, "patterns": len(pats), "sources": n_src,
                      "subjects": [s["id"] for s in subjects], "new_subjects": added},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
