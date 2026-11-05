# -*- coding: utf-8 -*-
"""hanfu-studio · 版型工作台（图形化父程序，tkinter 桌面程序，可打包 exe）

四层结构（用户 2026-11-02 定的路线）：
  ① 极简 SVG 预览   —— 直接矢量画，不转 PNG；滚轮缩放、拖拽平移、图层开关、点选组件
  ② 图形化编剧参数子程序 —— 参数滑杆+数值框，改完即时重绘；参数写回夹具(HANFU_PARAMS)
  ③ 选型编辑组件库 —— 版型树 → 号型/夹具 → 组件树（点组件＝预览里高亮）
  ④ 图形化父程序   —— 顶栏把「逆向入口」「许愿入口」摆出来：
       两个入口都面向 harness（AI 会话）做判级/量图/派生，软件负责
       **承载状态**（参数、夹具、组件、日志），并把需求/锚定表交接给 harness。

壳里没有几何：一切出图都走 adapters → 各项目现有的 build/make 脚本。
    python studio.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import adapters as A
from svgview import SvgView

# ── 配色：深色壳 + 浅画布（工具感）────────────────────────────────
CHROME, PANEL, PANEL2 = "#22252b", "#2a2e35", "#32373f"
LINE, INK, MUTE, ACCENT, OK, WARN = "#3d434c", "#e8eaed", "#9aa3ad", "#4c9aff", "#3fb950", "#e3b341"
FONT = ("Microsoft YaHei UI", 9)
FONT_B = ("Microsoft YaHei UI", 9, "bold")
FONT_T = ("Microsoft YaHei UI", 12, "bold")
FONT_S = ("Microsoft YaHei UI", 8)


def _btn(parent, text, cmd, accent=False, **kw):
    return tk.Button(parent, text=text, font=FONT_B, relief="flat", bd=0,
                     bg=(ACCENT if accent else PANEL2), fg=("#ffffff" if accent else INK),
                     activebackground=("#3a80e0" if accent else "#3d434c"),
                     activeforeground=("#ffffff" if accent else INK),
                     padx=10, pady=5, cursor="hand2", command=cmd, **kw)


class Studio(tk.Tk):
    def __init__(self):
        A.log("app.start", argv=" ".join(sys.argv), frozen=getattr(sys, "frozen", False),
              py=sys.executable, log=A.log_path())
        super().__init__()
        self.title("hanfu-studio · 手工编辑")
        self.geometry("1440x900")
        self.minsize(1100, 720)
        self.configure(bg=CHROME)
        self.spec = None
        self.size = None
        self.sex = None
        self.knobs = {}
        self.overrides = {}
        self.profile = None      # 分裁：基准档（artifact/vendor）
        self.ease = None        # 分裁：放量档
        self._debounce = None
        self._svg = ""
        self._layers = {}
        self._pieces = []
        self._canvas = None
        self._pending_layout = None
        self._loading = False
        self._ignore_tree = None
        self._lib_win = None
        self._lib_data = {}
        self._lib_img = None
        self._proj_win = None
        self._proj_data = {}
        self._cad_win = None
        self._iid_pid = {}
        self._iid_mode = {}
        self._render_dir = tempfile.mkdtemp(prefix="studio_view_")

        self._build_ui()
        self._fill_tree()
        self.after(120, self.select_first)

    # ───────────────────────── UI 骨架
    def _build_ui(self):
        # 顶栏
        bar = tk.Frame(self, bg=CHROME, height=46)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="hanfu-studio", font=FONT_T, bg=CHROME, fg=INK).pack(side="left", padx=14)
        tk.Label(bar, text="手工编辑", font=FONT_B, bg=CHROME, fg=ACCENT).pack(side="left", padx=(0, 10))
        self.crumb = tk.Label(bar, text="", font=FONT, bg=CHROME, fg=MUTE)
        self.crumb.pack(side="left", padx=(0, 12))

        _btn(bar, "逆向 / 许愿 → 接口文件", self.open_handoff, accent=True).pack(side="left", padx=3)
        tk.Frame(bar, bg=CHROME, width=12).pack(side="left")
        _btn(bar, "－", lambda: self.view.zoom(1 / 1.2)).pack(side="left", padx=1)
        _btn(bar, "适应", lambda: self.view.fit()).pack(side="left", padx=3)
        _btn(bar, "＋", lambda: self.view.zoom(1.2)).pack(side="left", padx=1)
        self.zoom_lbl = tk.Label(bar, text="100%", font=FONT_S, bg=CHROME, fg=MUTE, width=6)
        self.zoom_lbl.pack(side="left", padx=6)

        self.status = tk.Label(bar, text="就绪", font=FONT, bg=CHROME, fg=MUTE)
        self.status.pack(side="right", padx=14)
        _btn(bar, "批量生成", self.batch_all).pack(side="right", padx=3)
        _btn(bar, "一键生成", self.gen_all, accent=True).pack(side="right", padx=3)
        _btn(bar, "日志", self.open_log).pack(side="right", padx=3)
        _btn(bar, "打开目录", self.open_dir).pack(side="right", padx=3)
        _btn(bar, "导出产物", self.export).pack(side="right", padx=3)

        body = tk.Frame(self, bg=PANEL)
        body.pack(side="top", fill="both", expand=True)

        # 左：选型 → 号型 → 组件库
        left = tk.Frame(body, bg=PANEL, width=250)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._sec(left, "选型")
        proj_bar = tk.Frame(left, bg=PANEL)
        proj_bar.pack(fill="x", padx=8, pady=(0, 4))
        _btn(proj_bar, "项目管理", self.open_projects).pack(side="left")
        _btn(proj_bar, "新建项目", self.new_project).pack(side="left", padx=4)
        _btn(proj_bar, "CAD 协同", self.open_cad).pack(side="left", padx=(0, 4))
        _btn(proj_bar, "注册版型", self.open_register).pack(side="left")

        sel_box = tk.Frame(left, bg=PANEL)
        sel_box.pack(fill="x", padx=8, pady=(0, 6))
        self.tree = ttk.Treeview(sel_box, show="tree", selectmode="browse", height=7,
                                 style="Studio.Treeview")
        tsb = ttk.Scrollbar(sel_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree)
        self.tree.tag_configure("group", font=FONT_B, foreground=MUTE)
        self.tree.tag_configure("leaf", font=FONT, foreground=INK)
        self.tree.tag_configure("empty", font=FONT, foreground="#6b7380")
        self.tree.tag_configure("comp", font=FONT, foreground="#c8d2dc")

        self._sec(left, "模式（可复用）")
        # 模式区单独一个容器：控件直接建在容器里，显示/隐藏不串位
        self.mode_frame = tk.Frame(left, bg=PANEL)
        self.mode_frame.pack(fill="x")
        self.base_var = tk.StringVar()
        self.base_box = ttk.Combobox(self.mode_frame, textvariable=self.base_var, state="readonly",
                                    font=FONT, style="Studio.TCombobox")
        self.base_box.bind("<<ComboboxSelected>>", lambda e: self.on_mode())
        self.ease_var = tk.StringVar()
        self.ease_box = ttk.Combobox(self.mode_frame, textvariable=self.ease_var, state="readonly",
                                     font=FONT, style="Studio.TCombobox")
        self.ease_box.bind("<<ComboboxSelected>>", lambda e: self.on_mode())
        self.mode_note = tk.Label(self.mode_frame, text="", font=FONT_S, bg=PANEL, fg=MUTE,
                                  wraplength=222, justify="left")

        self._sec(left, "号型")
        self.size_var = tk.StringVar()
        self.size_box = ttk.Combobox(left, textvariable=self.size_var, state="readonly",
                                     font=FONT, style="Studio.TCombobox")
        self.size_box.pack(fill="x", padx=10)
        self.size_box.bind("<<ComboboxSelected>>", lambda e: self.on_size())
        self.sex_var = tk.StringVar()
        self.sex_box = ttk.Combobox(left, textvariable=self.sex_var, state="readonly",
                                    font=FONT, style="Studio.TCombobox")
        self.sex_box.pack(fill="x", padx=10, pady=(5, 0))
        self.sex_box.bind("<<ComboboxSelected>>", lambda e: self.on_sex())

        self._sec(left, "组件库")
        # 编辑/布局按钮先从底部占位，避免组件树展开后把它们挤出窗口
        edit_bar3 = tk.Frame(left, bg=PANEL)
        edit_bar3.pack(side="bottom", fill="x", padx=8, pady=(0, 10))
        _btn(edit_bar3, "导出排料", self.export_layout).pack(side="left", padx=(0, 6))
        tk.Label(edit_bar3, text="缝份", font=FONT_S, bg=PANEL, fg=MUTE).pack(side="left")
        self.seam_var = tk.StringVar(value="净版")
        self.seam_box = ttk.Combobox(edit_bar3, textvariable=self.seam_var, state="readonly",
                                     values=["净版", "5 mm", "10 mm", "15 mm"], width=7,
                                     font=FONT_S, style="Studio.TCombobox")
        self.seam_box.pack(side="left", padx=(3, 0))
        self.seam_box.bind("<<ComboboxSelected>>",
                           lambda e: A.log("ui.seam", mm=self.seam_mm()))

        edit_bar2 = tk.Frame(left, bg=PANEL)
        edit_bar2.pack(side="bottom", fill="x", padx=8, pady=(0, 3))
        for txt, cmd in (("保存布局", self.save_layout), ("打开布局", self.open_layout),
                         ("共享库", self.open_shared_library)):
            _btn(edit_bar2, txt, cmd).pack(side="left", padx=(0, 3))

        edit_bar = tk.Frame(left, bg=PANEL)
        edit_bar.pack(side="bottom", fill="x", padx=8, pady=(0, 3))
        for txt, cmd in (("新建", self.new_comp), ("复制", self.copy_comp),
                         ("粘贴", self.paste_comp), ("重置", self.reset_layout)):
            _btn(edit_bar, txt, cmd).pack(side="left", padx=(0, 3))

        comp_box = tk.Frame(left, bg=PANEL)
        comp_box.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.comp_tree = ttk.Treeview(comp_box, show="tree", selectmode="browse", height=8,
                                       style="Studio.Treeview")
        sb = ttk.Scrollbar(comp_box, orient="vertical", command=self.comp_tree.yview)
        self.comp_tree.configure(yscrollcommand=sb.set)
        self.comp_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.comp_tree.bind("<<TreeviewSelect>>", self.on_comp)
        self.comp_tree.tag_configure("comp", font=FONT, foreground="#c8d2dc")
        self.comp_tree.tag_configure("block", font=FONT_B, foreground=MUTE)

        self.bind_all("<Control-c>", lambda e: self._hotkey(self.copy_comp))
        self.bind_all("<Control-v>", lambda e: self._hotkey(self.paste_comp))

        # 右：参数 + 产物 + 图层
        right = tk.Frame(body, bg=PANEL, width=310)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._sec(right, "参数（改完即时重绘）")
        self.param_frame = tk.Frame(right, bg=PANEL)
        self.param_frame.pack(fill="both", expand=True, padx=8)
        self._sec(right, "产物")
        self.extra_var = tk.StringVar()
        self.extra_box = ttk.Combobox(right, textvariable=self.extra_var, state="disabled",
                                      font=FONT, style="Studio.TCombobox")
        self.extra_box.pack(fill="x", padx=10)
        self.extra_box.bind("<<ComboboxSelected>>", lambda e: self.on_extra())
        self.note = tk.Label(right, text="", font=FONT_S, bg=PANEL, fg=WARN, wraplength=280,
                              justify="left")
        self.note.pack(side="bottom", fill="x", padx=12, pady=10)

        # 中：矢量预览
        mid = tk.Frame(body, bg=PANEL)
        mid.pack(side="left", fill="both", expand=True)
        self.view = SvgView(mid)
        self.view.pack(fill="both", expand=True)
        self.view.on_pick(self.on_pick_view)
        self.view.on_scale(self._zoom_lbl)
        self.layer_frame = tk.Frame(mid, bg=PANEL)
        self.layer_frame.pack(fill="x", padx=10, pady=6)
        self.hint = tk.Label(mid, text="点组件选中 · 拖动移动 · 空白拖拽平移 · 滚轮缩放 · Ctrl+C/V 复制粘贴",
                             font=FONT_S, bg=PANEL, fg=MUTE)
        self.hint.pack(fill="x", padx=10, pady=(0, 6))

        self._style()

    def _sec(self, parent, text):
        tk.Label(parent, text=text, font=FONT_B, bg=PANEL, fg=MUTE).pack(
            anchor="w", padx=12, pady=(12, 4))

    def _style(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except Exception:
            pass
        st.configure("Studio.Treeview", background=PANEL, fieldbackground=PANEL,
                     foreground=INK, borderwidth=0, rowheight=22, font=FONT)
        st.configure("Studio.Treeview.Heading", background=PANEL, foreground=MUTE,
                     relief="flat", font=FONT_B)
        st.map("Studio.Treeview", background=[("selected", "#3a4350")],
               foreground=[("selected", "#ffffff")])
        st.configure("Studio.TCombobox", fieldbackground=PANEL2, background=PANEL2,
                     foreground=INK, arrowcolor=MUTE, borderwidth=0, padding=4)
        st.map("Studio.TCombobox", fieldbackground=[("readonly", PANEL2)],
               foreground=[("readonly", INK)])

    # ───────────────────────── 选型
    def _fill_tree(self, select_pid=None, select_project=None):
        old_iid = None
        sel = self.tree.selection()
        if sel:
            old_iid = sel[0]
        old_pid = self._iid_pid.get(old_iid) if old_iid else None
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._iid_pid = {}
        for proj in A.projects():
            pgid = "proj:" + str(proj["id"])
            self.tree.insert("", "end", iid=pgid, open=True, tags=("group",),
                             text="  %s（%d）" % (proj["name"], len(proj["patterns"])))
            if not proj["patterns"]:
                self.tree.insert(pgid, "end", text="    （空项目 · 可在项目管理里加版型）",
                                 tags=("empty",))
                continue
            by = {}
            for p in proj["patterns"]:
                by.setdefault(p["cut"], []).append(p)
            for cut, items in by.items():
                cgid = self.tree.insert(pgid, "end", open=True, tags=("group",),
                                        text="    %s（%d）" % (cut, len(items)))
                for p in items:
                    iid = "pat:%s:%s" % (proj["id"], p["id"])
                    self.tree.insert(cgid, "end", iid=iid, tags=("leaf",),
                                     text="      " + p["label"])
                    self._iid_pid[iid] = p["id"]
                    for m in (p.get("modes") or []):     # 模式也做成可选条目（点 V2 直接进 V2）
                        miid = "mode:%s:%s:%s" % (proj["id"], p["id"], m["id"])
                        self.tree.insert(iid, "end", iid=miid, tags=("modeleaf",),
                                         text="        · %s" % m["label"])
                        self._iid_pid[miid] = p["id"]
                        self._iid_mode[miid] = m["id"]
        target = None
        want = select_pid or old_pid
        if want:
            target = self._find_iid(want)
        if not target and select_project:
            for iid, pid in self._iid_pid.items():
                if iid.startswith("pat:%s:" % select_project):
                    target = iid
                    break
        if not target and self._iid_pid:
            target = next(iter(self._iid_pid))
        if target:
            self.tree.selection_set(target)
            self.tree.see(target)

    def _find_iid(self, pid):
        for iid, x in self._iid_pid.items():
            if x == pid:
                return iid
        return None

    def select_first(self):
        if self._iid_pid:
            iid = next(iter(self._iid_pid))
            self.tree.selection_set(iid)
            self.tree.see(iid)

    def _apply_pending_mode(self):
        """已选中同一版型时，只切模式并重绘。"""
        if not getattr(self, "_pending_mode", None) or not self.spec:
            return
        label = (self._mode_labels or {}).get(self._pending_mode)
        if not label:
            self._pending_mode = None
            return
        self.base_var.set(label)
        self._pending_mode = None
        self.on_mode()

    def on_tree(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        if self._ignore_tree == iid:
            self._ignore_tree = None
            return
        self._ignore_tree = None
        pid = self._iid_pid.get(iid)
        if pid:
            want_mode = self._iid_mode.get(iid)
            if want_mode:
                self._pending_mode = want_mode
            if self.spec and self.spec.get("id") == pid:
                if want_mode:
                    self._apply_pending_mode()
                return
            self._setup_pattern(pid)

    def _setup_pattern(self, pid):
        A.log("ui.select", pid=pid)
        if not self.spec or self.spec.get("id") != pid:
            self.view.reset_edits()
        self.spec = A.spec_of(pid)
        self.overrides = {}
        self.knobs = {}
        self.crumb.configure(text="%s ｜ %s" % (self.spec["label"], self.spec["cut"]))
        sexes = self.spec.get("sexes") or ["—"]
        self.sex = sexes[0]
        self.sex_var.set(self.sex)
        self.sex_box["state"] = "readonly" if len(sexes) > 1 else "disabled"
        self._fill_modes()
        self._load_sizes()
        self._fill_extras()
        self._build_params()

    def _fill_modes(self):
        spec = self.spec
        ms = spec.get("modes") or []
        self._mode_labels = dict((m["id"], m["label"]) for m in ms)   # 两种 kind 都要（通裁无下拉，但要点树）
        if spec.get("mode_kind") == "profile":
            self.base_box["values"] = [m["label"] for m in ms]
            pick = getattr(self, "_pending_mode", None)
            pick_label = self._mode_labels.get(pick) if pick else None
            self.base_var.set(pick_label or (ms[0]["label"] if ms else ""))
            self._pending_mode = None
            self.base_box.pack(fill="x", padx=10)
            self.ease_box["values"] = spec.get("ease") or []
            if spec.get("ease"):
                self.ease_var.set(spec["ease"][1] if len(spec["ease"]) > 1 else spec["ease"][0])
                self.ease_box.pack(fill="x", padx=10, pady=(5, 0))
            else:
                self.ease_box.pack_forget()
            self.profile = self._mode_id()
            self.ease = self.ease_var.get() if spec.get("ease") else None
            self.mode_note.pack(fill="x", padx=10, pady=(6, 0))
            self.mode_note.configure(text=self._mode_note())
        else:
            self.base_box.pack_forget()
            self.ease_box.pack_forget()
            self.profile = None
            self.ease = None
            # 通裁：模式不在下拉里，但 base_var 必须指向当前夹具，否则"点树上的 V3"落不到 V3
            pick = getattr(self, "_pending_mode", None)
            pick_label = self._mode_labels.get(pick) if pick else None
            if not pick_label and ms:
                pick_label = ms[0]["label"]
            self.base_var.set(pick_label or "")
            self._pending_mode = None
            self.mode_note.pack(fill="x", padx=10, pady=(6, 0))
            self.mode_note.configure(text=("模式：%s ｜ %s" % (pick_label, spec.get("mode_note", "")))
                                     if pick_label else spec.get("mode_note", ""))

    def _mode_id(self):
        ms = self.spec.get("modes") or []
        m = next((x for x in ms if x["label"] == self.base_var.get()), None)
        return m["id"] if m else None

    def _mode_note(self):
        ms = self.spec.get("modes") or []
        m = next((x for x in ms if x["label"] == self.base_var.get()), None)
        if not m:
            return ""
        return "%s：%s" % (m["label"], m.get("note", ""))

    def on_mode(self):
        if not self.spec:
            return
        mid = self._mode_id()
        if self.spec.get("mode_kind") == "fixture" and mid:      # 通裁：模式即号型
            sizes = (self.spec.get("sizes") or {}).get(self.sex) or []
            if mid in sizes:
                self.size = mid
                self.size_var.set(mid)
        self.profile = self._mode_id()
        self.ease = self.ease_var.get() or None
        self.mode_note.configure(text=self._mode_note())
        A.log("ui.mode", pid=self.spec["id"], profile=self.profile or "-", ease=self.ease or "-")
        if self.spec.get("mode_kind") == "fixture":
            self.overrides = {}          # 换夹具 = 换一整套参数，别把上一个夹具的覆盖带过去
            self._build_params()         # 滑杆要跟着夹具重建（否则 V3→V2 还显示 195）
        self.render()

    def _load_sizes(self):
        sizes = self.spec["sizes"][self.sex]
        self.size_box["values"] = sizes
        if self.spec["cut"] == "通裁":                 # 通裁：号型就是夹具 id → 跟当前模式保持一致
            want = self._mode_id() or (sizes[0] if sizes else "")
            self.size = want if want in sizes else (sizes[0] if sizes else "")
        else:
            self.size = sizes[len(sizes) // 2]
        self.size_var.set(self.size)

    def on_sex(self):
        if not self.spec:
            return
        self.sex = self.sex_var.get()
        self._load_sizes()
        self.render()

    def on_size(self):
        if not self.spec:
            return
        A.log("ui.size", pid=self.spec["id"], size=self.size_var.get())
        self.size = self.size_var.get()
        self.overrides = {}
        self._build_params()

    # ───────────────────────── 参数（图形化编剧参数子程序）
    def _build_params(self):
        for w in self.param_frame.winfo_children():
            w.destroy()
        self.knobs = {}
        knobs = self.spec.get("knobs") or []
        if not knobs:
            tk.Label(self.param_frame,
                     text="这个版型的参数由号型表决定（左侧选号型）。\n"
                          "几何与放码都在它自己的程序里。",
                     font=FONT, bg=PANEL, fg=MUTE, justify="left", wraplength=280
                     ).pack(anchor="w", pady=6)
            if not self._loading:
                self.render()
            return
        base = dict(self.spec["run"].get("fixtures", {}).get(self.size, {}))
        for k in knobs:
            var = tk.DoubleVar(value=base.get(k["key"], (k["min"] + k["max"]) / 2))
            self.knobs[k["key"]] = var
            box = tk.Frame(self.param_frame, bg=PANEL)
            box.pack(fill="x", pady=(8, 0))
            top = tk.Frame(box, bg=PANEL)
            top.pack(fill="x")
            tk.Label(top, text=k["label"], font=FONT, bg=PANEL, fg=MUTE).pack(side="left")
            ent = tk.Entry(top, textvariable=var, font=FONT, bg=PANEL2, fg=INK, bd=0,
                           width=8, justify="right", insertbackground=INK)
            ent.pack(side="right")
            ent.bind("<Return>", lambda e, key=k["key"]: self._on_param(key))
            ent.bind("<FocusOut>", lambda e, key=k["key"]: self._on_param(key))
            s = ttk.Scale(box, from_=k["min"], to=k["max"], variable=var,
                          command=lambda v, key=k["key"]: self._on_slider(key))
            s.pack(fill="x", pady=(2, 0))
        if not self._loading:
            self.render()

    def _on_slider(self, key):
        self._on_param(key, debounce=True)

    def _on_param(self, key, debounce=True):
        v = self.knobs.get(key)
        if v is None:
            return
        try:
            self.overrides[key] = float(v.get())
        except Exception:
            return
        if self._debounce:
            self.after_cancel(self._debounce)
        self._debounce = self.after(220, self.render) if debounce else self.render()

    # ───────────────────────── 渲染
    def render(self):
        if not self.spec:
            return
        pid, size, sex = self.spec["id"], self.size, self.sex
        over = dict(self.overrides)
        self.status.configure(text="生成中…")
        threading.Thread(target=self._work, args=(pid, size, sex, over), daemon=True).start()

    def _work(self, pid, size, sex, over):
        try:
            svg, meta = A.build_svg(pid, size, sex, over, profile=self.profile, ease=self.ease)
            self.after(0, lambda: self._show(svg, meta))
        except Exception as e:
            A.log_exc("ui.error", e, pid=pid, size=size)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._fail(msg))

    def _show(self, svg, meta):
        self._svg = svg
        self._pieces = meta.get("pieces") or []
        self._canvas = meta.get("canvas")
        self.view.set_piece_source(self._pieces)
        self.view.set_svg(svg)
        pending = self._pending_layout
        if (pending and pending.get("pid") == meta.get("pid")
                and pending.get("size") == meta.get("size")
                and pending.get("sex") == meta.get("sex")):
            layout = pending.get("layout") or {}
            self._pending_layout = None
            self.view.apply_layout(layout)
            A.log("ui.layout.applied", pid=meta.get("pid"), added=len(layout.get("added") or {}),
                  moved=len(layout.get("transforms") or {}))
        self._zoom_lbl()
        self._fill_components()
        self._fill_layers()
        self.status.configure(text="%s ｜ %s ｜ %d ms ｜ 裁片 %d"
                              % (meta.get("label"), meta.get("size"), meta.get("ms", 0),
                                 len(self._pieces)))
        A.log("ui.render", pid=meta.get("label"), size=meta.get("size"), ms=meta.get("ms"),
              pieces=len(self._pieces))

    def _zoom_lbl(self):
        self.zoom_lbl.configure(text="%d%%" % int(self.view.scale * 100))   # 1:1 = 100%

    def _fail(self, msg):
        A.log("ui.error", msg=msg)
        self.status.configure(text="出错")
        self.note.configure(text=msg[:300])

    # ───────────────────────── 组件库 / 图层
    def _fill_components(self, select=None):
        for i in self.comp_tree.get_children():
            self.comp_tree.delete(i)
        if not self.view.doc:
            return
        comps = self.view.components()
        refs = self.view.library_refs()
        ref_comps = set(r.get("component") for r in refs)
        if refs:
            rid = self.comp_tree.insert("", "end", text=" 共享库引用（%d）" % len(refs),
                                        open=True, iid="group:refs", tags=("block",))
            for r in refs:
                comp = r.get("component", "")
                libname = r.get("name") or r.get("library_id", "?")
                ver = r.get("version", "?")
                mark = "[区块] " if r.get("kind") == "block" else ""
                self.comp_tree.insert(rid, "end",
                                      text="  %s%s  ← %s v%s" % (mark, comp, libname, ver),
                                      iid="ref:" + comp, tags=("comp",))
        gid = self.comp_tree.insert("", "end", text=" 裁片（%d）" % len(comps), open=True,
                                   iid="group:pieces", tags=("block",))
        for c in comps:
            self.comp_tree.insert(gid, "end", text="  " + c, iid="comp:" + c, tags=("comp",))
        layers = self.view.layer_names()
        bid = self.comp_tree.insert("", "end", text=" 区块 / 图层（%d）" % len(layers),
                                    open=True, iid="group:layers", tags=("block",))
        for l in layers:
            self.comp_tree.insert(bid, "end", text=" " + (l or "未命名"),
                                  iid="layer:" + str(l), tags=("comp",))
        if select:
            target = ("ref:" + select) if select in ref_comps else ("comp:" + select)
            try:
                self.comp_tree.selection_set(target)
                self.comp_tree.see(target)
            except Exception:
                pass

    def on_comp(self, _evt=None):
        sel = self.comp_tree.selection()
        if not sel:
            return
        iid = sel[0]
        if iid.startswith("comp:"):
            self.view.select(iid[5:])
            A.log("ui.comp", name=iid[5:])
        elif iid.startswith("ref:"):
            self.view.select(iid[4:])
            A.log("ui.comp.ref", name=iid[4:])
        elif iid.startswith("layer:"):
            name = iid[6:]
            st = self.view.layer_state()
            self.view.set_layer(name, not st.get(name, True))
            A.log("ui.comp.layer", name=name)

    def on_pick_view(self, name):
        self._fill_components(select=name)

    # ── 手工编辑：新建 / 复制 / 粘贴 / 重置
    def _hotkey(self, fn):
        w = self.focus_get()
        if w is not None and w.winfo_class() in ("Entry", "TEntry", "Text",
                                                 "Spinbox", "TSpinbox", "TCombobox"):
            return None
        fn()
        return "break"

    def new_comp(self):
        if not self.view.doc:
            return
        raw = simpledialog.askstring("新建组件", "尺寸（宽×高，mm）：", initialvalue="420×300",
                                     parent=self)
        if not raw:
            return
        m = re.match(r"\s*(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)", raw)
        if not m:
            self.status.configure(text="尺寸格式应为 宽×高，例如 420×300")
            return
        name = self.view.add_component(float(m.group(1)), float(m.group(2)))
        self._fill_components(select=name)
        self.status.configure(text="已新建组件：%s（拖动可移动）" % name)
        A.log("ui.comp.new", name=name, w=m.group(1), h=m.group(2))

    def copy_comp(self):
        name = self.view.copy_selected()
        self.status.configure(text=("已复制组件：%s" % name) if name else "先在预览里选一个组件")

    def paste_comp(self):
        name = self.view.paste()
        if not name:
            self.status.configure(text="剪贴板里还没有组件（先选中后 Ctrl+C）")
            return
        self._fill_components(select=name)
        self.status.configure(text="已粘贴组件：%s" % name)
        A.log("ui.comp.paste", name=name)

    def reset_layout(self):
        if not self.view.doc:
            return
        if not self.view.has_edits():
            self.status.configure(text="当前没有手工改动")
            return
        if not messagebox.askyesno("重置布局", "清除所有移动、新建和复制的组件？", parent=self):
            return
        self.view.reset_edits()
        self._fill_components()
        self._fill_layers()
        self.status.configure(text="布局已重置")
        A.log("ui.comp.reset")

    # ── 注册版型：把"已有的版型程序"登记进来（不复制源码）
    def open_register(self):
        dlg = tk.Toplevel(self)
        dlg.title("注册版型 · 登记已有的版型程序")
        dlg.configure(bg=PANEL)
        dlg.geometry("760x700")
        tk.Label(dlg, text="注册版型（只登记，不复制源码）", font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=14, pady=(12, 2))
        tk.Label(dlg, text="填的是「项目目录 + 脚本 + 运行方式」三件事；预检不过不会写入。",
                 font=FONT_S, bg=PANEL, fg=MUTE).pack(anchor="w", padx=14)

        frm = tk.Frame(dlg, bg=PANEL); frm.pack(fill="x", padx=14, pady=8)
        def row(label, default="", width=46):
            r = tk.Frame(frm, bg=PANEL); r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=FONT, bg=PANEL, fg=MUTE, width=13, anchor="w").pack(side="left")
            e = tk.Entry(r, font=FONT, bg=PANEL2, fg=INK, bd=0, insertbackground=INK, width=width)
            e.insert(0, default); e.pack(side="left", fill="x", expand=True)
            return e
        ws = A.registry()["workspace"]
        projs = sorted([d for d in os.listdir(ws)
                        if os.path.isdir(os.path.join(ws, d)) and not d.startswith(".")])
        e_id = row("id（英文）", "my_pattern")
        e_label = row("名称", "我的版型")
        r0 = tk.Frame(frm, bg=PANEL); r0.pack(fill="x", pady=3)
        tk.Label(r0, text="裁法", font=FONT, bg=PANEL, fg=MUTE, width=13, anchor="w").pack(side="left")
        cut_var = tk.StringVar(value="分裁")
        ttk.Combobox(r0, textvariable=cut_var, values=["分裁", "通裁"], state="readonly",
                     font=FONT, style="Studio.TCombobox", width=10).pack(side="left")
        e_proj = row("项目目录", projs[0] if projs else "")
        e_script = row("脚本（相对项目）", "pattern/build.py")
        r1 = tk.Frame(frm, bg=PANEL); r1.pack(fill="x", pady=3)
        tk.Label(r1, text="运行方式", font=FONT, bg=PANEL, fg=MUTE, width=13, anchor="w").pack(side="left")
        kind_var = tk.StringVar(value="params")
        ttk.Combobox(r1, textvariable=kind_var, values=["params", "make"], state="readonly",
                     font=FONT, style="Studio.TCombobox", width=10).pack(side="left")
        tk.Label(r1, text="  params=夹具+旋钮；make=号型表（--sex/--size/--out）",
                 font=FONT_S, bg=PANEL, fg=MUTE).pack(side="left")
        e_style = row("argstyle", "--sex {sex} --size {size} --out {out}")

        tk.Label(dlg, text="模式（每行：id|名称|说明；params 时同时当夹具键）",
                 font=FONT_B, bg=PANEL, fg=MUTE).pack(anchor="w", padx=14, pady=(6, 2))
        t_modes = tk.Text(dlg, font=("Consolas", 9), bg=PANEL2, fg=INK, bd=0, height=4)
        t_modes.insert("1.0", "V1|原衣|对折线上下各一段")
        t_modes.pack(fill="x", padx=14)
        tk.Label(dlg, text="号型 / 夹具（params：每行 id|K=V,K=V；make：每行 性别|码1,码2）",
                 font=FONT_B, bg=PANEL, fg=MUTE).pack(anchor="w", padx=14, pady=(6, 2))
        t_sizes = tk.Text(dlg, font=("Consolas", 9), bg=PANEL2, fg=INK, bd=0, height=4)
        t_sizes.insert("1.0", "V1|HALF_L=624,SLIT_HALF=80")
        t_sizes.pack(fill="x", padx=14)
        out = tk.Text(dlg, font=("Consolas", 9), bg=PANEL2, fg=MUTE, bd=0, height=9)
        out.pack(fill="both", expand=True, padx=14, pady=8)

        def collect():
            modes = []
            for ln in t_modes.get("1.0", "end").strip().splitlines():
                if not ln.strip():
                    continue
                parts = [x.strip() for x in ln.split("|")]
                while len(parts) < 3:
                    parts.append("")
                modes.append(dict(id=parts[0], label=parts[1], note=parts[2]))
            kind = kind_var.get()
            run = dict(kind=kind, argstyle=e_style.get().strip())
            sexes, sizes, fixtures = [], {}, {}
            for ln in t_sizes.get("1.0", "end").strip().splitlines():
                if not ln.strip():
                    continue
                key, _, val = ln.partition("|")
                key, val = key.strip(), val.strip()
                if kind == "params":
                    fx = {}
                    for kv in val.split(","):
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            try:
                                fx[k.strip()] = float(v)
                            except ValueError:
                                pass
                    fixtures[key] = fx
                else:
                    sexes.append(key)
                    sizes[key] = [x.strip() for x in val.split(",") if x.strip()]
            if kind == "params":
                sexes = ["—"]
                sizes = {"—": [m["id"] for m in modes]}
                run["fixtures"] = fixtures
            rec = dict(id=e_id.get().strip(), label=e_label.get().strip(),
                       cut=cut_var.get(), project=e_proj.get().strip(),
                       script=e_script.get().strip(), run=run, sexes=sexes, sizes=sizes,
                       modes=modes, knobs=[])
            return rec

        def do_probe():
            rec = collect()
            out.delete("1.0", "end")
            for name, ok, detail in A.pattern_probe(rec):
                out.insert("end", "%s %-14s %s\n" % ("✓" if ok else "✗", name, detail))

        def do_register():
            rec = collect()
            try:
                A.register_pattern(rec)
            except Exception as e:
                out.insert("end", "\n注册失败：%s\n" % e)
                return
            out.insert("end", "\n已注册：%s（可注销）\n" % rec["id"])
            self._fill_tree()
            dlg.after(600, dlg.destroy)

        bw = tk.Frame(dlg, bg=PANEL); bw.pack(fill="x", padx=14, pady=(0, 12))
        _btn(bw, "预检", do_probe).pack(side="left")
        _btn(bw, "注册", do_register, accent=True).pack(side="left", padx=6)
        _btn(bw, "关闭", dlg.destroy).pack(side="left")
        A.log("ui.register.open")

    # ── 项目管理（内置只读；自建可建/改/删/加版型）
    def open_projects(self):
        if self._proj_win is not None and self._proj_win.winfo_exists():
            self._proj_win.lift()
            self._proj_win.focus_force()
            self._proj_refresh()
            return
        dlg = tk.Toplevel(self)
        dlg.title("项目管理 · studio")
        dlg.configure(bg=PANEL)
        dlg.geometry("940x560")
        self._proj_win = dlg
        tk.Label(dlg, text="项目管理", font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=16, pady=(12, 2))
        tk.Label(dlg, text="内置项目来自 patterns.json，只读；自建项目可建目录、加/移版型、重命名、换目录、删除。\n"
                            "项目只组织已注册的版型，不会复制版型源码；删除项目会连同项目目录一起删除（需确认）。",
                 font=FONT, bg=PANEL, fg=MUTE, justify="left").pack(anchor="w", padx=16)

        body = tk.Frame(dlg, bg=PANEL)
        body.pack(fill="both", expand=True, padx=16, pady=(8, 4))
        self.proj_tree = ttk.Treeview(body, columns=("name", "type", "folder", "count"),
                                      show="headings", selectmode="browse",
                                      style="Studio.Treeview")
        for col, label, width in (("name", "项目", 180), ("type", "类型", 90),
                                  ("folder", "目录", 420), ("count", "版型", 55)):
            self.proj_tree.heading(col, text=label)
            self.proj_tree.column(col, width=width, anchor="w")
        psb = ttk.Scrollbar(body, orient="vertical", command=self.proj_tree.yview)
        self.proj_tree.configure(yscrollcommand=psb.set)
        self.proj_tree.pack(side="left", fill="both", expand=True)
        psb.pack(side="left", fill="y")
        self.proj_tree.bind("<<TreeviewSelect>>", self._proj_on_select)

        self.proj_details = tk.Label(dlg, text="", font=FONT_S, bg=PANEL, fg=MUTE,
                                     justify="left", anchor="nw", wraplength=900)
        self.proj_details.pack(fill="x", padx=16, pady=(4, 4))

        b1 = tk.Frame(dlg, bg=PANEL)
        b1.pack(fill="x", padx=16, pady=(0, 3))
        _btn(b1, "新建项目", self.new_project, accent=True).pack(side="left")
        _btn(b1, "重命名", self._project_rename).pack(side="left", padx=6)
        _btn(b1, "更改目录", self._project_change_folder).pack(side="left", padx=6)
        _btn(b1, "另存为", self._project_duplicate).pack(side="left", padx=6)
        _btn(b1, "打开目录", self._project_open_folder).pack(side="right")
        b2 = tk.Frame(dlg, bg=PANEL)
        b2.pack(fill="x", padx=16, pady=(0, 12))
        _btn(b2, "添加版型", self._project_add_patterns).pack(side="left")
        _btn(b2, "移除版型", self._project_remove_patterns).pack(side="left", padx=6)
        _btn(b2, "删除项目", self._project_delete).pack(side="left", padx=6)
        _btn(b2, "刷新", self._proj_refresh).pack(side="right")
        self._proj_refresh()
        A.log("ui.projects.open")

    def _proj_alive(self):
        return self._proj_win is not None and self._proj_win.winfo_exists()

    def _proj_refresh(self):
        if not self._proj_alive():
            return
        sel = self.proj_tree.selection()
        keep = sel[0] if sel else None
        for iid in self.proj_tree.get_children():
            self.proj_tree.delete(iid)
        self._proj_data = {}
        nuser = 0
        for proj in A.projects():
            pid = proj["id"]
            if not proj.get("builtin"):
                nuser += 1
            self.proj_tree.insert("", "end", iid=pid, values=(
                proj.get("name", ""),
                "内置（只读）" if proj.get("builtin") else "自建",
                proj.get("folder", ""), len(proj.get("patterns") or [])))
            self._proj_data[pid] = proj
        if keep in self._proj_data:
            self.proj_tree.selection_set(keep)
        elif self._proj_data:
            first = next(iter(self._proj_data))
            self.proj_tree.selection_set(first)
        self._proj_on_select()

    def _proj_on_select(self, _evt=None):
        proj = self._proj_sel()
        if not proj:
            self.proj_details.configure(text="")
            return
        names = "、".join(p["label"] for p in (proj.get("patterns") or [])[:12]) or "（空项目）"
        if len(proj.get("patterns") or []) > 12:
            names += " …"
        mode = "内置项目只读，可用「另存为」创建自建项目" if proj.get("builtin") else "自建项目"
        self.proj_details.configure(
            text="%s（%s）\n目录：%s\n版型：%s\n备注：%s"
                 % (proj.get("name"), mode, proj.get("folder"),
                    names, proj.get("note") or "-"))

    def _proj_sel(self):
        if not self._proj_alive():
            return None
        sel = self.proj_tree.selection()
        return self._proj_data.get(sel[0]) if sel else None

    def _proj_require_user(self, proj):
        if proj and proj.get("builtin"):
            messagebox.showinfo("项目", "内置项目只读。可用「另存为」创建自建项目。",
                                parent=self._proj_win or self)
            return False
        return bool(proj)

    def new_project(self):
        parent = self._proj_win if self._proj_alive() else self
        dlg = tk.Toplevel(parent)
        dlg.title("新建项目")
        dlg.configure(bg=PANEL)
        dlg.geometry("640x360")
        tk.Label(dlg, text="新建项目", font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=16, pady=(12, 4))
        form = tk.Frame(dlg, bg=PANEL)
        form.pack(fill="x", padx=16)
        name_var = tk.StringVar()
        folder_var = tk.StringVar()
        note_var = tk.StringVar()
        picked = {"ids": []}

        def row(label, var, browse=False):
            r = tk.Frame(form, bg=PANEL)
            r.pack(fill="x", pady=4)
            tk.Label(r, text=label, font=FONT_S, bg=PANEL, fg=MUTE, width=8,
                     anchor="w").pack(side="left")
            ent = tk.Entry(r, textvariable=var, font=FONT, bg=PANEL2, fg=INK, bd=0,
                           insertbackground=INK)
            ent.pack(side="left", fill="x", expand=True, ipady=4)
            if browse:
                _btn(r, "浏览…", lambda: folder_var.set(
                    filedialog.askdirectory(parent=dlg, initialdir=folder_var.get() or
                                            A.registry()["workspace"]) or folder_var.get())
                     ).pack(side="left", padx=(6, 0))
            return ent

        row("项目名", name_var)
        row("目录", folder_var, browse=True)
        row("备注", note_var)
        tk.Label(form, text="目录留空＝workspace/<项目名>；项目只引用已注册版型，不复制源码。",
                 font=FONT_S, bg=PANEL, fg=MUTE, anchor="w").pack(fill="x", pady=(2, 6))
        praw = tk.Frame(form, bg=PANEL)
        praw.pack(fill="x", pady=(4, 0))
        plabel = tk.Label(praw, text="初始版型：未选择", font=FONT_S, bg=PANEL, fg=MUTE)
        plabel.pack(side="left")

        def choose_patterns():
            pats = A.registry()["patterns"]
            ids = self._pick_patterns("选择初始版型", pats, parent=dlg, preselected=picked["ids"])
            if ids is not None:
                picked["ids"] = ids
                plabel.configure(text="初始版型：已选 %d 个" % len(ids))

        _btn(praw, "选择版型…", choose_patterns).pack(side="right")

        def create():
            name = name_var.get().strip()
            if not name:
                messagebox.showinfo("新建项目", "项目名不能为空。", parent=dlg)
                return
            try:
                proj = A.project_create(name, folder_var.get().strip() or None,
                                        picked["ids"], note_var.get().strip())
            except Exception as e:
                messagebox.showerror("新建项目失败", "%s: %s" % (type(e).__name__, e),
                                     parent=dlg)
                return
            dlg.destroy()
            self.status.configure(text="已新建项目：%s" % proj["name"])
            self._after_projects_changed(select_project=proj["id"])
            A.log("ui.project.created", id=proj["id"], name=proj["name"])

        btns = tk.Frame(dlg, bg=PANEL)
        btns.pack(fill="x", padx=16, pady=12)
        _btn(btns, "创建", create, accent=True).pack(side="left")
        _btn(btns, "取消", dlg.destroy).pack(side="left", padx=6)

    def _pick_patterns(self, title, patterns, parent=None, preselected=None):
        """多选版型的小窗口；返回 id 列表，取消返回 None。"""
        parent = parent or (self._proj_win if self._proj_alive() else self)
        dlg = tk.Toplevel(parent)
        dlg.title(title)
        dlg.configure(bg=PANEL)
        dlg.geometry("640x520")
        tk.Label(dlg, text=title, font=FONT_B, bg=PANEL, fg=INK).pack(
            anchor="w", padx=14, pady=(10, 4))
        tk.Label(dlg, text="Ctrl/Shift 多选；项目只引用版型，不复制源码。",
                 font=FONT_S, bg=PANEL, fg=MUTE).pack(anchor="w", padx=14)
        box = tk.Frame(dlg, bg=PANEL)
        box.pack(fill="both", expand=True, padx=14, pady=8)
        lb = tk.Listbox(box, selectmode="extended", exportselection=False, font=FONT,
                        bg=PANEL2, fg=INK, bd=0, highlightthickness=0,
                        selectbackground="#3a4350", selectforeground="#ffffff")
        sb = ttk.Scrollbar(box, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        pre = set(preselected or [])
        ids = []
        for p in patterns:
            ids.append(p["id"])
            lb.insert("end", "%s ｜ %s / %s ｜ %s"
                      % (p["label"], p["project"], p["cut"], p["id"]))
            if p["id"] in pre:
                lb.selection_set("end")
        out = {"ids": None}

        def ok():
            out["ids"] = [ids[i] for i in lb.curselection()]
            dlg.destroy()

        btns = tk.Frame(dlg, bg=PANEL)
        btns.pack(fill="x", padx=14, pady=(0, 12))
        _btn(btns, "确定", ok, accent=True).pack(side="left")
        _btn(btns, "取消", dlg.destroy).pack(side="left", padx=6)
        self.wait_window(dlg)
        return out["ids"]

    def _after_projects_changed(self, select_project=None):
        if self._proj_alive():
            self._proj_refresh()
        self._fill_tree(select_project=select_project)

    def _project_rename(self):
        proj = self._proj_sel()
        if not self._proj_require_user(proj):
            return
        name = simpledialog.askstring("重命名项目", "新名称：", initialvalue=proj["name"],
                                       parent=self._proj_win)
        if not name:
            return
        try:
            A.project_update(proj["id"], name=name)
        except Exception as e:
            messagebox.showerror("重命名失败", "%s: %s" % (type(e).__name__, e),
                                 parent=self._proj_win)
            return
        self._after_projects_changed(select_project=proj["id"])

    def _project_change_folder(self):
        proj = self._proj_sel()
        if not self._proj_require_user(proj):
            return
        folder = filedialog.askdirectory(parent=self._proj_win,
                                          initialdir=proj.get("folder") or A.registry()["workspace"])
        if not folder:
            return
        try:
            A.project_update(proj["id"], folder=folder)
        except Exception as e:
            messagebox.showerror("更改目录失败", "%s: %s" % (type(e).__name__, e),
                                 parent=self._proj_win)
            return
        self.status.configure(text="项目目录已改为：%s（不会移动已有文件）" % folder)
        self._after_projects_changed(select_project=proj["id"])

    def _project_delete(self):
        proj = self._proj_sel()
        if not self._proj_require_user(proj):
            return
        try:
            info = A.project_delete_preview(proj["id"])
        except Exception as e:
            messagebox.showerror("删除项目", "%s: %s" % (type(e).__name__, e),
                                 parent=self._proj_win)
            return
        dlg = tk.Toplevel(self._proj_win)
        dlg.title("删除项目 · 确认文件")
        dlg.configure(bg=PANEL)
        dlg.geometry("820x620")
        dlg.transient(self._proj_win)
        tk.Label(dlg, text="删除项目：%s" % proj["name"], font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=16, pady=(12, 2))
        tk.Label(dlg, text="项目目录：%s" % info["folder"], font=FONT_S, bg=PANEL, fg=MUTE,
                 anchor="w").pack(fill="x", padx=16)
        if info["exists"] and info["safe"]:
            head = ("以下文件将被永久删除（整个项目目录）：")
        elif info["exists"]:
            head = ("目录不会删除（%s），本次只移除项目登记。目录内容如下：" % info["reason"])
        else:
            head = "项目目录不存在，本次只移除项目登记。"
        tk.Label(dlg, text=head, font=FONT, bg=PANEL,
                 fg=(WARN if not (info["exists"] and info["safe"]) else "#e06c75"),
                 justify="left", wraplength=780).pack(anchor="w", padx=16, pady=(6, 2))
        size_kb = info["size"] / 1024.0
        tk.Label(dlg, text="文件 %d 个 ｜ 目录 %d 个 ｜ 共 %.1f KB"
                           % (len(info["files"]), len(info["dirs"]), size_kb),
                 font=FONT_S, bg=PANEL, fg=MUTE).pack(anchor="w", padx=16, pady=(0, 4))
        box = tk.Frame(dlg, bg=PANEL)
        box.pack(fill="both", expand=True, padx=16, pady=4)
        txt = tk.Text(box, bg=PANEL2, fg=INK, bd=0, highlightthickness=0,
                      font=("Consolas", 9), wrap="none")
        ysb = ttk.Scrollbar(box, orient="vertical", command=txt.yview)
        xsb = ttk.Scrollbar(box, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        txt.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)
        lines = []
        if info["exists"]:
            lines.append("目录：" + info["folder"])
            lines.append("")
            lines.append(("将被删除的文件：" if info["safe"] else "目录内文件（不会删除）："))
            if info["files"]:
                lines.extend("  " + f for f in info["files"])
            else:
                lines.append("  （无文件）")
            if info["dirs"]:
                lines.append("")
                lines.append("子目录：")
                lines.extend("  " + d + os.sep for d in info["dirs"])
        else:
            lines.append("（目录不存在）")
        txt.insert("1.0", "\n".join(lines))
        txt.configure(state="disabled")

        var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            dlg, variable=var, bg=PANEL, fg=INK, selectcolor=PANEL2,
            activebackground=PANEL, activeforeground=INK, bd=0, highlightthickness=0,
            font=FONT, text=("我已确认以上文件将被永久删除" if info["safe"]
                             else "我已确认移除该项目登记"))
        chk.pack(anchor="w", padx=16, pady=(6, 2))

        btns = tk.Frame(dlg, bg=PANEL)
        btns.pack(fill="x", padx=16, pady=(4, 12))
        del_btn = _btn(btns, "永久删除" if info["safe"] else "移除登记", None, accent=True)
        del_btn.configure(command=lambda: do_delete())
        del_btn.pack(side="left")
        _btn(btns, "取消", dlg.destroy).pack(side="left", padx=6)
        del_btn.configure(state="disabled")
        chk.configure(command=lambda: del_btn.configure(
            state=("normal" if var.get() else "disabled")))

        def do_delete():
            if not var.get():
                return
            try:
                r = A.project_delete(proj["id"])
            except Exception as e:
                messagebox.showerror("删除失败", "%s: %s" % (type(e).__name__, e), parent=dlg)
                return
            dlg.destroy()
            self._after_projects_changed()
            if r.get("folder_deleted"):
                messagebox.showinfo("删除项目", "项目及目录已删除。", parent=self._proj_win)
            else:
                why = ("；目录未删除：" + r["reason"]) if r.get("reason") else ""
                messagebox.showinfo("删除项目", "项目登记已移除" + why, parent=self._proj_win)
            A.log("ui.project.deleted", id=proj["id"], folder_deleted=r.get("folder_deleted"),
                  files=len(info["files"]))

        dlg.grab_set()

    def _project_duplicate(self):
        proj = self._proj_sel()
        if not proj:
            return
        name = simpledialog.askstring("另存为项目", "新项目名：",
                                       initialvalue=proj["name"] + " 副本",
                                       parent=self._proj_win)
        if not name:
            return
        try:
            new = A.project_create(name, None, [p["id"] for p in proj["patterns"]],
                                   note="另存自 %s" % proj["name"])
        except Exception as e:
            messagebox.showerror("另存失败", "%s: %s" % (type(e).__name__, e),
                                 parent=self._proj_win)
            return
        self._after_projects_changed(select_project=new["id"])

    def _project_add_patterns(self):
        proj = self._proj_sel()
        if not self._proj_require_user(proj):
            return
        have = set(p["id"] for p in proj["patterns"])
        cand = [p for p in A.registry()["patterns"] if p["id"] not in have]
        if not cand:
            messagebox.showinfo("添加版型", "没有可添加的版型（已全部加入）。",
                                parent=self._proj_win)
            return
        ids = self._pick_patterns("添加版型", cand, parent=self._proj_win)
        if not ids:
            return
        A.project_add_patterns(proj["id"], ids)
        self._after_projects_changed(select_project=proj["id"])

    def _project_remove_patterns(self):
        proj = self._proj_sel()
        if not self._proj_require_user(proj):
            return
        if not proj["patterns"]:
            return
        ids = self._pick_patterns("移除版型", proj["patterns"], parent=self._proj_win)
        if not ids:
            return
        A.project_remove_patterns(proj["id"], ids)
        self._after_projects_changed(select_project=proj["id"])

    def _project_open_folder(self):
        proj = self._proj_sel()
        if not proj:
            return
        folder = proj.get("folder") or ""
        if not os.path.isdir(folder):
            messagebox.showinfo("打开目录", "目录不存在：%s" % folder, parent=self._proj_win)
            return
        try:
            os.startfile(folder)
        except Exception:
            pass

    # ── CAD 协同（SVG/DXF 导入导出，独立于版型程序）
    def open_cad(self):
        if self._cad_win is not None and self._cad_win.winfo_exists():
            self._cad_win.lift()
            self._cad_win.focus_force()
            return
        dlg = tk.Toplevel(self)
        dlg.title("CAD 协同 · studio")
        dlg.configure(bg=PANEL)
        dlg.geometry("1180x800")
        self._cad_win = dlg
        tk.Label(dlg, text="CAD 协同", font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=14, pady=(10, 2))
        tk.Label(dlg, text="导入 SVG/DXF（保留图层、mm）；拖拽移动图层，Ctrl+C/V 复制粘贴；"
                            "删除＝删手工副本/隐藏原图层；导出 SVG/DXF 与外部 CAD 协同。",
                 font=FONT, bg=PANEL, fg=MUTE, justify="left").pack(anchor="w", padx=14)
        bar = tk.Frame(dlg, bg=PANEL)
        bar.pack(fill="x", padx=14, pady=(8, 4))
        _btn(bar, "导入 SVG", self._cad_import_svg).pack(side="left")
        _btn(bar, "导入 DXF", self._cad_import_dxf).pack(side="left", padx=4)
        _btn(bar, "导出 SVG", self._cad_export_svg).pack(side="left", padx=4)
        _btn(bar, "导出 DXF", self._cad_export_dxf, accent=True).pack(side="left", padx=4)
        tk.Frame(bar, bg=PANEL, width=12).pack(side="left")
        _btn(bar, "复制", self._cad_copy).pack(side="left", padx=2)
        _btn(bar, "粘贴", self._cad_paste).pack(side="left", padx=2)
        _btn(bar, "删除/隐藏", self._cad_remove).pack(side="left", padx=2)
        _btn(bar, "适应", self._cad_fit).pack(side="left", padx=2)
        self.cad_zoom = tk.Label(bar, text="100%", font=FONT_S, bg=PANEL, fg=MUTE, width=6)
        self.cad_zoom.pack(side="right")

        self.cad_layer_frame = tk.Frame(dlg, bg=PANEL)
        self.cad_layer_frame.pack(fill="x", padx=14, pady=2)
        mid = tk.Frame(dlg, bg=PANEL)
        mid.pack(fill="both", expand=True, padx=14, pady=(4, 2))
        self.cad_view = SvgView(mid)
        self.cad_view.pack(fill="both", expand=True)
        self.cad_view.on_scale(self._cad_zoom)
        # 默认打开"当前预览的 SVG"（用户 2026-11-03）：省掉每次手工导入同一条链路
        _loaded = ""
        if getattr(self, "_svg", ""):
            try:
                if self.cad_view.load_external_svg(self._svg):
                    _loaded = "已载入当前预览%s" % (
                        "（%s %s）" % (self.spec["label"], self.size) if self.spec else "")
            except Exception as e:
                A.log("ui.cad.prefill_fail", err="%s: %s" % (type(e).__name__, e))
        self.cad_status = tk.Label(dlg, text=_loaded or "导入 SVG/DXF 开始。", font=FONT_S,
                                   bg=PANEL, fg=MUTE, anchor="w")
        self.cad_status.pack(fill="x", padx=14, pady=(0, 8))
        dlg.bind("<Control-c>", lambda e: self._cad_copy())
        dlg.bind("<Control-v>", lambda e: self._cad_paste())
        A.log("ui.cad.open")

    def _cad_alive(self):
        return self._cad_win is not None and self._cad_win.winfo_exists()

    def _cad_status(self, text):
        if self._cad_alive():
            self.cad_status.configure(text=text)

    def _cad_zoom(self):
        if self._cad_alive():
            self.cad_zoom.configure(text="%d%%" % int(self.cad_view.scale * 100))

    def _cad_fill_layers(self):
        if not self._cad_alive():
            return
        for w in self.cad_layer_frame.winfo_children():
            w.destroy()
        st = self.cad_view.layer_state()
        for layer in self.cad_view.layer_names()[:20]:
            var = tk.BooleanVar(value=st.get(layer, True))
            tk.Checkbutton(self.cad_layer_frame, text=layer, variable=var, font=FONT_S,
                           bg=PANEL, fg=MUTE, selectcolor=PANEL2, activebackground=PANEL,
                           activeforeground=INK, bd=0, highlightthickness=0,
                           command=lambda l=layer, v=var: self.cad_view.set_layer(l, v.get())
                           ).pack(side="left", padx=2)

    def _cad_after_load(self, name, meta=None):
        if not self._cad_alive():
            return
        self._cad_fill_layers()
        self.cad_view.fit()
        n = len(self.cad_view.components())
        extra = (" ｜ 实体 %s" % meta.get("entities")) if meta and meta.get("entities") else ""
        self._cad_status("已导入 %s ｜ 图层 %d%s" % (name, n, extra))

    def _cad_import_svg(self):
        if not self._cad_alive():
            return
        fn = filedialog.askopenfilename(parent=self._cad_win, title="导入 SVG",
                                         filetypes=[("SVG", "*.svg"), ("所有文件", "*.*")])
        if not fn:
            return
        try:
            with open(fn, encoding="utf-8") as fh:
                text = fh.read()
            if not self.cad_view.load_external_svg(text):
                raise ValueError("SVG 解析失败")
        except Exception as e:
            messagebox.showerror("导入 SVG", "%s: %s" % (type(e).__name__, e),
                                 parent=self._cad_win)
            return
        self._cad_after_load(os.path.basename(fn))
        A.log("ui.cad.import_svg", file=fn)

    def _cad_import_dxf(self):
        if not self._cad_alive():
            return
        fn = filedialog.askopenfilename(parent=self._cad_win, title="导入 DXF",
                                         filetypes=[("DXF", "*.dxf"), ("所有文件", "*.*")])
        if not fn:
            return
        self._cad_status("导入 DXF…")
        threading.Thread(target=self._cad_do_import_dxf, args=(fn,), daemon=True).start()

    def _cad_do_import_dxf(self, fn):
        try:
            svg, meta = A.import_dxf(fn)
            self.after(0, lambda: self._cad_loaded_dxf(svg, meta, os.path.basename(fn)))
        except Exception as e:
            A.log_exc("ui.cad.import_dxf_fail", e, file=fn)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._cad_fail(msg))

    def _cad_loaded_dxf(self, svg, meta, name):
        if not self._cad_alive():
            return
        if not self.cad_view.load_external_svg(svg):
            self._cad_fail("DXF 转换出的 SVG 解析失败")
            return
        self._cad_after_load(name, meta)
        A.log("ui.cad.import_dxf", file=name, entities=meta.get("entities"))

    def _cad_fail(self, msg):
        self._cad_status("失败：" + msg[:200])
        if self._cad_alive():
            messagebox.showerror("CAD 协同", msg, parent=self._cad_win)

    def _cad_export_svg(self):
        if not self._cad_alive() or not self.cad_view.doc:
            self._cad_status("先导入 SVG/DXF")
            return
        fn = filedialog.asksaveasfilename(
            parent=self._cad_win, title="导出 SVG", defaultextension=".svg",
            initialdir=A.studio_out_dir("interop"), initialfile="cad_export.svg",
            filetypes=[("SVG", "*.svg")])
        if not fn:
            return
        try:
            with open(fn, "w", encoding="utf-8") as fh:
                fh.write(self.cad_view.export_svg())
        except Exception as e:
            messagebox.showerror("导出 SVG", "%s: %s" % (type(e).__name__, e),
                                 parent=self._cad_win)
            return
        self._cad_status("已导出 SVG：" + os.path.basename(fn))
        A.log("ui.cad.export_svg", file=fn)

    def _cad_export_dxf(self):
        if not self._cad_alive() or not self.cad_view.doc:
            self._cad_status("先导入 SVG/DXF")
            return
        fn = filedialog.asksaveasfilename(
            parent=self._cad_win, title="导出 DXF", defaultextension=".dxf",
            initialdir=A.studio_out_dir("interop"), initialfile="cad_export.dxf",
            filetypes=[("DXF", "*.dxf")])
        if not fn:
            return
        scene = self.cad_view.scene_json()
        self._cad_status("导出 DXF…")
        threading.Thread(target=self._cad_do_export_dxf, args=(scene, fn), daemon=True).start()

    def _cad_do_export_dxf(self, scene, fn):
        try:
            meta = A.export_scene_dxf(scene, fn)
            self.after(0, lambda: self._cad_exported(meta))
        except Exception as e:
            A.log_exc("ui.cad.export_dxf_fail", e, file=fn)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._cad_fail(msg))

    def _cad_exported(self, meta):
        if not self._cad_alive():
            return
        self._cad_status("已导出 DXF：%s ｜ 实体 %s ｜ 图层 %s"
                         % (os.path.basename(meta["dxf"]), meta.get("entities"),
                            meta.get("layers")))
        A.log("ui.cad.export_dxf", file=meta["dxf"])

    def _cad_copy(self):
        name = self.cad_view.copy_selected()
        self._cad_status(("已复制图层：%s" % name) if name else "先点选一个图层/副本")

    def _cad_paste(self):
        name = self.cad_view.paste()
        if name:
            self._cad_fill_layers()
            self._cad_status("已粘贴：%s" % name)
        else:
            self._cad_status("剪贴板为空（先点选后 Ctrl+C）")

    def _cad_remove(self):
        r = self.cad_view.remove_selected()
        if r == "deleted":
            self._cad_fill_layers()
            self._cad_status("已删除手工副本")
        elif r == "hidden":
            self._cad_fill_layers()
            self._cad_status("已隐藏该原图层（导出时省略）")
        else:
            self._cad_status("先点选一个图层/副本")

    def _cad_fit(self):
        self.cad_view.fit()

    # ── 共享组件库（studio 内部资产，跨项目复用）
    def open_shared_library(self):
        if self._lib_win is not None and self._lib_win.winfo_exists():
            self._lib_win.lift()
            self._lib_win.focus_force()
            self._lib_refresh()
            return
        dlg = tk.Toplevel(self)
        dlg.title("共享组件库 · studio")
        dlg.configure(bg=PANEL)
        dlg.geometry("880x580")
        self._lib_win = dlg
        tk.Label(dlg, text="共享组件库", font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=16, pady=(12, 2))
        tk.Label(dlg, text="studio 内部资产：默认收录所有项目组件（分裁=裁片，通裁=区块）。\n"
                            "分裁组件只在分裁版型间互通；通裁组件只在通裁版型间互通。\n"
                            "插入＝引用实例（记录库 id + 版本）；「断开引用」后保留当前几何快照；不做自动参数适配。",
                 font=FONT, bg=PANEL, fg=MUTE, justify="left").pack(anchor="w", padx=16)

        sr = tk.Frame(dlg, bg=PANEL)
        sr.pack(fill="x", padx=16, pady=(8, 4))
        tk.Label(sr, text="搜索", font=FONT_S, bg=PANEL, fg=MUTE).pack(side="left")
        self.lib_search_var = tk.StringVar()
        ent = tk.Entry(sr, textvariable=self.lib_search_var, font=FONT, bg=PANEL2, fg=INK,
                       bd=0, insertbackground=INK)
        ent.pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=4)
        ent.bind("<KeyRelease>", lambda e: self._lib_refresh())
        self.lib_count = tk.Label(sr, text="", font=FONT_S, bg=PANEL, fg=MUTE)
        self.lib_count.pack(side="left", padx=(8, 0))

        body = tk.Frame(dlg, bg=PANEL)
        body.pack(fill="both", expand=True, padx=16, pady=4)
        left = tk.Frame(body, bg=PANEL)
        left.pack(side="left", fill="both", expand=True)
        self.lib_tree = ttk.Treeview(left, columns=("name", "source", "type", "ver"),
                                     show="headings", selectmode="browse",
                                     style="Studio.Treeview")
        for col, label, width in (("name", "组件", 140), ("source", "来源", 215),
                                  ("type", "类型", 70), ("ver", "版本", 48)):
            self.lib_tree.heading(col, text=label)
            self.lib_tree.column(col, width=width, anchor="w")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.lib_tree.yview)
        self.lib_tree.configure(yscrollcommand=sb.set)
        self.lib_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.lib_tree.bind("<<TreeviewSelect>>", self._lib_on_select)

        right = tk.Frame(body, bg=PANEL)
        right.pack(side="right", fill="y", padx=(10, 0))
        self.lib_canvas = tk.Canvas(right, width=280, height=190, bg="#f7f7f5",
                                    highlightthickness=0, bd=0)
        self.lib_canvas.pack(fill="x")
        self.lib_meta = tk.Label(right, text="", font=FONT_S, bg=PANEL, fg=MUTE,
                                 justify="left", wraplength=300, anchor="nw")
        self.lib_meta.pack(fill="both", expand=True, pady=(8, 0))

        btns = tk.Frame(dlg, bg=PANEL)
        btns.pack(fill="x", padx=16, pady=(4, 12))
        _btn(btns, "插入到当前布局", self._lib_insert, accent=True).pack(side="left")
        _btn(btns, "存入当前选中组件", self._lib_save_current).pack(side="left", padx=6)
        _btn(btns, "断开所选引用", self._lib_detach).pack(side="left", padx=6)
        _btn(btns, "删除组件", self._lib_delete).pack(side="left", padx=6)
        _btn(btns, "刷新", self._lib_refresh).pack(side="right")
        _btn(btns, "打开库目录", lambda: os.startfile(A.studio_library_dir())).pack(
            side="right", padx=6)
        self._lib_refresh()
        A.log("ui.library.open")
        if not A.project_catalog_cached():
            self.lib_count.configure(text="正在收集项目组件…")
            threading.Thread(target=self._do_catalog, daemon=True).start()

    def _do_catalog(self):
        try:
            A.project_catalog()
        except Exception as e:
            A.log_exc("ui.library.catalog_fail", e)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._lib_catalog_fail(msg))
            return
        self.after(0, self._lib_refresh)

    def _lib_catalog_fail(self, msg):
        if not self._lib_alive():
            return
        self.lib_count.configure(text="项目组件收集失败")
        self.lib_meta.configure(text="项目组件收集失败：\n" + msg[:500])

    def _lib_alive(self):
        return self._lib_win is not None and self._lib_win.winfo_exists()

    def _lib_refresh(self):
        if not self._lib_alive():
            return
        q = (self.lib_search_var.get() or "").strip().lower()
        for iid in self.lib_tree.get_children():
            self.lib_tree.delete(iid)
        self._lib_data = {}
        builtin = A.project_catalog_cached()
        custom = A.library_list()
        entries = [(c, True) for c in builtin] + [(c, False) for c in custom]
        nproj = len(builtin)
        ncustom = len(custom)
        shown = 0
        for comp, is_builtin in entries:
            src = comp.get("source") or {}
            source = "%s / %s" % (src.get("project", "-"),
                                  src.get("pattern_label") or src.get("pattern", "-"))
            mode = src.get("mode_label")
            if mode:
                source += " · " + mode
            if src.get("size") and src.get("size") != "—":
                source += " (%s)" % src["size"]
            kind = comp.get("kind", "piece")
            type_label = ("项目" if is_builtin else "自存") + (
                "裁片" if kind == "piece" else "区块")
            hay = ("%s %s %s %s" % (comp.get("name", ""), source, type_label,
                                    comp.get("id", ""))).lower()
            if q and q not in hay:
                continue
            cid = comp["id"]
            self.lib_tree.insert("", "end", iid=cid, values=(
                comp.get("name", ""), source, type_label,
                "v%s" % comp.get("version", "?")))
            self._lib_data[cid] = comp
            shown += 1
        self.lib_count.configure(text=("显示 %d（项目 %d / 自存 %d）" % (shown, nproj, ncustom))
                                 if q else ("项目 %d ｜ 自存 %d" % (nproj, ncustom)))
        self.lib_canvas.delete("all")
        self.lib_meta.configure(text="" if shown else
                                "还没有组件。项目组件正在收集，或先在预览里选中裁片存入共享库。")

    def _lib_on_select(self, _evt=None):
        sel = self.lib_tree.selection()
        if not sel:
            return
        comp = self._lib_data.get(sel[0])
        if not comp:
            return
        src = comp.get("source") or {}
        piece = comp.get("piece") or {}
        box = piece.get("box")
        kind = comp.get("kind", "piece")
        type_label = ("项目" if comp.get("builtin") else "自存") + (
            "裁片" if kind == "piece" else "区块")
        source = "%s / %s" % (src.get("project", "-"),
                              src.get("pattern_label") or src.get("pattern", "-"))
        if src.get("mode_label"):
            source += " · " + src["mode_label"]
        lines = ["%s  v%s ｜ %s" % (comp.get("name", ""), comp.get("version", "?"), type_label),
                 "来源：%s" % source,
                 "裁法：%s ｜ 号型：%s" % (src.get("cut", "-"), src.get("size", "-")),
                 "组件：%s ×%s" % (piece.get("name", "-"), piece.get("qty", 1))]
        if box:
            lines.append("尺寸：%.0f × %.0f mm" % (box[2] - box[0], box[3] - box[1]))
        if not comp.get("builtin"):
            lines.append("创建：%s" % comp.get("created", "-"))
        else:
            lines.append("创建：项目默认")
        lines.append("id：%s" % comp.get("id", "-"))
        self.lib_meta.configure(text="\n".join(lines))
        self._lib_draw(comp)

    def _lib_draw(self, comp):
        c = self.lib_canvas
        c.delete("all")
        pts = A.piece_outline(comp.get("piece") or {})
        if len(pts) < 2:
            c.create_text(140, 95, text="无几何", fill=MUTE, font=FONT_S)
            return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        bw, bh = max(x1 - x0, 1.0), max(y1 - y0, 1.0)
        s = min(264.0 / bw, 174.0 / bh)
        ox = (280.0 - bw * s) / 2.0 - x0 * s
        oy = (190.0 - bh * s) / 2.0 - y0 * s
        flat = [v for (x, y) in pts for v in (ox + x * s, oy + y * s)]
        c.create_line(flat, fill="#1a1a1a", width=1.2)

    def _lib_insert(self):
        sel = self.lib_tree.selection()
        comp = self._lib_data.get(sel[0]) if sel else None
        if not comp:
            self.status.configure(text="先在共享库里选一个组件")
            return
        if not self.spec or not self.view.doc:
            return
        src_cut = (comp.get("source") or {}).get("cut")
        if not src_cut:
            src_cut = "分裁" if comp.get("kind") == "piece" else "通裁"
        if self.spec["cut"] != src_cut:
            messagebox.showinfo("共享组件",
                                "分裁组件只和分裁互通；通裁组件只在通裁内部互通。\n"
                                "当前是%s版型，不能插入%s组件。" % (self.spec["cut"], src_cut),
                                parent=self._lib_win)
            return
        try:
            fresh = comp if comp.get("builtin") else A.library_get(comp["id"], comp.get("version"))
            kind = comp.get("kind", "piece")
            ref = dict(library_id=comp["id"], version=fresh.get("version", comp.get("version")),
                       name=comp.get("name", ""), source=comp.get("source") or {},
                       kind=kind, builtin=bool(comp.get("builtin")))
            name = self.view.insert_piece(fresh["piece"], fresh.get("name") or comp.get("name"),
                                          ref=ref, kind=kind)
        except Exception as e:
            A.log_exc("ui.library.insert_fail", e, id=comp.get("id"))
            messagebox.showerror("插入失败", "%s: %s" % (type(e).__name__, e),
                                 parent=self._lib_win)
            return
        self._fill_components(select=name)
        self._fill_layers()
        if kind == "block":
            self.status.configure(text="已插入项目区块：%s（通裁内部参考；整衣 DXF 仍由导出产物出）" % name)
        else:
            self.status.configure(text="已插入共享组件：%s（引用 %s v%s）"
                                  % (name, comp["id"], ref["version"]))
        A.log("ui.library.insert", id=comp["id"], version=ref["version"], component=name,
              kind=kind, cut=src_cut)

    def _lib_save_current(self):
        name = self.view.selected()
        if not name:
            msg = ("先在预览里点选一个裁片。" if self.spec and self.spec["cut"] == "分裁"
                   else "通裁没有可点选的独立裁片；项目区块已默认收录在共享库。")
            messagebox.showinfo("存入共享库", msg, parent=self._lib_win)
            return
        piece = self.view.piece_of(name)
        if not piece:
            messagebox.showinfo("存入共享库", "这个组件没有真实几何。", parent=self._lib_win)
            return
        source = dict(project=self.spec["project"], pattern=self.spec["id"],
                      pattern_label=self.spec["label"], cut=self.spec["cut"],
                      size=self.size, sex=self.sex,
                      profile=self.profile, ease=self.ease,
                      overrides=dict(self.overrides))
        kind = "piece" if self.spec["cut"] == "分裁" else "block"
        self.status.configure(text="存入共享库…")
        A.log("ui.library.save.start", name=name, pid=self.spec["id"], kind=kind)
        threading.Thread(target=self._do_lib_save,
                         args=(name, piece, source, kind), daemon=True).start()

    def _do_lib_save(self, name, piece, source, kind):
        try:
            comp = A.library_save(name, piece, source, kind=kind)
            self.after(0, lambda comp=comp: self._lib_saved(comp))
        except Exception as e:
            A.log_exc("ui.library.save_fail", e, name=name)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._fail(msg))

    def _lib_saved(self, comp):
        self.status.configure(text="已存入共享库：%s（%s）" % (comp["name"], comp["id"]))
        if self._lib_alive():
            self._lib_refresh()
            try:
                self.lib_tree.selection_set(comp["id"])
                self.lib_tree.see(comp["id"])
                self._lib_on_select()
            except Exception:
                pass
        A.log("ui.library.saved", id=comp["id"], name=comp["name"])

    def _lib_detach(self):
        name = self.view.selected()
        if not name:
            self.status.configure(text="先在预览里选中一个共享库组件")
            return
        if self.view.detach_component(name):
            self._fill_components(select=name)
            self._fill_layers()
            self.status.configure(text="已断开引用：%s（保留当前裁片快照）" % name)
            A.log("ui.library.detach", component=name)
        else:
            self.status.configure(text="当前选中的不是共享库引用")

    def _lib_delete(self):
        sel = self.lib_tree.selection()
        comp = self._lib_data.get(sel[0]) if sel else None
        if not comp:
            self.status.configure(text="先在共享库里选一个组件")
            return
        if comp.get("builtin"):
            messagebox.showinfo("项目组件",
                                "项目默认组件由组件目录自动生成，不能删除。\n"
                                "需要改动请复制/另存为自存组件。",
                                parent=self._lib_win)
            return
        cid = comp["id"]
        refs = [r for r in self.view.library_refs() if r.get("library_id") == cid]
        extra = ("\n\n当前布局有 %d 个引用；删除库文件不会删除布局里的裁片快照。" % len(refs)
                 if refs else "")
        if not messagebox.askyesno("删除共享组件",
                                   "从 studio 组件库永久删除「%s」？%s" % (comp.get("name"), extra),
                                   parent=self._lib_win):
            return
        try:
            A.library_delete(cid)
        except Exception as e:
            messagebox.showerror("删除失败", "%s: %s" % (type(e).__name__, e), parent=self._lib_win)
            return
        self._lib_refresh()
        self.status.configure(text="已删除共享组件：%s" % comp.get("name"))
        A.log("ui.library.deleted", id=cid)

    # ── 排料工程：保存 / 打开 / 出可裁 DXF
    def seam_mm(self):
        m = re.search(r"(\d+(?:\.\d+)?)", self.seam_var.get() if hasattr(self, "seam_var") else "")
        return float(m.group(1)) if m else 0.0

    def _layout_dir(self):
        return A.studio_out_dir("layouts")

    def _layout_context(self):
        return dict(pid=self.spec["id"], size=self.size, sex=self.sex,
                    profile=self.profile, ease=self.ease,
                    overrides=dict(self.overrides), seam=self.seam_mm())

    def save_layout(self):
        if not self.spec or not self.view.doc:
            return
        tag = "%s_%s" % (self.spec["id"], str(self.size).replace("/", "-"))
        fn = filedialog.asksaveasfilename(
            parent=self, title="保存布局工程", initialdir=self._layout_dir(),
            initialfile=tag + ".layout.json", defaultextension=".layout.json",
            filetypes=[("布局工程", "*.layout.json"), ("JSON", "*.json")])
        if not fn:
            return
        state = dict(schema="hanfu-studio/layout@1",
                     saved_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                     context=self._layout_context(),
                     layout=self.view.layout_state())
        with open(fn, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=1)
        self.status.configure(text="布局已保存：" + os.path.basename(fn))
        A.log("ui.layout.save", file=fn, pid=self.spec["id"], size=self.size)

    def open_layout(self):
        fn = filedialog.askopenfilename(
            parent=self, title="打开布局工程", initialdir=self._layout_dir(),
            filetypes=[("布局工程", "*.layout.json"), ("JSON", "*.json")])
        if not fn:
            return
        try:
            state = json.load(open(fn, encoding="utf-8"))
            self._load_layout(state)
            A.log("ui.layout.open", file=fn)
        except Exception as e:
            A.log_exc("ui.layout.open_fail", e, file=fn)
            messagebox.showerror("打开布局失败", "%s: %s" % (type(e).__name__, e), parent=self)

    def _load_layout(self, state):
        ctx = state.get("context") or {}
        pid = ctx.get("pid")
        known = [p["id"] for p in A.registry()["patterns"]]
        if pid not in known:
            raise ValueError("工程里的版型不存在：%s" % pid)
        self._loading = True
        try:
            self._setup_pattern(pid)
            iid = self._find_iid(pid)
            if iid:
                self._ignore_tree = iid
                self.tree.selection_set(iid)
            sex = ctx.get("sex")
            if sex in (self.spec.get("sexes") or []):
                self.sex = sex
                self.sex_var.set(sex)
            self._load_sizes()
            size = ctx.get("size")
            if size in (self.spec["sizes"].get(self.sex) or []):
                self.size = size
            self.size_var.set(self.size)
            if self.spec.get("mode_kind") == "profile":
                prof = ctx.get("profile")
                m = next((x for x in (self.spec.get("modes") or []) if x["id"] == prof), None)
                if m:
                    self.profile = prof
                    self.base_var.set(m["label"])
                ease = ctx.get("ease")
                if ease in (self.spec.get("ease") or []):
                    self.ease = ease
                    self.ease_var.set(ease)
                self.mode_note.configure(text=self._mode_note())
            self.overrides = dict(ctx.get("overrides") or {})
            self._build_params()
            for key, var in self.knobs.items():
                if key in self.overrides:
                    try:
                        var.set(float(self.overrides[key]))
                    except (TypeError, ValueError):
                        pass
            seam = float(ctx.get("seam") or 0)
            label = "净版" if seam <= 0 else ("%g mm" % seam)
            vals = list(self.seam_box["values"])
            if label not in vals:
                vals.append(label)
                self.seam_box["values"] = vals
            self.seam_var.set(label)
            self._pending_layout = dict(pid=pid, size=self.size, sex=self.sex,
                                        layout=state.get("layout") or {})
        finally:
            self._loading = False
        self.render()
        self.status.configure(text="正在恢复布局…")

    def export_layout(self):
        """按当前排料直接出一份可裁 DXF（不动子程序产物）。"""
        if not self.spec:
            return
        if self.spec["cut"] != "分裁":
            self.status.configure(text="通裁请用「导出产物」：整衣 DXF 已包含")
            return
        if not self._pieces:
            self.status.configure(text="还没有裁片几何（先等预览出图）")
            return
        A.log("ui.layoutdxf", pid=self.spec["id"], size=self.size, seam=self.seam_mm())
        self.status.configure(text="生成排料 DXF…")
        threading.Thread(target=self._do_export_layout,
                         args=(self.spec["id"], self.size, self.sex, dict(self.overrides),
                               self.profile, self.ease, list(self._pieces),
                               self.view.layout_state(), self._canvas, self.seam_mm()),
                         daemon=True).start()

    def _do_export_layout(self, pid, size, sex, over, prof, ease, pieces, layout, canvas, seam):
        try:
            r = A.export_layout_dxf(pid, size, sex, pieces=pieces, layout=layout,
                                    canvas=canvas, profile=prof, ease=ease, seam=seam)
            self.after(0, lambda r=r: self._layout_exported(r))
        except Exception as e:
            A.log_exc("ui.error", e, pid=pid, size=size, stage="layout_dxf")
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._fail(msg))

    def _layout_exported(self, r):
        self._last_dir = r["dir"]
        self.status.configure(text="排料 DXF 完成：%d 片 ｜ %s%s"
                              % (r["n"], os.path.basename(r["dxf"]),
                                 "（含缝份）" if r.get("seam") else "（净版）"))
        try:
            os.startfile(r["dir"])
        except Exception:
            pass

    def _fill_layers(self):
        for w in self.layer_frame.winfo_children():
            w.destroy()
        if not self.view.doc:
            return
        st = self.view.layer_state()
        for l in self.view.layer_names()[:14]:
            v = tk.BooleanVar(value=st.get(l, True))
            tk.Checkbutton(self.layer_frame, text=l, variable=v, font=FONT_S,
                           bg=PANEL, fg=MUTE, selectcolor=PANEL2, activebackground=PANEL,
                           activeforeground=INK, bd=0, highlightthickness=0,
                           command=lambda lay=l, var=v: self._toggle_layer(lay, var.get())
                           ).pack(side="left", padx=2)

    def _toggle_layer(self, layer, visible):
        self.view.set_layer(layer, visible)
        A.log("ui.layer", layer=layer, visible=visible)

    # ───────────────────────── 产物 / 导出
    def _fill_extras(self):
        ex = self.spec.get("extras") or []
        self._extras = ex
        if not ex:
            self.extra_box["values"] = ["—"]
            self.extra_var.set("—")
            self.extra_box.configure(state="disabled")
            return
        self.extra_box["values"] = ["当前配置"] + [e["label"] for e in ex]
        self.extra_var.set("当前配置")
        self.extra_box.configure(state="readonly")

    def on_extra(self):
        idx = self.extra_box.current()
        if idx <= 0:
            return
        ex = self._extras[idx - 1]
        self.status.configure(text="生成中（%s）…" % ex["label"])
        over = dict(self.overrides)
        threading.Thread(target=self._work_extra,
                         args=(self.spec["id"], ex["id"], self.size, over), daemon=True).start()

    def _work_extra(self, pid, eid, size, over):
        try:
            r = A.run_extra(pid, eid, size, over)
            if not r["files"]:
                raise RuntimeError("脚本没有产出图片")
            self.after(0, lambda: self._show_file(r["files"][0], r))
        except Exception as e:
            A.log_exc("ui.error", e, pid=pid, extra=eid)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._fail(msg))

    def _show_file(self, png, r):
        self.note.configure(text=r.get("note", ""))
        self.status.configure(text="%s ｜ %s" % (r["label"], os.path.basename(png)))
        try:
            os.startfile(png)
        except Exception:
            pass

    def batch_all(self):
        """批量生成：每个可复用模式各出一整套（成衣/裁片/DXF/闸门报告）。"""
        if not self.spec:
            return
        dlg = tk.Toplevel(self)
        dlg.title("批量生成 · 每个模式一整套")
        dlg.configure(bg=PANEL)
        dlg.geometry("520x260")
        tk.Label(dlg, text="批量生成 · %s" % self.spec["label"], font=FONT_T, bg=PANEL,
                 fg=INK).pack(anchor="w", padx=14, pady=(12, 2))
        plan = A.batch_plan(self.spec["id"])
        plan_all = A.batch_plan(self.spec["id"], all_sizes=True)
        tk.Label(dlg, text="每模式取中码：%d 组　｜　每模式全码：%d 组\n"
                           "每组产出：SVG + 裁片 JSON + DXF（通裁另含整衣 DXF）+ 形制核对"
                 % (len(plan), len(plan_all)), font=FONT, bg=PANEL, fg=MUTE, justify="left"
                 ).pack(anchor="w", padx=14)
        var = tk.IntVar(value=0)
        tk.Radiobutton(dlg, text="每模式取中码（快，%d 组）" % len(plan), variable=var, value=0,
                       font=FONT, bg=PANEL, fg=INK, selectcolor=PANEL2, activebackground=PANEL,
                       bd=0, highlightthickness=0).pack(anchor="w", padx=16, pady=(8, 0))
        tk.Radiobutton(dlg, text="每模式全码（慢，%d 组）" % len(plan_all), variable=var, value=1,
                       font=FONT, bg=PANEL, fg=INK, selectcolor=PANEL2, activebackground=PANEL,
                       bd=0, highlightthickness=0).pack(anchor="w", padx=16)
        def go():
            dlg.destroy()
            self.status.configure(text="批量生成中…")
            pid = self.spec["id"]
            threading.Thread(target=self._do_batch, args=(pid, bool(var.get())), daemon=True).start()
        _btn(dlg, "开始", go, accent=True).pack(anchor="w", padx=16, pady=14)

    def _do_batch(self, pid, all_sizes):
        try:
            r = A.generate_batch(pid, all_sizes=all_sizes)
            self.after(0, lambda: self._batched(r))
        except Exception as e:
            A.log_exc("ui.error", e, pid=pid)
            self.after(0, lambda: self._fail("%s: %s" % (type(e).__name__, e)))

    def _batched(self, r):
        self._last_dir = r["dir"]
        self.status.configure(text="批量完成：%d 组，成功 %d，失败 %d ｜ %s"
                             % (r["total"], r["ok"], r["total"] - r["ok"],
                                os.path.basename(r["dir"])))
        try:
            os.startfile(r["dir"])
        except Exception:
            pass
        if r["total"] - r["ok"]:
            self.note.configure(text="有失败项，见批量清单.md")

    def gen_all(self):
        """一键生成：出图 + 落盘全套产物（子程序按注册表接口跑，父程序只管调度）。"""
        if not self.spec:
            return
        A.log("ui.gen", pid=self.spec["id"], size=self.size)
        self.status.configure(text="一键生成中…")
        pid, size, sex = self.spec["id"], self.size, self.sex
        over = dict(self.overrides)
        prof, ease = self.profile, self.ease
        threading.Thread(target=self._do_gen, args=(pid, size, sex, over, prof, ease),
                         daemon=True).start()

    def _do_gen(self, pid, size, sex, over, prof, ease):
        try:
            r = A.generate_all(pid, size, sex, over, profile=prof, ease=ease)
            self.after(0, lambda: self._generated(r))
        except Exception as e:
            A.log_exc("ui.error", e, pid=pid, size=size)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._fail(msg))

    def _generated(self, r):
        self._last_dir = r["dir"]
        g = r.get("gates") or {}
        sm = g.get("summary") or {}
        self.status.configure(text="一键生成完成：%d 个文件%s ｜ 核对 通过 %s / 示意 %s"
                             % (len(r["files"]), "（含 DXF）" if r["dxf"] else "",
                                sm.get("pass_", "-"), sm.get("warn", "-")))
        if g:
            self._gate_dialog(r)
        try:
            os.startfile(r["dir"])
        except Exception:
            pass

    def _gate_dialog(self, r):
        """形制核对报告：失败只示意，不硬打回；人工确认写 signoff.json。"""
        g = r.get("gates") or {}
        dlg = tk.Toplevel(self)
        dlg.title("形制核对 · %s" % g.get("pid", ""))
        dlg.configure(bg=PANEL)
        dlg.geometry("880x560")
        sm = g.get("summary") or {}
        tk.Label(dlg, text="形制核对 ｜ %s ｜ %s" % (g.get("pid"), g.get("cls")),
                 font=FONT_T, bg=PANEL, fg=INK).pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(dlg, text="通过 %s ／ 示意 %s ／ 共 %s ｜ %s"
                           % (sm.get("pass_"), sm.get("warn"), sm.get("total"), g.get("policy", "")),
                 font=FONT_S, bg=PANEL, fg=MUTE, wraplength=840, justify="left").pack(
            anchor="w", padx=14)
        cols = ("status", "group", "name", "detail")
        tv = ttk.Treeview(dlg, columns=cols, show="headings", style="Studio.Treeview", height=16)
        for c, t, w in (("status", "结果", 60), ("group", "组", 100),
                        ("name", "检查项", 230), ("detail", "说明", 460)):
            tv.heading(c, text=t)
            tv.column(c, width=w, anchor="w")
        tv.tag_configure("PASS", foreground="#7fae7a")
        tv.tag_configure("WARN", foreground="#e3b341")
        for x in g.get("items", []):
            tv.insert("", "end", values=(x["status"], x["group"], x["name"], x["detail"]),
                      tags=(x["status"],))
        tv.pack(fill="both", expand=True, padx=14, pady=8)
        row = tk.Frame(dlg, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(0, 12))
        def do_sign():
            import gates as G
            fn = G.signoff(g.get("pid"), g.get("size"), g, by="user",
                           note="界面人工确认放行")
            self.status.configure(text="已签收：" + os.path.basename(fn))
            dlg.destroy()
        _btn(row, "人工确认放行（写 signoff.json）", do_sign, accent=True).pack(side="left")
        _btn(row, "打开核对目录", lambda: os.startfile(g.get("dir") or r["dir"])).pack(
            side="left", padx=6)
        _btn(row, "关闭", dlg.destroy).pack(side="left")

    def export(self):
        if not self.spec:
            return
        A.log("ui.export", pid=self.spec["id"], size=self.size)
        self.status.configure(text="导出中…")
        pid, size, sex = self.spec["id"], self.size, self.sex
        over = dict(self.overrides)
        layout = self.view.export_svg() if self.view.doc else ""
        state = self.view.layout_state()
        threading.Thread(target=self._do_export,
                         args=(pid, size, sex, over, layout, self.spec["cut"],
                               list(self._pieces), state, self._canvas, self.seam_mm()),
                         daemon=True).start()

    def _do_export(self, pid, size, sex, over, layout="", cut="", pieces=None,
                   layout_state=None, canvas=None, seam=0.0):
        try:
            r = A.export(pid, size, sex, over, profile=self.profile, ease=self.ease)
            if layout:
                tag = "%s_%s" % (pid, str(size).replace("/", "-"))
                svg = os.path.join(r["dir"], "手工布局_%s.svg" % tag)
                with open(svg, "w", encoding="utf-8") as fh:
                    fh.write(layout)
                png = svg[:-4] + ".png"
                try:
                    A.svg_to_png(layout, png, px=1400)
                except Exception as e:
                    A.log_exc("ui.export.layout_png", e, pid=pid, size=size)
                r["files"].extend([os.path.basename(svg), os.path.basename(png)])
                A.log("ui.export.layout", pid=pid, size=size, file=svg)
            if cut == "分裁" and pieces:
                try:
                    lr = A.export_layout_dxf(pid, size, sex, pieces=pieces, layout=layout_state,
                                             canvas=canvas, outdir=r["dir"],
                                             profile=self.profile, ease=self.ease, seam=seam)
                    r["files"].extend(lr["files"])
                    r["layout_dxf"] = lr["dxf"]
                except Exception as e:
                    A.log_exc("ui.export.layout_dxf", e, pid=pid, size=size)
                    r["layout_error"] = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda r=r: self._exported(r))
        except Exception as e:
            A.log_exc("ui.error", e, pid=pid, size=size)
            msg = "%s: %s" % (type(e).__name__, e)
            self.after(0, lambda msg=msg: self._fail(msg))

    def _exported(self, r):
        self._last_dir = r["dir"]
        self.status.configure(text="导出完成：%d 个文件%s%s"
                             % (len(r["files"]),
                                "（含 DXF）" if r["dxf"] else "",
                                "（含排料 DXF）" if r.get("layout_dxf") else "（含手工布局）"))
        if r.get("layout_error"):
            self.note.configure(text="排料 DXF 失败：%s" % r["layout_error"][:220])

    def open_dir(self):
        d = getattr(self, "_last_dir", None) or A.studio_out_dir()
        try:
            os.startfile(d)
        except Exception:
            pass

    def open_log(self):
        try:
            os.startfile(A.log_path())
        except Exception:
            pass

    # ───────────────────────── 入口（面向 harness）
    def open_handoff(self):
        """逆向 / 许愿 合并为一个入口：作用是**导出接口文件给 harness**。"""
        dlg = tk.Toplevel(self)
        dlg.title("逆向 / 许愿 → 导出接口文件给 harness")
        dlg.configure(bg=PANEL)
        dlg.geometry("680x560")
        # 置顶并聚焦：否则看起来"点了没反应"（窗口开在主窗后面）
        try:
            dlg.transient(self)
            dlg.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 680) // 2
            y = self.winfo_rooty() + 60
            dlg.geometry("+%d+%d" % (max(x, 0), max(y, 0)))
            dlg.lift()
            dlg.focus_force()
            dlg.attributes("-topmost", True)
            dlg.after(600, lambda: dlg.winfo_exists() and dlg.attributes("-topmost", False))
        except Exception as e:
            A.log("ui.handoff.lift_fail", err="%s: %s" % (type(e).__name__, e))
        tk.Label(dlg, text="逆向 / 许愿 → 接口文件", font=FONT_T, bg=PANEL, fg=INK).pack(
            anchor="w", padx=16, pady=(14, 2))
        tk.Label(dlg, text="这一层不做自动识别：量图、锚定、判级、派生都由 harness（AI 会话）完成。\n"
                            "这里做的只有一件事：把「版型 + 模式 + 参数 + 组件 + 闸门 + 约定」打包成接口文件交给 harness。",
                 font=FONT, bg=PANEL, fg=MUTE, justify="left").pack(anchor="w", padx=16)

        kind = tk.StringVar(value="reverse")
        row = tk.Frame(dlg, bg=PANEL); row.pack(fill="x", padx=16, pady=(10, 4))
        for val, txt in (("reverse", "逆向：实物/官图 → 版型程序"), ("wish", "许愿：一句话需求 → 版型程序")):
            tk.Radiobutton(row, text=txt, variable=kind, value=val, font=FONT, bg=PANEL,
                           fg=INK, selectcolor=PANEL2, activebackground=PANEL,
                           activeforeground=INK, bd=0, highlightthickness=0
                           ).pack(side="left", padx=(0, 16))

        tk.Label(dlg, text="需求 / 官图路径", font=FONT_B, bg=PANEL, fg=MUTE).pack(
            anchor="w", padx=16, pady=(8, 2))
        self.h_text = tk.Text(dlg, font=FONT, bg=PANEL2, fg=INK, bd=0, height=6,
                              insertbackground=INK)
        self.h_text.pack(fill="both", expand=True, padx=16)

        info = tk.Frame(dlg, bg=PANEL); info.pack(fill="x", padx=16, pady=8)
        self.h_info = tk.Label(info, text="", font=FONT_S, bg=PANEL, fg=MUTE, justify="left",
                               wraplength=640)
        self.h_info.pack(anchor="w")
        self._refresh_handoff_info()

        btns = tk.Frame(dlg, bg=PANEL); btns.pack(fill="x", padx=16, pady=(4, 12))
        _btn(btns, "导出接口文件给 harness", self._handoff_export, accent=True).pack(side="left")
        _btn(btns, "复制当前参数", self._reverse_copy).pack(side="left", padx=6)
        A.log("ui.handoff.open", pid=self.spec["id"] if self.spec else "-")

    def _refresh_handoff_info(self):
        spec = self.spec
        if not spec:
            self.h_info.configure(text="")
            return
        modes = "、".join("%s(%s)" % (m["label"], m["id"]) for m in (spec.get("modes") or []))
        ncomp = len(self.view.components()) if self.view.doc else 0
        nref = len(self.view.library_refs()) if self.view.doc else 0
        self.h_info.configure(text="将打包：版型 %s ｜ 模式 %s ｜ 号型 %s ｜ 参数 %d 个 ｜ 组件 %d 个（库引用 %d） ｜ 产物 %d 项 ｜ 闸门 4 道"
                                % (spec["label"], modes or "-", self.size or "-",
                                   len(self.overrides), ncomp, nref,
                                   len(spec.get("extras") or [])))

    def _handoff_export(self):
        txt = self.h_text.get("1.0", "end").strip()
        kind = "reverse" if txt.startswith("逆向") else "wish"
        try:
            fn = A.interface_file(kind, request=txt,
                                   artifact_path=txt if kind == "reverse" else "",
                                   pid=self.spec["id"] if self.spec else None,
                                   size=self.size, sex=self.sex,
                                   overrides=dict(self.overrides),
                                   components=(self.view.components()
                                               if self.view.doc else []),
                                   library=(self.view.library_refs()
                                            if self.view.doc else []))
        except Exception as e:
            self.note.configure(text="导出接口文件失败：%s" % e)
            return
        self.clipboard_clear()
        self.clipboard_append(fn)
        self.status.configure(text="接口文件已导出：" + os.path.basename(fn))
        A.log("ui.handoff.done", file=fn)

    def _reverse_copy(self):
        cur = dict(self.spec["run"].get("fixtures", {}).get(self.size, {}))
        cur.update(self.overrides)
        self.clipboard_clear()
        self.clipboard_append(json.dumps(cur, ensure_ascii=False, indent=1))
        self.status.configure(text="当前参数已复制到剪贴板（可交给 harness）")


def _cli_check_library():
    """打包版无界面自检：确认项目组件目录可读/可生成，结果写 out/library_check.txt。"""
    try:
        cat = A.project_catalog_cached() or A.project_catalog()
        lines = ["OK components=%d" % len(cat)]
        for c in cat:
            s = c.get("source") or {}
            lines.append("%s\t%s\t%s\t%s" % (c.get("name"), s.get("pattern"),
                                             c.get("kind"), s.get("size")))
        text = "\n".join(lines)
    except Exception as e:
        text = "FAIL %s: %s" % (type(e).__name__, e)
    fn = os.path.join(A.studio_out_dir(), "library_check.txt")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    A.log("cli.library_check", file=fn, ok=text.startswith("OK"))
    return 0 if text.startswith("OK") else 1


def _cli_check_projects():
    """打包版无界面自检：确认项目登记可读。"""
    try:
        ps = A.projects()
        lines = ["OK projects=%d" % len(ps)]
        for p in ps:
            lines.append("%s\t%s\t%s\t%d"
                         % (p.get("name"), "builtin" if p.get("builtin") else "user",
                            p.get("folder"), len(p.get("patterns") or [])))
        text = "\n".join(lines)
    except Exception as e:
        text = "FAIL %s: %s" % (type(e).__name__, e)
    fn = os.path.join(A.studio_out_dir(), "projects_check.txt")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    A.log("cli.projects_check", file=fn, ok=text.startswith("OK"))
    return 0 if text.startswith("OK") else 1


def _cli_check_cad(path):
    """打包版 CAD 协同自检：DXF 导入 + 场景导出 DXF。"""
    dbg = ("interpreter=%s\nsys.executable=%s\nscript=%s\n"
           % (A.PY, sys.executable, A.resource_path("dxf_io.py")))
    try:
        svg, meta = A.import_dxf(path)
        outdir = A.studio_out_dir("interop")
        with open(os.path.join(outdir, "cad_check.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        scene = dict(units="mm", viewBox=[0, 0, 100, 100], transforms={},
                     items=[dict(layer="0", comp=None, kind="line",
                                 data=[[10, 10], [90, 90]],
                                 style={"stroke": "#1a1a1a"})])
        em = A.export_scene_dxf(scene, os.path.join(outdir, "cad_check.dxf"))
        text = ("OK import_entities=%s import_layers=%s export_entities=%s\n"
                % (meta.get("entities"), meta.get("layers"), em.get("entities")))
    except Exception as e:
        text = "FAIL %s: %s\n" % (type(e).__name__, e)
    text += dbg
    fn = os.path.join(A.studio_out_dir(), "cad_check.txt")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(text)
    A.log("cli.cad_check", file=fn, ok=text.startswith("OK"))
    return 0 if text.startswith("OK") else 1


if __name__ == "__main__":
    # windowed 打包（PyInstaller --windowed）里 sys.stdout/stderr 是 None，
    # 任何 print / traceback 都会抛 AttributeError 并被 Tk 吞掉（表现＝点了没反应）。
    if sys.stdout is None or sys.stderr is None:
        _dn = open(os.devnull, "w", encoding="utf-8")
        sys.stdout = sys.stdout or _dn
        sys.stderr = sys.stderr or _dn
    if "--check-library" in sys.argv:
        sys.exit(_cli_check_library())
    if "--check-projects" in sys.argv:
        sys.exit(_cli_check_projects())
    if "--batch" in sys.argv:
        i = sys.argv.index("--batch")
        pid = sys.argv[i + 1] if len(sys.argv) > i + 1 else "shenyi"
        r = A.generate_batch(pid, all_sizes=("--all" in sys.argv))
        print("%s：%d 组，成功 %d ｜ %s" % (pid, r["total"], r["ok"], r["dir"]))
        sys.exit(0 if r["ok"] == r["total"] else 1)
    if "--check-cad" in sys.argv:
        i = sys.argv.index("--check-cad")
        sample = sys.argv[i + 1] if len(sys.argv) > i + 1 else ""
        sys.exit(_cli_check_cad(sample))
    if "--check-handoff" in sys.argv:
        # 无界面自检：接口文件能否生成（打包版也能跑，用来判断"点了没反应"是前端还是后端）
        try:
            fn = A.interface_file("wish", request="自检", pid="shenyi", size="V3", overrides={})
            text = "OK " + fn
        except Exception as e:
            text = "FAIL %s: %s" % (type(e).__name__, e)
        try:                                  # windowed 版没有控制台，结果落到文件里
            out = A.studio_out_dir()
            with open(os.path.join(out, "handoff_check.txt"), "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            text += "（已写 %s/handoff_check.txt）" % out
        except Exception:
            pass
        print(text)
        sys.exit(0 if text.startswith("OK") else 1)
    app = Studio()
    if "--handoff" in sys.argv:          # 排障用：启动即打开该面板（便于截图确认）
        app.after(1500, app.open_handoff)
    app.mainloop()
