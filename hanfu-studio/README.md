# hanfu-studio · 版型工作台（框架层）

**这里没有几何。** 它是壳：选型 → 参数 → 预览 → 排料 → 导出，出图一律调用各项目**已有的**
`pattern/*.py`。几何知识留在版型自己的程序里。

---

## 1 口径

裁法只有两种，名字固定为 **默认** 与 **古制**（旧文档里的"分裁/通裁"已全部改名）：

| | **默认** | **古制** |
|---|---|---|
| 版型是什么 | 一组裁片，每片一条闭合轮廓 | 一块布 ＋ 折叠序列（段 / 折线 / 剪口） |
| DXF | 每片一条轮廓 | **整衣一片**连续闭合外轮廓，折线剪口另设图层 |
| 图纸 | 裁片图（各片排开标尺寸） | 顺序图（材料→对折→剪开→压领→平铺） |
| 参数 | 号型 / 基准档 / 放量 ＋ 旋钮（在推导值上覆写） | 夹具 ＋ 旋钮 |
| 组件库里是 | **裁片**（piece） | **区块**（block，无独立裁片） |

两套底层逻辑不同，**不硬合并**：壳只认「脚本 ＋ 参数 ＋ 产物」。
选型树按 **项目 → 口径 → 版型** 分组。

### 三条父子契约

1. `kind=make`：`--sex {sex} --size {size} --out {out}`，可加 `--params <json>` / `--dump-params`；
2. `kind=params`：`HANFU_PARAMS` ＋ `HANFU_OUT` 环境变量；
3. 子程序回传 `<产物>.pieces.json`（轮廓 / 布纹 / 刀口 / 片名 / box），父程序据此排料与出 DXF。

### 裁片图统一出图口径

`sheet.write_sheet()`（母本 `ming-gaojiaoling/pattern/sheet.py`，各项目拷一份）：自动排版、
图层固定 `OUTLINE / NOTCH / MARK / AUX_PATH / GRAIN / DIM / LABEL / BLOCK / SCALE`、
带图签与 100mm 标尺。**不要手搓 polygon + 填充**（老版型陆续改成这套）。

---

## 2 四个核心功能（＝四层结构）

> **名称说明**：② 叫「图形化编剧参数**子程序**」，这个"子程序"指**本软件内部的功能模块**
> （负责把参数编成命令行）；与"版型子程序"（`hanfu-cad` 这些目录）**不是一回事**，不改名。

| 层 | 做什么 | 在哪 |
|---|---|---|
| ① 极简 SVG 预览 | **矢量**直画到 Canvas（不转 PNG）：滚轮缩放、拖拽平移、图层开关、点选组件高亮 | `svgview.py` |
| ② 图形化编剧参数子程序 | 参数滑杆＋数值框，改完即时重绘；旋钮统一走 `--params` 覆写到子程序推导值上，可一键重置 | `studio.py` 参数区 ＋ `adapters._args` |
| ③ 选型编辑组件库 | 版型树 → 号型 → 组件树（裁片/区块），点组件＝预览里高亮 | `studio.py` 左栏 ＋ `library/` |
| ④ 图形化父程序 | 顶栏「逆向 / 许愿 → 接口文件」「一键生成」，承载状态并交接给 harness（**通用全能**：逆向 / 复制 / 改动 / 增删查改 / 实验新版型 / 快速出图） | `studio.py` 顶栏 ＋ `adapters.py` |

**父程序的产出物是"程序"，不是图纸**（通用全能：输入不限，出口只有可下厂图纸）：
实物 / 官图 / 手绘 / 号型表 → 量图 → 版型程序；
一句话需求 → 判级（参数级 / 结构级 / 裁法级）→ 改夹具 / 派生程序 / 新谱系根；
已有版型 → 复制 / 改动 / 增删查改 → 新版型或新图。
判定与派生由 harness（AI 会话）执行，软件只承载状态、导出接口文件。

---

## 3 选型与参数

- 树：`项目（N）→ 口径（N）→ 版型 → 模式`。点模式节点＝直接切到那一档。
- **号型**：`kind=make` 按 `sex × size` 取；**模式**：make 档为说明性（如「本案」），
  params 档的模式就是夹具 id（V1/V2/V3）。
- **旋钮**：`patterns.json` 的 `knobs`，值域/步长/单位都在里面。滑杆基准由
  `adapters.probe_params()` 调子程序 `--dump-params` **现问**，父程序不另存尺码表。
- 改号型/模式/参数只重绘几何，**手工摆放保留**；切版型才清空布局。

---

## 4 预览与手工排料（只改摆放，不碰几何）

- **移动**：点中裁片拖动，轮廓与邻近的缝线/刀口/尺寸/文字一起走；空白处拖动＝平移画布。
- **新建 / 复制粘贴**：组件库下方「新建」输入 `宽×高`；`Ctrl+C / Ctrl+V` 副本偏移 40mm。
- **重置**：清掉所有移动、新建、复制。
- **归属**：SVG 里 `<片名>_ot` 是锚，其它层按最近裁片框归组；`BLOCK / SCALE` 与标题栏不动。
- **缝份**：净版 / 5 / 10 / 15 mm，用 shapely 做闭合轮廓外偏移（尖角斜接）。
- **导出排料**：「导出排料」→ `out/排料_<版型>_<号型>_<时间>/手工排料_*.dxf`；
  图层 `CUT_裁剪 / GRAIN_布纹 / NOTCH_刀口 / TEXT_文字 / DIM_标注`，选缝份时另有 `NET_净样`。
