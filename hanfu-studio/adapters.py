# -*- coding: utf-8 -*-
"""适配层：把三个项目里**已有的**脚本当成外部程序调用。

这里没有几何。只有：
  build_svg(pid, size, sex, overrides) → 调 build/make 脚本，拿回 SVG
  svg_to_png(svg, png)                 → 调 Edge 无头截图（和项目自己的 preview.py 同一路子）

分工的理由：分裁（半臂/接袖）与通裁（深衣/直领交襟）**底层逻辑不同**，
各自留在各自项目里；框架只认"脚本 + 参数 + 产物"这三样。
"""
import copy
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = {}

# ── 运行日志（软件自己的日志；排查问题先读它）────────────────────────
# 每次运行一行：时间 事件 k=v k=v …；UI 在线程里跑，故加锁。
# 位置：HANFU_STUDIO_LOG_DIR → 打包后 %LOCALAPPDATA%\hanfu-studio\logs → 源码目录 logs/
_LOG_LOCK = threading.Lock()


def log_dir():
    d = os.environ.get("HANFU_STUDIO_LOG_DIR")
    if not d:
        if getattr(sys, "frozen", False):
            d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                             "hanfu-studio", "logs")
        else:
            d = os.path.join(HERE, "logs")
    os.makedirs(d, exist_ok=True)
    return d


def log_path():
    return os.path.join(log_dir(), time.strftime("studio-%Y-%m-%d.log"))


# ── 子进程不要在打包版里闪黑窗 ────────────────────────────────────
#   windowed（PyInstaller --windowed）的父进程没有控制台；一 spawn python.exe（控制台程序）
#   Windows 就给它新建一个控制台窗口 → 每步出图闪一个黑窗（用户 2026-11-05 报的现象）。
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0        # CREATE_NO_WINDOW


def _hidden_kwargs(kw):
    """给 subprocess 补上"不显示窗口"的参数（Windows）。"""
    if os.name != "nt":
        return kw
    kw.setdefault("creationflags", _NO_WINDOW)
    si = kw.get("startupinfo") or subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0                                   # SW_HIDE
    kw["startupinfo"] = si
    return kw


def _run(args, **kw):
    """subprocess.run 的封装：Windows 下不弹控制台窗口。"""
    return subprocess.run(args, **_hidden_kwargs(kw))


def _popen(args, **kw):
    return subprocess.Popen(args, **_hidden_kwargs(kw))


def log(event, **fields):
    """写一行运行日志。fields 里的值会原样转成字符串。"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    parts = ["%s %-16s" % (ts, event)]
    for k, v in fields.items():
        if isinstance(v, float):
            v = round(v, 3)
        parts.append("%s=%s" % (k, str(v).replace("\n", " | ")[:400]))
    line = " ".join(parts)
    with _LOG_LOCK:
        try:
            with open(log_path(), "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            pass
    return line


def log_exc(event, exc, **fields):
    tb = traceback.format_exc().replace("\n", " | ")
    return log(event, err="%s: %s" % (type(exc).__name__, exc), tb=tb, **fields)

# 出图要跑各项目自己的脚本：这些脚本需要 stdlib（+ make.py 出 DXF 时需 ezdxf）。
# 打包成 exe 后 sys.executable 指向 exe 本身，不能用它当解释器。
def _pkg_dir():
    """程序所在目录：打包后在 exe 旁边，源码运行时在 hanfu-studio/。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return HERE


_PY_CANDIDATES = [
    os.environ.get("HANFU_PY"),
    # 随包运行时（tools/stage_runtime.py 放的）：换台电脑不装 Python 也能出图
    os.path.join(_pkg_dir(), "runtime", "python.exe"),
    os.path.join(_pkg_dir(), "dist", "runtime", "python.exe"),   # 源码运行时也给个随包 runtime 兜底
    os.path.join(_pkg_dir(), "dist", "runtime", "python.exe"),   # 源码运行时也给个随包 runtime 兜底
    os.path.join(_pkg_dir(), "runtime", "bin", "python3"),
    (json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8")).get("python")
     if os.path.exists(os.path.join(HERE, "config.json")) else None),
    os.path.join(os.path.expanduser("~"), ".workbuddy", "binaries", "python", "envs",
                 "hanfu", "Scripts", "python.exe"),
    (None if getattr(sys, "frozen", False) else sys.executable),
]


def python_exe():
    for c in _PY_CANDIDATES:
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError(
        "找不到可用的 Python 解释器。\n\n"
        "按这个顺序找过：HANFU_PY 环境变量 → 随包 runtime/ → config.json 的 python →\n"
        "~/.workbuddy/.../envs/hanfu → sys.executable。\n\n"
        "修法：① 用完整发行包（exe 旁边应有 runtime/ 目录，缺了跑 tools/stage_runtime.py）；\n"
        "② 或装 Python 3.10+ 并在 config.json 里写 python 路径；③ 或设 HANFU_PY。")


PY = python_exe()

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_edge():
    p = os.environ.get("HANFU_EDGE")
    for c in ([p] if p else []) + EDGE_CANDIDATES:
        if c and os.path.exists(c):
            return c
    for name in ("msedge", "microsoft-edge", "chrome", "chromium"):
        w = shutil.which(name)
        if w:
            return w
    raise FileNotFoundError("找不到 Edge/Chromium：可设环境变量 HANFU_EDGE")


def registry():
    with open(os.path.join(HERE, "patterns.json"), encoding="utf-8") as fh:
        return json.load(fh)


def resource_path(name):
    """源码目录或 PyInstaller 解包目录里的文件。"""
    return os.path.join(getattr(sys, "_MEIPASS", HERE), name)


def studio_out_dir(*parts):
    """studio 自己的输出根：<workspace>/hanfu-studio/out/…
    子程序几何仍留在各自项目里，但界面导出的东西归 studio，不写进 hanfu-cad。"""
    d = os.path.join(ws_root(), "hanfu-studio", "out", *parts)
    os.makedirs(d, exist_ok=True)
    return d


# ── studio 内部共享组件库（独立资产，不是子项目裁片索引）────────────
def studio_library_dir():
    d = os.path.join(ws_root(), "hanfu-studio", "library")
    os.makedirs(d, exist_ok=True)
    return d


def _safe_cid(cid):
    if (not cid or cid in (".", "..") or os.path.basename(cid) != cid
            or any(ch in cid for ch in '\\/:*?"<>|')):
        raise ValueError("非法组件 id：%r" % (cid,))
    return cid


def library_list():
    out = []
    for fn in glob.glob(os.path.join(studio_library_dir(), "*", "component.json")):
        try:
            with open(fn, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        if d.get("id"):
            out.append(d)
    out.sort(key=lambda x: x.get("updated", ""), reverse=True)
    return out


def library_get(cid, version=None):
    base = os.path.join(studio_library_dir(), _safe_cid(cid))
    cur = os.path.join(base, "component.json")
    if not os.path.exists(cur):
        raise FileNotFoundError("组件不存在：%s" % cid)
    with open(cur, encoding="utf-8") as fh:
        d = json.load(fh)
    if version is None:
        return d
    vf = os.path.join(base, "versions", "%s.json" % version)
    if os.path.exists(vf):
        with open(vf, encoding="utf-8") as fh:
            snap = json.load(fh)
    else:
        snap = dict(d)
    for k in ("id", "name", "source", "schema"):
        snap.setdefault(k, d.get(k))
    return snap


def library_delete(cid):
    d = os.path.join(studio_library_dir(), _safe_cid(cid))
    if not os.path.isdir(d):
        raise FileNotFoundError("组件不存在：%s" % cid)
    shutil.rmtree(d)
    log("library.delete", id=cid, dir=d)


def _sample_cmds(cmds, n=28):
    pts, cur = [], None
    for c in cmds:
        k = c[0]
        if k in ("M", "L"):
            cur = tuple(c[1])
            pts.append(cur)
        elif k == "C":
            p0, p1, p2, p3 = cur, c[1], c[2], c[3]
            for i in range(1, n + 1):
                t = i / n
                mt = 1 - t
                pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
                            + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
                            + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
            cur = tuple(p3)
        elif k == "Q":
            p0, c1, p3 = cur, c[1], c[2]
            for i in range(1, n + 1):
                t = i / n
                pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c1[0] + t * t * p3[0],
                            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c1[1] + t * t * p3[1]))
            cur = tuple(p3)
    return pts


def _piece_thumb_svg(piece):
    pts = _sample_cmds(piece.get("cmds") or [])
    if not pts:
        return ""
    ox, oy = float(piece.get("ox", 0)), float(piece.get("oy", 0))
    xy = [(x + ox, oy - y) for (x, y) in pts]     # 缩略图仍用 SVG 坐标（y 向下）
    xs = [p[0] for p in xy]
    ys = [p[1] for p in xy]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    pad = max(20.0, 0.08 * max(x1 - x0, y1 - y0))
    W, H = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    sw = max(2.0, max(x1 - x0, y1 - y0) / 260.0)
    d = "M " + " L ".join("%.2f %.2f" % p for p in xy) + " Z"
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" '
            'viewBox="%g %g %g %g">'
            '<rect x="%g" y="%g" width="%g" height="%g" fill="#ffffff"/>'
            '<path d="%s" stroke="#1a1a1a" stroke-width="%g" fill="none"/>'
            '</svg>' % (W, H, x0 - pad, y0 - pad, W, H,
                         x0 - pad, y0 - pad, W, H, d, sw))


def library_save(name, piece, source=None, kind="piece"):
    """把组件存成 studio 内部资产：library/<id>/component.json + thumb.png。"""
    base_name = (name or piece.get("name") or "组件").strip()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in base_name)[:40] or "component"
    cid = "%s_%s" % (safe, uuid.uuid4().hex[:6])
    root = os.path.join(studio_library_dir(), cid)
    os.makedirs(os.path.join(root, "versions"), exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    comp = dict(schema="hanfu-studio/component@1", id=cid, name=base_name,
                version=1, kind=kind, source=source or {},
                piece=copy.deepcopy(piece), created=now, updated=now)
    svg = _piece_thumb_svg(piece)
    if svg:
        png = os.path.join(root, "thumb.png")
        try:
            svg_to_png(svg, png, px=360)
            comp["thumb"] = "thumb.png"
        except Exception as e:
            log_exc("library.thumb_fail", e, id=cid)
            try:
                with open(os.path.join(root, "thumb.svg"), "w", encoding="utf-8") as fh:
                    fh.write(svg)
                comp["thumb_svg"] = "thumb.svg"
            except Exception:
                pass
    with open(os.path.join(root, "component.json"), "w", encoding="utf-8") as fh:
        json.dump(comp, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(root, "versions", "1.json"), "w", encoding="utf-8") as fh:
        json.dump(comp, fh, ensure_ascii=False, indent=1)
    log("library.save", id=cid, name=base_name, thumb=bool(comp.get("thumb")))
    return comp


# ── 项目默认组件目录（把 studio 管理的所有项目组件自动收进共享库）──
_CATALOG_SCHEMA = 1
_CATALOG_LOCK = threading.Lock()


def _safe_tag(s, limit=28):
    s = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(s))
    return s[:limit] or "x"


def _catalog_signature():
    reg = registry()
    sig = []
    for p in reg["patterns"]:
        proj = os.path.join(reg["workspace"], p["project"])
        files = [os.path.join(proj, p["script"])]
        if p.get("pieces_post"):
            files.append(os.path.join(proj, p["pieces_post"]))
        sig.append([p["id"], p["cut"],
                    [round(os.path.getmtime(f), 3) if os.path.exists(f) else 0 for f in files]])
    return json.dumps(sig, ensure_ascii=False, sort_keys=True)


def _catalog_path():
    return os.path.join(studio_library_dir(), "_project_catalog.json")