- **布局工程**：「保存 / 打开布局」→ `out/layouts/*.layout.json`，记录版型、号型、模式、参数、
  缝份、每个组件位移、新建/复制组件（含真实裁片定义）与图层可见性；打开时先恢复上下文再渲染。
- **边界**：排料 DXF 是"按当前版型程序几何排料"，不会把移动/新增写回版型程序的几何。
- **导出产物**：写 `out/exports/<版型>_<号型>/`，含子程序产物 ＋ 手工布局 SVG/PNG ＋ 排料 DXF。

---

## 5 组件库（studio 自有资产）

- 打开「共享库」自动收集**所有已注册项目**的组件：默认口径 → 项目裁片；古制 → 项目区块
  （上衣/裳·前/裳·后/领条 这类功能区块）。
- 目录缓存 `library/_project_catalog.json`，项目脚本 mtime 变化自动失效重建；项目默认组件**不能删**。
- **裁法隔离**：默认只与默认互通，古制只在古制内部互通；跨口径插入会被拒绝。
- **存 / 插**：「存入当前选中组件」→ `library/<id>/`（`component.json` + `versions/1.json` + `thumb.png`）；
  「插入到当前布局」＝**引用实例**（记 `library_id + version + source + kind`），可「断开引用」保留几何快照。
- **不做自动参数适配**：跨版型插入后按当前版型手动调整。
- 接口文件里多一个 `library` 字段，列出当前布局的库引用。

---

## 6 注册版型

左栏「注册版型」→ 填 **项目目录 + 脚本 + 运行方式**（+ 模式/号型或夹具）→「预检」逐条核对：

| 预检项 | 判据 |
|---|---|
| 项目目录 / 脚本存在 | 目录与脚本文件都在 |
| 脚本语法 | `py_compile` 可编译 |
| 运行方式 | `make` 或 `params` |
| argstyle 占位 | 只允许 `{sex} {size} {out} {profile} {ease}` |
| 模式 / 号型 | make：`sexes` 非空且 `sizes[sex]` 非空、argstyle 含 `{out}`；params：模式＝夹具键、号型＝夹具键 |
| id | 未被占用 |

**预检不过不写入**。写入＝`patterns.json` 加一条 `custom: true`（**只登记，不复制源码**）；
`adapters.unregister_pattern()` 可注销，内置版型拒绝注销。注册完立刻能走预览 / 一键生成 / 形制核对。

### 注册表从哪读（2026-11-09 修，别踩回去）

`adapters.registry_file()`：

- **源码运行** → 本目录 `patterns.json`；
- **打包（frozen）** → 从 exe 所在目录**往上找 5 级** `patterns.json`（命中 `<ws>/hanfu-studio/patterns.json`），
  找不到才退回随包 `_MEIPASS` 副本；
- `register / unregister` 同源；打包且只能写到 `_MEIPASS` 时**直接报错**（写进临时目录重启即丢）。

> 曾经的 bug：固定读 `HERE/patterns.json`。打包后 `HERE` 是解包临时目录，读的是**打包那一刻**的旧快照；
> 而 `projects.json` 是实时读的 → 新注册的版型查不到，被 `projects()` 静默过滤 → 项目显示成**空项目**。

---

## 7 项目管理（studio 可写）

- **内置项目**：由 `patterns.json` 按 `project` 字段派生，只读；「另存为」可复制成自建项目（只复制引用）。
- **自建项目**：登记在 `hanfu-studio/projects.json`（运行时状态，**不入库**，含本机路径），
  项目目录内有 `project.json` 清单。可新建（可勾初始版型）/ 重命名 / 更改目录（只改登记路径）/
  添加·移除版型 / 另存为 / 打开目录 / 删除。
- 项目**只组织已注册版型**，不复制/不生成源码；空项目在树里显示「空项目」。
- **删除**：先弹「确认文件」列出目录内全部将被删除的文件与总大小，勾选确认后才删；
  只删带匹配 `project.json` 的目录，受保护路径（workspace 根、`hanfu-studio`、各已注册项目目录）不删。
- 引用其他项目的版型源码不在项目目录里，删项目不动它们。

---

## 8 批量生成 / 一键生成

- **批量**：顶栏「批量生成」或 `python batch_cli.py all`。默认口径＝模式(基准) × 放量 × 号型；
  古制＝每个夹具一套。落到 `out/batch/<版型>/<模式_性别_号型>/`，内含
  `SVG / pieces.json / DXF（古制另含整衣 DXF）/ 尺码表（默认）/ 形制核对/` ＋ 顶层 `批量清单.md`。
- **一键**：`adapters.generate_all()` → 出图 → 落盘全套 → 返回清单。