def project_catalog_cached():
    fn = _catalog_path()
    if not os.path.exists(fn):
        return []
    try:
        with open(fn, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return []
    if d.get("schema") != _CATALOG_SCHEMA or d.get("signature") != _catalog_signature():
        return []
    return d.get("components") or []


def _catalog_configs(p):
    """每个项目默认收哪些组件：分裁一个代表配置；通裁按每个模式各收一套。"""
    sexes = p.get("sexes") or ["—"]
    sex = sexes[0]
    modes = p.get("modes") or []
    if p["cut"] == "通裁":
        out = []
        for m in modes:
            out.append(dict(sex=sex, size=m["id"], profile=None, ease=None,
                            mode_label=m.get("label", m["id"])))
        if not out:
            sizes = p["sizes"].get(sex) or ["—"]
            out.append(dict(sex=sex, size=sizes[0], profile=None, ease=None, mode_label=""))
        return out
    sizes = p["sizes"].get(sex) or ["—"]
    size = "M" if "M" in sizes else sizes[len(sizes) // 2]
    m = modes[0] if modes else {}
    ease = "合体" if "合体" in (p.get("ease") or []) else (p.get("ease") or [None])[0]
    return [dict(sex=sex, size=size, profile=m.get("id"), ease=ease,
                 mode_label=m.get("label", ""))]


def project_catalog(refresh=False):
    """生成/读取所有项目组件的默认目录（缓存到 library/_project_catalog.json）。"""
    with _CATALOG_LOCK:
        if not refresh:
            cached = project_catalog_cached()
            if cached:
                return cached
        reg = registry()
        comps = []
        for p in reg["patterns"]:
            for cfg in _catalog_configs(p):
                try:
                    _, meta = build_svg(p["id"], cfg["size"], cfg["sex"], use_cache=False,
                                        profile=cfg["profile"], ease=cfg["ease"])
                except Exception as e:
                    log_exc("catalog.build_fail", e, pid=p["id"], size=cfg["size"])
                    continue
                pieces = meta.get("pieces") or []
                kind = "piece" if p["cut"] == "分裁" else "block"
                for idx, piece in enumerate(pieces):
                    name = piece.get("name") or ("组件%d" % (idx + 1))
                    cid = "proj_%s_%s_%d_%s" % (p["id"], _safe_tag(cfg["size"], 16), idx,
                                                _safe_tag(name))
                    comps.append(dict(
                        schema="hanfu-studio/component@1", id=cid, name=name,
                        version=1, kind=kind, builtin=True,
                        source=dict(project=p["project"], pattern=p["id"],
                                    pattern_label=p["label"], cut=p["cut"],
                                    size=cfg["size"], sex=cfg["sex"],
                                    profile=cfg["profile"], ease=cfg["ease"],
                                    mode_label=cfg["mode_label"]),
                        piece=piece, created="", updated=""))
                log("catalog.pattern", pid=p["id"], size=cfg["size"], pieces=len(pieces))
        data = dict(schema=_CATALOG_SCHEMA, signature=_catalog_signature(),
                    generated=time.strftime("%Y-%m-%d %H:%M:%S"), components=comps)
        with open(_catalog_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        log("catalog.ok", components=len(comps))
        return comps


def piece_outline(piece):
    """裁片轮廓 → SVG 坐标点列（供共享库预览画布）。"""
    pts = _sample_cmds(piece.get("cmds") or [])
    ox, oy = float(piece.get("ox", 0)), float(piece.get("oy", 0))
    return [(x + ox, oy - y) for (x, y) in pts]


def child_env(extra=None):
    """子进程统一用 UTF-8，并清掉 PyInstaller/父进程可能污染的 Python 环境。"""
    env = dict(os.environ)
    for k in ("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"):
        env.pop(k, None)
    mei = getattr(sys, "_MEIPASS", None)
    mei = os.path.abspath(mei) if mei else None
    parts = []
    for p in (env.get("PATH") or "").split(os.pathsep):
        if not p:
            continue
        ap = os.path.abspath(p)
        if mei and (ap == mei or "_MEI" in p.upper()):
            continue        # 防止子解释器误加载打包目录里的 DLL
        parts.append(p)
    env["PATH"] = os.pathsep.join(parts)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if extra:
        env.update(extra)
    return env


def ws_root():
    """仓库根（各子程序所在目录）。patterns.json 的 workspace 可为**相对**（推荐 ".."）；
    打包后（frozen）按 exe 位置向上找；都找不到再退回 config.json / cwd。"""
    ws = registry().get("workspace") or ".."
    cands = []
    try:
        cfg = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
        if cfg.get("workspace"):
            cands.append(cfg["workspace"])
    except Exception:
        pass
    if os.path.isabs(ws):
        cands.append(ws)
    else:
        cands.append(os.path.abspath(os.path.join(HERE, ws)))
        if getattr(sys, "frozen", False):
            d = os.path.dirname(os.path.abspath(sys.executable))
            for _ in range(5):
                cands.append(d)
                d = os.path.dirname(d)
    for c in cands:
        if c and os.path.isdir(os.path.join(c, "hanfu-cad")):
            return c
    return cands[0] if cands else os.getcwd()


def spec_of(pid):
    for p in registry()["patterns"]:
        if p["id"] == pid:
            return p
    raise KeyError("没有这个版型：%s" % pid)


def groups():
    """按谱系根分组：分裁 / 通裁"""
    out = {}
    for p in registry()["patterns"]:
        out.setdefault(p["cut"], []).append(p)
    return out


# ── 项目登记（studio 可写；内置项目从 patterns.json 派生）──────────
_PROJECTS_SCHEMA = 1


def projects_path():
    return os.path.join(ws_root(), "hanfu-studio", "projects.json")


def _load_user_projects():
    fn = projects_path()
    if not os.path.exists(fn):
        return []
    try:
        with open(fn, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return []
    if isinstance(d, dict):
        return d.get("projects") or []
    return d if isinstance(d, list) else []


def _save_user_projects(items):
    fn = projects_path()
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with open(fn, "w", encoding="utf-8") as fh:
        json.dump(dict(schema=_PROJECTS_SCHEMA, projects=items), fh,
                  ensure_ascii=False, indent=1)


def _write_project_manifest(rec):
    folder = rec.get("folder")
    if not folder:
        return
    os.makedirs(folder, exist_ok=True)
    data = dict(schema="hanfu-studio/project@1", id=rec["id"], name=rec.get("name"),
                note=rec.get("note", ""), created=rec.get("created", ""),
                updated=rec.get("updated", ""), patterns=rec.get("patterns") or [])
    with open(os.path.join(folder, "project.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def projects():
    """全部项目：内置（patterns.json）+ studio 自建（projects.json）。"""
    reg = registry()
    ws = reg["workspace"]
    by = {}
    order = []
    for p in reg["patterns"]:
        folder = p["project"]
        if folder not in by:
            by[folder] = []
            order.append(folder)
        by[folder].append(p)
    out = []
    for folder in order:
        out.append(dict(id="builtin:" + _safe_tag(folder), name=folder,
                        folder=os.path.join(ws, folder), builtin=True,
                        note="内置项目（来自 patterns.json）", patterns=by[folder],
                        created="", updated=""))
    regmap = dict((p["id"], p) for p in reg["patterns"])
    for up in _load_user_projects():
        pats = [regmap[x] for x in (up.get("patterns") or []) if x in regmap]
        out.append(dict(id=up.get("id"), name=up.get("name") or up.get("id"),
                        folder=up.get("folder") or "", builtin=False,
                        note=up.get("note") or "", patterns=pats,
                        created=up.get("created") or "", updated=up.get("updated") or ""))
    return out


# ── 注册版型：父程序登记"已有的版型程序"，不复制源码 ────────────────
_ALLOWED_PH = {"sex", "size", "out", "profile", "ease"}


def pattern_probe(rec):
    """预检一条版型登记：项目/脚本/语法/argstyle/模式/号型/id 唯一。返回 [(项, ok, 说明)]。"""
    out = []
    ws = ws_root()
    proj = (rec.get("project") or "").strip()
    proj_dir = os.path.join(ws, proj) if proj else ""
    out.append(("项目目录", bool(proj_dir) and os.path.isdir(proj_dir), proj_dir or "未填"))
    script = os.path.join(proj_dir, (rec.get("script") or "").strip()) if proj_dir else ""
    ok_script = bool(script) and os.path.isfile(script)
    out.append(("脚本存在", ok_script, script or "未填"))
    if ok_script:
        r = _run([PY, "-c",
                            "import py_compile,sys;py_compile.compile(sys.argv[1],doraise=True)",
                            script], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=child_env(), timeout=120)
        out.append(("脚本语法", r.returncode == 0, (r.stderr or "可编译")[-160:]))
    run = rec.get("run") or {}
    kind = run.get("kind")
    out.append(("运行方式", kind in ("make", "params"),
                kind if kind else "未填（make/params）"))
    style = run.get("argstyle") or ""
    ph = set(re.findall(r"\{(\w+)\}", style))
    out.append(("argstyle 占位", ph <= _ALLOWED_PH,
                ("ok：" + ",".join(sorted(ph))) if ph <= _ALLOWED_PH
                else "非法占位：%s" % ",".join(sorted(ph - _ALLOWED_PH))))
    modes = rec.get("modes") or []
    out.append(("模式说明", all(m.get("id") and m.get("label") for m in modes) if modes else kind == "make",
                "%d 个模式" % len(modes)))
    if kind == "params":
        fx = run.get("fixtures") or {}
        mids = [m["id"] for m in modes]
        out.append(("模式＝夹具键", set(mids) == set(fx.keys()),
                    "模式 %s ／ 夹具 %s" % (mids, list(fx))))
        sizes = rec.get("sizes") or {}
        allsz = [s for v in sizes.values() for s in v]
        out.append(("号型＝夹具键", set(allsz) == set(fx.keys()),
                    "号型 %s" % allsz))
    else:
        sexes = rec.get("sexes") or []
        sizes = rec.get("sizes") or {}
        out.append(("号型表", bool(sexes) and all(sizes.get(x) for x in sexes),
                    "%s" % {k: len(v) for k, v in sizes.items()}))
        out.append(("argstyle 含 --out", "{out}" in style, style or "未填"))
    out.append(("id 未占用", all(p["id"] != rec.get("id") for p in registry()["patterns"]),
                rec.get("id") or "未填"))
    return out


def register_pattern(rec):
    """把一条版型登记写进 patterns.json（custom=True）。预检不过不写。"""
    checks = pattern_probe(rec)
    bad = [c for c in checks if not c[1]]
    if bad:
        raise ValueError("预检未过：" + "；".join("%s（%s）" % (c[0], c[2]) for c in bad))
    path = os.path.join(HERE, "patterns.json")
    d = json.load(open(path, encoding="utf-8"))
    item = dict(rec)
    item["custom"] = True
    item.setdefault("label", item["id"])
    d["patterns"].append(item)
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("pattern.register", pid=item["id"], project=item.get("project"),
        script=item.get("script"), kind=(item.get("run") or {}).get("kind"))
    return item


def unregister_pattern(pid):
    """注销：只允许删除 custom 登记的版型（源码不在工作室里，删登记而已）。"""
    path = os.path.join(HERE, "patterns.json")
    d = json.load(open(path, encoding="utf-8"))
    keep, drop = [], None
    for p in d["patterns"]:
        if p["id"] == pid:
            if not p.get("custom"):
                raise ValueError("内置版型不能注销：%s" % pid)
            drop = p
        else:
            keep.append(p)
    if not drop:
        raise ValueError("没有这个登记：%s" % pid)
    d["patterns"] = keep
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("pattern.unregister", pid=pid)
    return pid


def project_get(proj_id):
    for p in projects():
        if p.get("id") == proj_id:
            return p
    return None


def _protected_folder(folder):
    """workspace 根、studio 目录、任何已注册项目目录及其子目录都不许当自建项目目录。"""
    ws = os.path.abspath(ws_root())
    f = os.path.abspath(folder)
    if f == ws:
        return True
    roots = [os.path.join(ws, "hanfu-studio")]
    roots += [os.path.abspath(os.path.join(ws, p["project"])) for p in registry()["patterns"]]
    return any(f == r or f.startswith(r + os.sep) for r in roots)


def project_create(name, folder=None, pattern_ids=None, note=""):
    name = (name or "").strip()
    if not name:
        raise ValueError("项目名不能为空")
    ws = ws_root()
    explicit = bool(folder and str(folder).strip())
    folder = os.path.abspath(os.path.expanduser(
        folder if explicit else os.path.join(ws, _safe_tag(name, 40))))
    if _protected_folder(folder):
        raise ValueError("不能把项目目录设在已有项目或 studio 目录内：%s" % folder)
    if explicit and os.path.exists(os.path.join(folder, "project.json")):
        raise ValueError("目录已有 project.json，请换一个目录")
    if not explicit:
        base = folder
        n = 2
        while os.path.exists(folder) and os.listdir(folder):
            folder = "%s_%d" % (base, n)
            n += 1
    if os.path.exists(folder) and not os.path.isdir(folder):
        raise ValueError("目录不是文件夹：%s" % folder)
    os.makedirs(folder, exist_ok=True)
    valid = set(p["id"] for p in registry()["patterns"])
    pats = []
    for x in (pattern_ids or []):
        if x in valid and x not in pats:
            pats.append(x)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    rec = dict(id="user:%s_%s" % (_safe_tag(name, 30), uuid.uuid4().hex[:6]),
               name=name, folder=folder, note=note, patterns=pats,
               created=now, updated=now)
    raw = _load_user_projects()
    raw.append(rec)
    _save_user_projects(raw)
    _write_project_manifest(rec)
    log("project.create", id=rec["id"], name=name, folder=folder, patterns=len(pats))
    return project_get(rec["id"])


def _update_user_project(proj_id, fn):
    raw = _load_user_projects()
    for rec in raw:
        if rec.get("id") == proj_id:
            if str(proj_id).startswith("builtin:"):
                raise ValueError("内置项目不能修改")
            fn(rec)
            rec["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            _save_user_projects(raw)
            _write_project_manifest(rec)
            return rec
    raise KeyError("项目不存在：%s" % proj_id)


def project_update(proj_id, name=None, folder=None, note=None):
    def fn(rec):
        if name is not None:
            if not str(name).strip():
                raise ValueError("项目名不能为空")
            rec["name"] = str(name).strip()
        if folder is not None:
            f = os.path.abspath(os.path.expanduser(folder))
            if _protected_folder(f):
                raise ValueError("不能把项目目录设在已有项目或 studio 目录内：%s" % f)
            mf = os.path.join(f, "project.json")
            if os.path.exists(mf):
                try:
                    with open(mf, encoding="utf-8") as fh:
                        md = json.load(fh)
                except Exception:
                    md = {}
                if md.get("id") not in (None, rec.get("id")):
                    raise ValueError("目录已有另一个项目：%s" % f)
            if os.path.exists(f) and not os.path.isdir(f):
                raise ValueError("目录不是文件夹：%s" % f)
            os.makedirs(f, exist_ok=True)
            rec["folder"] = f
        if note is not None:
            rec["note"] = note
    _update_user_project(proj_id, fn)
    log("project.update", id=proj_id)
    return project_get(proj_id)


def project_delete_preview(proj_id):
    """删除前预览：列出项目目录里将被删除的文件/目录，并判断目录是否可安全删除。"""
    proj = project_get(proj_id)
    if not proj:
        raise KeyError("项目不存在：%s" % proj_id)
    if proj.get("builtin"):
        raise ValueError("内置项目不能删除")
    folder = proj.get("folder") or ""
    info = dict(folder=folder, exists=False, files=[], dirs=[], size=0,
                manifest_ok=False, safe=False, reason="")
    if not folder or not os.path.isdir(folder):
        info["reason"] = "项目目录不存在"
        return info
    info["exists"] = True
    manifest = os.path.join(folder, "project.json")
    if os.path.exists(manifest):
        try:
            with open(manifest, encoding="utf-8") as fh:
                md = json.load(fh)
            info["manifest_ok"] = md.get("id") == proj_id
        except Exception:
            info["manifest_ok"] = False
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        relroot = os.path.relpath(root, folder)
        for d in dirs:
            info["dirs"].append(d if relroot == "." else os.path.join(relroot, d))
        for f in sorted(files):
            full = os.path.join(root, f)
            info["files"].append(f if relroot == "." else os.path.join(relroot, f))
            try:
                info["size"] += os.path.getsize(full)
            except OSError:
                pass
    if _protected_folder(folder):
        info["reason"] = "目录位于受保护的项目路径"
    elif not info["manifest_ok"]:
        info["reason"] = "目录缺少匹配的 project.json"
    else:
        info["safe"] = True
    return info


def project_delete(proj_id, delete_folder=True):
    """删除自建项目：移除登记，并在确认安全时删除带匹配 project.json 的项目目录。"""
    if str(proj_id).startswith("builtin:"):
        raise ValueError("内置项目不能删除")
    raw = _load_user_projects()
    rec = next((r for r in raw if r.get("id") == proj_id), None)
    if rec is None:
        raise KeyError("项目不存在：%s" % proj_id)
    folder = rec.get("folder") or ""
    deleted = False
    reason = ""
    if delete_folder and folder and os.path.isdir(folder):
        manifest = os.path.join(folder, "project.json")
        safe = False
        if os.path.exists(manifest):
            try:
                with open(manifest, encoding="utf-8") as fh:
                    md = json.load(fh)
                safe = md.get("id") == proj_id
            except Exception:
                safe = False
        protected = _protected_folder(folder)
        if protected:
            safe = False
            reason = "目录位于受保护的项目路径"
        elif not safe:
            reason = "目录缺少匹配的 project.json"
        if safe:
            shutil.rmtree(folder)
            deleted = True
    kept = [r for r in raw if r.get("id") != proj_id]
    _save_user_projects(kept)
    log("project.delete", id=proj_id, folder=folder, folder_deleted=deleted, reason=reason)
    return dict(folder=folder, folder_deleted=deleted, reason=reason)


def project_add_patterns(proj_id, pattern_ids):
    valid = set(p["id"] for p in registry()["patterns"])

    def fn(rec):
        pats = list(rec.get("patterns") or [])
        for x in (pattern_ids or []):
            if x in valid and x not in pats:
                pats.append(x)
        rec["patterns"] = pats
    _update_user_project(proj_id, fn)
    log("project.add_patterns", id=proj_id, add=len(pattern_ids or []))
    return project_get(proj_id)


def project_remove_patterns(proj_id, pattern_ids):
    drop = set(pattern_ids or [])

    def fn(rec):
        rec["patterns"] = [x for x in (rec.get("patterns") or []) if x not in drop]
    _update_user_project(proj_id, fn)
    log("project.remove_patterns", id=proj_id, remove=len(drop))
    return project_get(proj_id)


def modes(pid):
    """版型的「可复用模式」清单（基准档 / 夹具），父程序据此一键调用子程序。"""
    spec = spec_of(pid)
    return spec.get("modes") or []


def default_profile(sex):
    return "artifact" if sex == "女" else "vendor"


def _args(spec, sex, size, out, profile=None, ease=None):
    """按注册表的 argstyle 拼命令行——这是父程序与子程序之间唯一的接口。"""
    style = spec["run"].get("argstyle") or "--sex {sex} --size {size} --out {out}"
    fmt = dict(sex=sex, size=size, out=out,
               profile=profile or default_profile(sex),
               ease=ease or "合体")
    return [a for a in style.format(**fmt).split() if a]


def _read_pieces(src, params_kind=False):
    """从脚本产物里取裁片几何（pieces.json）。通裁可能没有 pieces → 返回空表。"""
    if params_kind:
        paths = [src.rsplit(".", 1)[0] + ".pieces.json"]
    else:
        paths = sorted(glob.glob(os.path.join(src, "**", "*.pieces.json"), recursive=True))
    fallback = ([], None)
    for fn in paths:
        if not os.path.exists(fn):
            continue
        try:
            d = json.load(open(fn, encoding="utf-8"))
        except Exception:
            continue
        pieces = d.get("pieces") or []
        canvas = d.get("canvas")
        if pieces:
            log("pieces.read", file=os.path.basename(fn), n=len(pieces))
            return pieces, canvas
        fallback = (pieces, canvas)
    return fallback


def build_svg(pid, size, sex="女", overrides=None, use_cache=True, profile=None, ease=None):
    overrides = overrides or {}
    log("build.start", pid=pid, size=size, sex=sex, profile=profile or "-", ease=ease or "-",
        overrides=json.dumps(overrides, ensure_ascii=False))
    key = (pid, size, sex, profile or "", ease or "",
           tuple(sorted(overrides.items())))
    if use_cache and key in CACHE:
        return CACHE[key]

    spec = spec_of(pid)
    ws = ws_root()
    proj = os.path.join(ws, spec["project"])
    script = os.path.join(proj, spec["script"])
    if not os.path.exists(script):
        raise FileNotFoundError("脚本不存在：%s" % script)

    tmp = tempfile.mkdtemp(prefix="studio_")
    env = child_env()
    t0 = time.time()
    kind = spec["run"]["kind"]

    if kind == "make":
        r = _run([PY, script] + _args(spec, sex, size, tmp, profile, ease),
                           cwd=proj, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        if r.returncode != 0:
            log("build.fail", pid=pid, size=size, rc=r.returncode,
                stderr=(r.stderr or "")[-600:], stdout=(r.stdout or "")[-300:])
            raise RuntimeError("脚本失败：%s" % (r.stderr or r.stdout)[-500:])
        cands = [f for f in glob.glob(os.path.join(tmp, "**", "*.svg"), recursive=True)
                 if "拼合平铺图" not in os.path.basename(f)]
        if not cands:
            raise RuntimeError("没有生成 SVG")
        svg = open(sorted(cands)[0], encoding="utf-8").read()
        params = {}
    else:
        params = dict(spec["run"]["fixtures"].get(size, {}))
        for k, v in overrides.items():
            params[k] = float(v)
        out_svg = os.path.join(tmp, "sheet.svg")
        env["HANFU_PARAMS"] = json.dumps(params, ensure_ascii=False)
        env["HANFU_OUT"] = out_svg
        r = _run([PY, script], cwd=os.path.dirname(script), env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        if r.returncode != 0 or not os.path.exists(out_svg):
            log("export.fail", pid=pid, size=size, rc=r.returncode,
                stderr=(r.stderr or "")[-600:])
            raise RuntimeError("脚本失败：%s" % (r.stderr or r.stdout)[-500:])
        post = spec.get("pieces_post")
        if post:
            pj = out_svg.rsplit(".", 1)[0] + ".pieces.json"
            ps = os.path.join(proj, post)
            rp = _run([PY, ps, pj], cwd=os.path.dirname(ps), env=env,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=120)
            if rp.returncode != 0:
                log("pieces_post.fail", pid=pid, size=size, rc=rp.returncode,
                    stderr=(rp.stderr or "")[-600:])
        svg = open(out_svg, encoding="utf-8").read()

    pieces, canvas = _read_pieces(tmp if kind == "make" else out_svg,
                                  params_kind=(kind != "make"))
    meta = dict(pid=pid, label=spec["label"], cut=spec["cut"], size=size, sex=sex,
                params=params, ms=int((time.time() - t0) * 1000),
                bytes=len(svg), script=os.path.relpath(script, ws),
                pieces=pieces, canvas=canvas)
    shutil.rmtree(tmp, ignore_errors=True)
    log("build.ok", pid=pid, size=size, ms=meta["ms"], bytes=meta["bytes"])
    if use_cache:
        CACHE[key] = (svg, meta)
    return svg, meta


def export(pid, size, sex="女", overrides=None, outdir=None, profile=None, ease=None):
    """把当前配置的产物落盘（不改几何，只是让脚本写到指定目录）。

    分裁（kind=make）：脚本自己会出 .svg + .dxf + .pieces.json → 直接 --out 到目标目录
    通裁（kind=params）：脚本只出 .svg + .pieces.json；DXF 要"整衣一片"，另行处理，这里不假装有
    """
    overrides = overrides or {}
    spec = spec_of(pid)
    ws = ws_root()
    proj = os.path.join(ws, spec["project"])
    script = os.path.join(proj, spec["script"])
    outdir = outdir or studio_out_dir("exports", "%s_%s" % (pid, str(size).replace("/", "-")))
    os.makedirs(outdir, exist_ok=True)

    if spec["run"]["kind"] == "make":
        r = _run([PY, script] + _args(spec, sex, size, outdir, profile, ease),
                           cwd=proj, env=child_env(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        if r.returncode != 0:
            log("build.fail", pid=pid, size=size, rc=r.returncode,
                stderr=(r.stderr or "")[-600:], stdout=(r.stdout or "")[-300:])
            raise RuntimeError("脚本失败：%s" % (r.stderr or r.stdout)[-500:])
    else:
        params = dict(spec["run"]["fixtures"].get(size, {}))
        for k, v in overrides.items():
            params[k] = float(v)
        out_svg = os.path.join(outdir, "%s_%s.svg" % (pid, size))
        env = child_env()
        env["HANFU_PARAMS"] = json.dumps(params, ensure_ascii=False)
        env["HANFU_OUT"] = out_svg
        r = _run([PY, script], cwd=os.path.dirname(script), env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        if r.returncode != 0 or not os.path.exists(out_svg):
            log("export.fail", pid=pid, size=size, rc=r.returncode,
                stderr=(r.stderr or "")[-600:])
            raise RuntimeError("脚本失败：%s" % (r.stderr or r.stdout)[-500:])
        # 补片：通裁的 build_* 只写空 pieces，pieces_post 才会把裁片/区块补进去
        post = spec.get("pieces_post")
        if post:
            side = out_svg.rsplit(".", 1)[0] + ".pieces.json"
            rp = _run([PY, os.path.join(proj, post), side], cwd=proj,
                                env=child_env(), capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=300)
            log("export.pieces_post", pid=pid, size=size, rc=rp.returncode,
                ok=os.path.exists(side))
        # 整衣 DXF（方案 B：一条连续外轮廓 + 标注）——同一套参数再跑整衣脚本
        ex = next((e for e in spec.get("extras", []) if e["id"] == "whole_dxf"), None)
        if ex:
            whole = os.path.join(proj, ex["script"])
            env2 = dict(env)
            env2["HANFU_OUT"] = os.path.join(outdir, "整衣_%s.dxf" % size)
            _run([PY, whole], cwd=os.path.dirname(whole), env=env2,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)

    files = sorted(glob.glob(os.path.join(outdir, "**", "*.*"), recursive=True))
    log("export.ok", pid=pid, size=size, dir=outdir, files=len(files),
        dxf=any(f.lower().endswith(".dxf") for f in files))
    return dict(dir=outdir, files=[os.path.relpath(f, outdir) for f in files],
                dxf=any(f.lower().endswith(".dxf") for f in files))


def generate_all(pid, size, sex="女", overrides=None, profile=None, ease=None, outdir=None):
    """一键生成：预览用 SVG + 落盘全套产物（分裁：svg/dxf/pieces/尺码表；通裁：加整衣 DXF）。"""
    spec = spec_of(pid)
    outdir = outdir or studio_out_dir("generate", "%s_%s_%s"
                                      % (pid, size, time.strftime("%m%d-%H%M")))
    os.makedirs(outdir, exist_ok=True)
    log("gen.start", pid=pid, size=size, outdir=outdir)
    svg, meta = build_svg(pid, size, sex, overrides, use_cache=False, profile=profile, ease=ease)
    with open(os.path.join(outdir, "预览.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)
    r = export(pid, size, sex, overrides, outdir=outdir, profile=profile, ease=ease)
    # 生成即闸门：形制核对（失败只示意，不阻断）
    gres = None
    try:
        import gates as G
        side = glob.glob(os.path.join(outdir, "*.pieces.json"))
        pd = {}
        if side:
            pd = json.load(open(sorted(side)[0], encoding="utf-8"))
        gres = G.run(pid, size, sex, params=pd.get("params") or meta.get("params"),
                     resolved=pd.get("resolved") or {},
                     pieces=pd.get("pieces") or meta.get("pieces"),
                     outdir=os.path.join(outdir, "形制核对"))
    except Exception as e:
        log("gates.fail", pid=pid, size=size, err="%s: %s" % (type(e).__name__, e))
    files = sorted(glob.glob(os.path.join(outdir, "**", "*.*"), recursive=True))
    log("gen.ok", pid=pid, size=size, files=len(files), dir=outdir,
        gates="%s/%s" % ((gres or {}).get("summary", {}).get("pass_", "-"),
                          (gres or {}).get("summary", {}).get("warn", "-")))
    return dict(dir=outdir, files=[os.path.relpath(f, outdir) for f in files],
                dxf=any(f.lower().endswith(".dxf") for f in files), meta=meta, gates=gres)


def batch_plan(pid, sex=None, all_sizes=False):
    """列出"批量生成"要跑的组合：分裁＝模式(基准) × 放量 × 号型；通裁＝每个夹具模式。"""
    spec = spec_of(pid)
    kind = (spec.get("run") or {}).get("kind")
    plan = []
    if kind == "make":
        sexes = [sex] if sex else (spec.get("sexes") or ["女"])
        for s in sexes:
            sizes = (spec.get("sizes") or {}).get(s) or []
            if not all_sizes:
                sizes = [sizes[len(sizes) // 2]] if sizes else []
            eases = list(spec.get("ease") or ["合体"])      # patterns.json 里是数组
            if not all_sizes:
                eases = [eases[len(eases) // 2]]             # 取中档（合体）
            for m in (spec.get("modes") or []):
                for e in eases:
                    for sz in sizes:
                        plan.append(dict(profile=m["id"], mode=m["label"], ease=e, sex=s, size=sz))
    else:
        for m in (spec.get("modes") or []):
            plan.append(dict(profile=None, mode=m["label"], ease=None, sex=(spec.get("sexes") or ["—"])[0],
                             size=m["id"]))
    return plan


def _flatten(d, inner_name=None):
    """把 make.py 自建的内层目录（<profile>_<sex>_<size>）内容提到 d 下，删空壳。
    inner_name 为空时，退化为"只有一个子目录才压平"。"""
    try:
        items = list(os.listdir(d))
    except OSError:
        return
    dirs = [x for x in items if os.path.isdir(os.path.join(d, x))]
    target = inner_name if inner_name in dirs else (dirs[0] if len(dirs) == 1 else None)
    if not target:
        return
    inner = os.path.join(d, target)
    for x in os.listdir(inner):
        src, dst = os.path.join(inner, x), os.path.join(d, x)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst, ignore_errors=True)
            else:
                os.remove(dst)
        shutil.move(src, dst)
    try:
        os.rmdir(inner)
    except OSError:
        pass


def generate_batch(pid, sex=None, all_sizes=False, outdir=None):
    """批量生成：每个"可复用模式"各出一整套产物 + 形制核对；最后写 批量清单.md。"""
    spec = spec_of(pid)
    plan = batch_plan(pid, sex=sex, all_sizes=all_sizes)
    fresh = outdir is None
    outdir = outdir or studio_out_dir("batch", pid)          # 固定目录：每次重建，不按时间戳堆垃圾
    if fresh and os.path.isdir(outdir):
        shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir, exist_ok=True)
    log("batch.start", pid=pid, n=len(plan), dir=outdir)
    rows = []
    for item in plan:
        tag = "%s_%s_%s" % (item["profile"] or item["size"], item["sex"], item["size"])
        if item["ease"]:
            tag += "_" + item["ease"]
        tag = tag.replace("/", "-")
        try:
            sub = os.path.join(outdir, tag)
            r = generate_all(pid, item["size"], item["sex"], {}, profile=item["profile"],
                             ease=item["ease"], outdir=sub)
            if item["profile"]:      # 只有分裁（make）会自建内层目录；通裁的"形制核对/"必须留着
                _flatten(sub, "%s_%s_%s" % (item["profile"], item["sex"], item["size"]))
            sm = (r.get("gates") or {}).get("summary") or {}
            rows.append(dict(item, tag=tag, files=len(r["files"]), dxf=r["dxf"],
                             gates=sm, ok=True))
        except Exception as e:
            log("batch.item_fail", pid=pid, tag=tag, err="%s: %s" % (type(e).__name__, e))
            rows.append(dict(item, tag=tag, files=0, dxf=False, gates={}, ok=False, err=str(e)[:200]))
    L = ["# 批量生成 · %s（每个可复用模式一整套）" % spec["label"], "",
         "> 由 `adapters.generate_batch()` 生成。每行一个组合：产物目录 `./<tag>/` 内含 "
         "SVG / 裁片 JSON / DXF（通裁另含整衣 DXF）+ `形制核对/`。", "",
         "| 模式 | 基准 | 放量 | 性别 | 号型 | 文件 | DXF | 核对(通过/示意) | 结果 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        sm = x.get("gates") or {}
        L.append("| %s | %s | %s | %s | %s | %d | %s | %s/%s | %s |"
                 % (x["mode"], x.get("profile") or "—", x.get("ease") or "—", x["sex"], x["size"],
                    x["files"], "有" if x["dxf"] else "无",
                    sm.get("pass_", "-"), sm.get("warn", "-"),
                    "OK" if x.get("ok") else ("失败：" + x.get("err", ""))))
    ok_n = sum(1 for x in rows if x.get("ok"))
    L += ["", "**合计：%d 组，成功 %d，失败 %d**" % (len(rows), ok_n, len(rows) - ok_n)]
    fn = os.path.join(outdir, "批量清单.md")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    log("batch.ok", pid=pid, n=len(rows), ok=ok_n, dir=outdir)
    return dict(dir=outdir, rows=rows, manifest=fn, ok=ok_n, total=len(rows))


def export_layout_dxf(pid, size, sex="女", pieces=None, layout=None, canvas=None,
                      outdir=None, profile=None, ease=None, seam=0.0):
    """把「手工排料」写成真正可裁的 DXF：移动、新建、复制的裁片都进图。

    输入是子程序产出的 pieces.json（源几何）+ 界面布局（位移/新增），
    几何本身仍留在各项目里；这里只做摆放变换并调 layout_dxf.py 出图。
    """
    spec = spec_of(pid)
    if spec["cut"] != "分裁":
        raise ValueError("%s 是通裁：整衣 DXF 由「导出产物」出，不做裁片排料" % spec["label"])
    if not pieces:
        raise ValueError("没有裁片几何（pieces.json 为空），无法生成排料 DXF")
    layout = layout or {}
    transforms = layout.get("transforms") or {}
    added = layout.get("added") or {}

    def shift(p, dx, dy):
        q = copy.deepcopy(p)
        q["ox"] = float(p.get("ox", 0)) + dx
        # SVG y = oy - local_y；界面向下移动 dy，对应 oy + dy（CAD 里 y 随之 -dy）
        q["oy"] = float(p.get("oy", 0)) + dy
        box = p.get("box")
        if box:
            q["box"] = [box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy]
        return q

    out_pieces = []
    for p in pieces:
        dx, dy = transforms.get(p.get("name"), (0.0, 0.0))
        out_pieces.append(shift(p, dx, dy))
    for name, item in added.items():
        p = item.get("piece")
        if not p:
            continue
        dx, dy = transforms.get(name, (0.0, 0.0))
        q = shift(p, dx, dy)
        q["name"] = name
        q["qty"] = 1
        if item.get("ref"):
            q["library"] = copy.deepcopy(item["ref"])
        out_pieces.append(q)
    if not out_pieces:
        raise ValueError("排料里没有裁片")

    if not canvas:
        canvas = [max(p["box"][2] for p in out_pieces) + 200,
                  max(p["box"][3] for p in out_pieces) + 200]
    tag = "%s_%s" % (pid, str(size).replace("/", "-"))
    outdir = outdir or studio_out_dir("排料_%s_%s" % (tag, time.strftime("%m%d-%H%M%S")))
    os.makedirs(outdir, exist_ok=True)
    jf = os.path.join(outdir, "手工排料_%s.pieces.json" % tag)
    df = os.path.join(outdir, "手工排料_%s.dxf" % tag)
    data = dict(canvas=canvas, pieces=out_pieces, seam_allowance=float(seam or 0),
                title="%s · %s · %s" % (spec["label"], size,
                                        ("加载 %s" % profile) if profile else ""))
    with open(jf, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    script = resource_path("layout_dxf.py")
    t0 = time.time()
    r = _run([PY, "-P", script, jf, df], env=child_env(), cwd=outdir,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    if r.returncode != 0 or not os.path.exists(df):
        log("layoutdxf.fail", pid=pid, size=size, rc=r.returncode,
            stderr=(r.stderr or "")[-700:])
        raise RuntimeError("排料 DXF 失败：%s" % ((r.stderr or r.stdout or "")[-500:]))
    log("layoutdxf.ok", pid=pid, size=size, seam=seam, pieces=len(out_pieces),
        ms=int((time.time() - t0) * 1000), file=df)
    return dict(dir=outdir, dxf=df, pieces_json=jf, n=len(out_pieces), seam=seam,
                files=[os.path.basename(jf), os.path.basename(df)])


def import_dxf(path):
    """DXF → SVG（外部 CAD 协同）。返回 SVG 文本和转换摘要。"""
    script = resource_path("dxf_io.py")
    tmp = tempfile.mkdtemp(prefix="studio_dxf_in_")
    svg = os.path.join(tmp, "imported.svg")
    t0 = time.time()
    r = _run([PY, "-P", script, "import", path, svg], env=child_env(), cwd=tmp,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    if r.returncode != 0 or not os.path.exists(svg):
        log("dxf.import.fail", file=path, rc=r.returncode,
            stderr=(r.stderr or "")[-700:])
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError("DXF 导入失败：%s" % ((r.stderr or r.stdout or "")[-500:]))
    with open(svg, encoding="utf-8") as fh:
        text = fh.read()
    meta = {}
    for line in reversed((r.stdout or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                meta = json.loads(line)
                break
            except Exception:
                pass
    shutil.rmtree(tmp, ignore_errors=True)
    meta["ms"] = int((time.time() - t0) * 1000)
    log("dxf.import.ok", file=path, entities=meta.get("entities"),
        layers=meta.get("layers"), ms=meta["ms"])
    return text, meta


def export_scene_dxf(scene, out_path):
    """场景 JSON → DXF（保留图层/颜色/文字）。"""
    script = resource_path("dxf_io.py")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    jf = os.path.splitext(out_path)[0] + ".scene.json"
    with open(jf, "w", encoding="utf-8") as fh:
        json.dump(scene, fh, ensure_ascii=False, indent=1)
    t0 = time.time()
    r = _run([PY, "-P", script, "export", jf, out_path], env=child_env(),
                       cwd=os.path.dirname(os.path.abspath(out_path)),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    if r.returncode != 0 or not os.path.exists(out_path):
        log("dxf.export.fail", file=out_path, rc=r.returncode,
            stderr=(r.stderr or "")[-700:])
        raise RuntimeError("DXF 导出失败：%s" % ((r.stderr or r.stdout or "")[-500:]))
    meta = {}
    for line in reversed((r.stdout or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                meta = json.loads(line)
                break
            except Exception:
                pass
    meta.update(dxf=out_path, scene_json=jf, ms=int((time.time() - t0) * 1000))
    log("dxf.export.ok", file=out_path, entities=meta.get("entities"),
        layers=meta.get("layers"), ms=meta["ms"])
    return meta


CONVENTIONS = {    "设计目的": "每个版型一种程序；父程序专门逆向出版型的程序",
    "两个入口": "逆向（实物/官图→版型程序）、许愿（一句话需求→版型程序）；"
                "两者都面向 harness（AI 会话）做量图/判级/派生，桌面程序只承载状态与交接",
    "许愿判级": {"参数级": "同一程序换夹具（不新建程序）",
                "结构级": "用 Δ 派生新程序（禁止复制父版型源码）",
                "裁法级": "新谱系根（分裁 ↔ 通裁）"},
    "继承规则": "允许取用父版型的片，禁止复制父版型源码；派生记录只记 op/参数/父版型/产物 hash，不记几何",
    "拟合边界": "只许纯形状自由度（白名单）；只出建议值不改 DEF；多闸门；正背共用一组参数",
    "禁止": ["合并成万能参数化引擎", "共享层加服饰语义", "用 YAML-DSL 描述版型",
             "造自动化的许愿引擎/DSL（交互面向 harness）"],
}


def interface_file(kind, request="", artifact_path="", pid=None, size=None, sex=None,
                   overrides=None, outdir=None, components=None, library=None):
    """导出「接口文件」给 harness：把版型、模式、参数、组件、闸门、约定打包成一个 JSON。"""
    spec = spec_of(pid) if pid else None
    out = dict(
        schema="hanfu-studio/interface@1",
        created=time.strftime("%Y-%m-%d %H:%M:%S"),
        task=dict(kind=kind, request=request, artifact_path=artifact_path),
        pattern=None, components=list(components or []), library=list(library or []),
        gates=[], conventions=CONVENTIONS,
        workspace=ws_root(),
        log=log_path(),
    )
    if spec:
        out["pattern"] = dict(
            id=spec["id"], label=spec["label"], cut=spec["cut"], project=spec["project"],
            script=spec["script"], run=spec["run"], modes=spec.get("modes") or [],
            mode_kind=spec.get("mode_kind"), ease=spec.get("ease"),
            knobs=spec.get("knobs") or [], extras=[e["id"] for e in (spec.get("extras") or [])],
            size=size, sex=sex, params=overrides or {},
            product=spec.get("product", ""),
        )
    out["gates"] = [
        dict(name="像素叠合（可叠合判定）", cmd="python verification/overlay.py front back",
             where="hanfu-cad/（叠合根＝archive/v3 含接袖原尺寸版）"),
        dict(name="形状拟合（只出建议值）", cmd="python verification/fit.py", where="hanfu-cad/"),
        dict(name="形制核对表", cmd="python verification/verify.py", where="hanfu-cad/ 与 hanfu-jiexiu/"),
        dict(name="通裁整衣 DXF", cmd="python pattern/export_dxf_whole.py", where="hanfu-shenyi/"),
    ]
    outdir = outdir or os.path.join(ws_root(), "hanfu-studio", "out", "interface")
    os.makedirs(outdir, exist_ok=True)
    fn = os.path.join(outdir, "interface_%s_%s.json" % (kind, time.strftime("%m%d-%H%M%S")))
    json.dump(out, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("iface.write", kind=kind, pid=pid or "-", file=fn, request=request[:80])
    return fn


def run_extra(pid, extra_id, size=None, overrides=None):
    """跑项目里现成的"附加产物"脚本（make_cmp.py / export_dxf_whole.py），返回它产出的文件。

    通裁（kind=params）的附加脚本吃 HANFU_PARAMS/HANFU_OUT：这里把当前夹具+旋钮传下去，
    并把 HANFU_OUT 指到 out/studio/<pid>_<size>/，产物落盘可复用。
    """
    spec = spec_of(pid)
    ws = ws_root()
    proj = os.path.join(ws, spec["project"])
    ex = next((e for e in spec.get("extras", []) if e["id"] == extra_id), None)
    if not ex:
        raise KeyError("这个版型没有产物：%s" % extra_id)
    script = os.path.join(proj, ex["script"])
    env = child_env()
    if spec["run"]["kind"] == "params" and size:
        params = dict(spec["run"]["fixtures"].get(size, {}))
        for k, v in (overrides or {}).items():
            params[k] = float(v)
        env["HANFU_PARAMS"] = json.dumps(params, ensure_ascii=False)
        env["HANFU_OUT"] = studio_out_dir("extras", "%s_%s" % (pid, str(size).replace("/", "-")))
        os.makedirs(env["HANFU_OUT"], exist_ok=True)
    r = _run([PY, script], cwd=os.path.dirname(script), env=env,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    if r.returncode != 0:
        log("extra.fail", pid=pid, extra=extra_id, rc=r.returncode,
            stderr=(r.stderr or "")[-600:])
        raise RuntimeError("脚本失败：%s" % (r.stderr or r.stdout)[-500:])
    files = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                j = json.loads(line)
                if j.get("png"):
                    files.append(j["png"])
            except Exception:
                pass
    log("extra.ok", pid=pid, extra=extra_id, size=size, files=len(files),
        out=r.stdout.strip().splitlines()[-1][:200] if (r.stdout or "").strip() else "")
    return dict(label=ex["label"], files=files, note=ex.get("note", ""))


def svg_to_png(svg, png, px=1200):
    """SVG → PNG（Edge 无头，按 viewBox 等比，白底）"""
    import re
    src = re.sub(r"<\?xml.*?\?>", "", svg, flags=re.S).strip()
    m = re.search(r'viewBox="\s*(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\s*"', src)
    if not m:
        raise ValueError("SVG 没有 viewBox")
    W, H = float(m.group(3)), float(m.group(4))
    w = px
    h = max(1, int(round(px * H / W)))
    src = re.sub(r'\swidth="[\d.]+mm"\sheight="[\d.]+mm"', ' width="%d" height="%d"' % (w, h), src, count=1)
    tmp = png + ".html"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write('<!doctype html><meta charset="utf-8">'
                 '<style>html,body{margin:0;background:#fff}svg{display:block}</style>' + src)
    try:
        _prof = os.path.join(tempfile.gettempdir(), "hanfu_edge_profile")   # 独立 profile，避免并发撞锁
        _run([find_edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--user-data-dir=" + _prof,
                        "--default-background-color=FFFFFFFF",
                        "--screenshot=" + os.path.abspath(png),
                        "--window-size=%d,%d" % (w, h),
                        "file:///" + os.path.abspath(tmp).replace("\\", "/")],
                       check=True, capture_output=True, timeout=180)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    from PIL import Image
    im = Image.open(png)
    if im.size != (w, h):
        im.resize((w, h), Image.LANCZOS).save(png)
    return png


if __name__ == "__main__":
    # 无界面自检：python adapters.py 深衣 V2 out.png
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("size")
    ap.add_argument("png")
    a = ap.parse_args()
    svg, meta = build_svg(a.pid, a.size)
    svg_to_png(svg, a.png)
    print(meta)