---

## 9 CAD 协同（SVG / DXF 导入导出）

独立窗口，不改造版型程序，专门和外部 CAD 换图纸。

- **导入**：SVG 按 `<g id="图层">` 读入；DXF 走 `dxf_io.py`（ezdxf 子进程），读
  LWPOLYLINE/POLYLINE/SPLINE/ARC/CIRCLE/ELLIPSE/LINE/TEXT/MTEXT，INSERT 递归展开，
  按 `$INSUNITS` 折 mm，图层/颜色/文字保留，曲线按 0.5mm 采样。
- **修改**：拖拽移动整个图层、复制图层、删除＝删手工副本 / 隐藏原图层；隐藏图层不写出。
- **导出**：SVG 按图层写 `<g id="图层">`；DXF 写 LWPOLYLINE/LINE/CIRCLE/TEXT ＋ 旁挂 `.scene.json`。
- 默认落 `out/interop/`；GUI 进程不 import ezdxf，全交给 `dxf_io.py` 子进程。
- **边界**：第一版是图层级修改，还没有逐点改曲线与圆弧保真回写。

---

## 10 日志与自检

- **日志**：`logs/studio-YYYY-MM-DD.log`（打包后写 `%LOCALAPPDATA%\hanfu-studio\logs`）。
  每次出图/产物/导出/异常一行，脚本失败连 stderr 全文一起记；顶栏「日志」可直接打开。
- **自检**：`python selftest.py [版型id]` 走完所有版型 × 号型 × 产物，结果写进同一份日志。
- **打包版 CLI 自检**（都不开窗）：
  - `--check-library` → `out/library_check.txt`（首行 `OK components=N`）
  - `--check-projects` → `out/projects_check.txt`（首行 `OK projects=N`）
  - `--check-cad <x.dxf>` → `out/cad_check.txt`
  - `--batch <版型id>` → `out/batch/...`

---

## 11 目录

```
hanfu-studio/
  studio.py       tkinter 界面（左选型/号型/组件，中预览，右参数）
  adapters.py     适配层：调脚本出 SVG、注册表、项目、组件库、批量/一键（无几何）
  svgview.py      矢量预览 / 手工排料（移动、新建、复制粘贴）
  layout_dxf.py   排料 DXF 生成（ezdxf；缝份用 shapely，独立子进程）
  dxf_io.py       CAD 协同：DXF ↔ SVG / 场景 JSON（ezdxf 子进程）
  gates.py        形制核对（闸门）
  library/        组件库（每个组件一个目录；_project_catalog.json 是缓存）
  patterns.json   版型注册表（源）
  projects.json   自建项目登记（运行时生成，不入库）
  config.json     解释器与默认版型
  kit/            给 harness 的素材包
  build_exe.py    PyInstaller 打包
  selftest.py / batch_cli.py / shot.py
```

## 12 跑 / 打包

```bash
<python> studio.py            # 需要带 tkinter 的解释器
<python> build_exe.py         # → dist\hanfu-studio.exe（打包后自动备 runtime\）
```

exe 里不带几何，照样调用各项目 `pattern/*.py`，所以项目要留在原位（与 exe 同一仓）。
解释器顺序见 `adapters.python_exe()`：`HANFU_PY` → 随包 `runtime\` → `config.json` → 本机 venv → `sys.executable`。

> **重打包的坑**：PyInstaller 覆盖 `dist/hanfu-studio.exe` 时走 `os.remove`，会被沙箱 safe-delete 拦
> （`Some operations were aborted`），且 exe 正在运行时删不掉（可重命名不可删）。
> 做法：先 `mv dist/hanfu-studio.exe dist/_old.exe` 再打包。

## 13 接一个新版型

在 `patterns.json` 加一条（或走界面的「注册版型」）：

```json
{ "id": "...", "label": "...", "cut": "默认|古制",
  "project": "hanfu-xxx", "script": "pattern/make.py",
  "run": { "kind": "make|params", "argstyle": "--sex {sex} --size {size} --out {out}" },
  "sexes": ["—"], "sizes": { "—": ["本案"] },
  "modes": [ { "id": "case", "label": "本案", "note": "..." } ],
  "ease": ["合体"],
  "knobs": [ { "key": "NECK_W", "label": "开领宽", "min": 80, "max": 240, "step": 10, "unit": "mm" } ],
  "gates": { "fab_w": 600.0, "max_panels": 4, "min_radius": 10, "invariants": [], "reference": [] },
  "product": "...", "knob_note": "..." }
```

- `kind=make` 走号型；`kind=params` 走夹具 ＋ 旋钮。**两条都不用改脚本**——这是"迁移"而非"重做"的前提。
- `make` 也能挂旋钮：父程序把覆盖值拼成 `--params <json>`，子程序在"号型推导值"上覆写。
- 子程序侧只需要两件事：① 认 `--sex/--size/--out`（或环境变量）；② 回传 `.pieces.json`。
  建议照 `ming-gaojiaoling/pattern/make.py` 当模板，出图统一走 `sheet.write_sheet()`。
