# 汉服 CAD · 单仓（父程序 + 六个子程序 + 一个试验版型 + 一份 AI 素材包）

**通用全能，最适合快速上手的汉服开发工具**：逆向 / 复制 / 改动 / 增删查改 / 实验新版型 / 快速出图都可以；
输入不限（实物照片 / 官图 / 手绘 / 号型表 / 一句话需求 / 已有版型），出口只有一种——可下厂的净版图纸。

一个仓装三样东西：**父程序（壳）**、**子程序（版型程序）**、**给 harness 的素材包**。

| 目录 | 角色 | 一句话 |
|---|---|---|
| **`hanfu-studio/`** | **父程序** | 图形化版型工作台：选型 / 参数 / 预览 / 手工排料 / 组件库 / 注册 / CAD 协同。**不含几何**，出图一律调子程序的脚本；内含 `kit/`（素材包） |
| `hanfu-cad/` | 子程序 | **对穿交半臂**（钱樟墓夹袄，11 码） |
| `hanfu-jiexiu/` | 子程序 | **对穿交接袖**（长袖，男装 5 码） |
| `hanfu-shenyi/` | 子程序 | **深衣** V2 宽袖 / V3 窄袖 ＋ **原始直领交襟衣** V1 |
| `ming-gaojiaoling/` | 子程序 | **明制高交领**（用户手绘标准图，单号「本案」） |
| `tang-yuanling/` | 子程序 | **唐圆领**（逐步绘图定稿，单号「本案」） |
| `hanfu-zhidui/` | 子程序 | **直领对襟**（以半臂后片为底，照原始直领的口径开领装领，单号「本案」） |
| `shiyan-shuling/` | 试验版型（已注册） | **试验竖领浅交襟**（以厂商基准半臂为底逐步构造；领条＝**一条带状**，三段沿共边相接、两端分开首尾不接，不自交；单号「本案」） |

## 口径

裁法只有两种，名字就是这两个词：

| 口径 | 版型是什么 | DXF | 图纸 |
|---|---|---|---|
| **默认** | 一组裁片，每片一条闭合轮廓 | 每片一条轮廓 | 裁片图（各片排开标尺寸） |
| **古制** | 一块布 ＋ 折叠序列（段 / 折线 / 剪口） | **整衣一片**连续闭合外轮廓，折线剪口另设图层 | 顺序图（材料 → 对折 → 剪开 → 压领 → 平铺） |

两套底层逻辑不同，**不硬合并**：几何留在各自项目里，壳只认「脚本 ＋ 参数 ＋ 产物」。

已注册版型（`hanfu-studio/patterns.json`，共 8 个）：

| id | 口径 | 项目 | 脚本 | 号型 |
|---|---|---|---|---|
| `banbi` | 默认 | `hanfu-cad` | `pattern/make.py` | 女 XS–2XL ／ 男 S–2XL |
| `jiexiu` | 默认 | `hanfu-jiexiu` | `pattern/make.py` | 男装 5 码 |
| `shenyi` | 古制 | `hanfu-shenyi` | `pattern/build_shenyi.py` | V2 / V3 |
| `zhiling` | 古制 | `hanfu-shenyi` | `pattern/build.py` | V1 |
| `minggaojiaoling` | 默认 | `ming-gaojiaoling` | `pattern/make.py` | 本案 |
| `tangyuanling` | 默认 | `tang-yuanling` | `pattern/make.py` | 本案 |
| `zhilingduijin` | 默认 | `hanfu-zhidui` | `pattern/make.py` | 本案 |
| `shiyanshuling` | 默认 | `shiyan-shuling` | `pattern/make.py` | 本案（试验） |

> `shiyanshuling` 是**试验版型**：定稿几何（第 6 步），**暂无旋钮**（不造假滑杆）；
> 改版型走改 `pattern/*.py` 或重新派生。模板 `pattern/_tpl.pieces.json`（`shuling-v1`）。说明见 `shiyan-shuling/使用说明.md`。

## 父-子关系（别改口径）

`hanfu-studio` 是**父程序**，各版型目录（`hanfu-*` 六个 ＋ 试验版型 `shiyan-shuling`）是**子程序**：父程序**调用**它们、
**从属**关系成立，但**目录独立、代码不搬进 studio、子程序仍能单独跑**。
这不是合并、不是 vendoring、不是冻结。

三条契约（已在代码里成立）：

1. `make` 号型档：`--sex {sex} --size {size} --out {out}`（可加 `--params <json>` / `--dump-params`）；
2. `params` 夹具档：`HANFU_PARAMS` ＋ `HANFU_OUT` 环境变量；
3. 子程序回传 `<产物>.pieces.json`（裁片轮廓 / 布纹 / 刀口 / 片名），父程序据此排料与出 DXF。

**出图口径统一**：裁片图一律走 `sheet.write_sheet()`（`ming-gaojiaoling/pattern/sheet.py` 是母本，
各项目拷一份），图层固定为 `OUTLINE / NOTCH / MARK / AUX_PATH / GRAIN / DIM / LABEL / BLOCK / SCALE`，
带图签与 100mm 标尺。不要手搓 polygon + 填充。

## 从哪读起

1. `hanfu-studio/README.md` —— 父程序手册：四层结构、父子契约、注册版型、项目管理、组件库、排料、打包
2. `hanfu-studio/kit/04-口径清单.md` —— **动手前必读**：形制口径、术语黑名单、按口径分开的闸门判据
3. `hanfu-studio/kit/README.md` —— 素材包：三个入口 ＋ 阅读顺序 ＋ 三条铁律

单个版型看它自己目录里的 `README.md`（或 `pattern/使用说明.md`）。

## 子程序里的三类文件（读代码前先分清）

1. **版型程序本体** —— `pattern/*.py`。父-子关系**只对这类成立**。
2. **各项目自己长出来的验证脚本与参考** —— `verification/`、`sources/`、`archive/`。史料，父程序不依赖。
3. **为接通父程序而改/加进去的东西** —— `export_dxf_whole*.py`、`pattern/sheet.py`、派生量重算等。

## 发行包（换台电脑双击即用）

```
hanfu-studio.exe        主程序（单文件）
runtime\                 随包 Python 3.13（embeddable + ezdxf/numpy/Pillow/shapely/fontTools）
```

- 出图 / 出 DXF 靠 `runtime\python.exe` 跑子程序脚本。解释器解析顺序：
  `HANFU_PY` → 随包 `runtime\` → `config.json` 的 python → 本机 venv → `sys.executable`。
- 重建：`python hanfu-studio/build_exe.py`（会顺带调 `tools/stage_runtime.py` 备运行时）。
- **exe 里不带几何，也不该"锁死"版型清单**：`patterns.json` 打包后仍从仓库读（见
  `adapters.registry_file()`），所以新注册版型不必重新打包。

## 跑

```bash
# 父程序（本机带 tkinter 的解释器）
<python> hanfu-studio/studio.py

# 自检（所有版型 × 号型 × 产物，结果写 logs/）
<python> hanfu-studio/selftest.py

# 重建 kit 索引（版型 / 闸门 / 项目 / 素材镜像）
cd hanfu-studio/kit && <python> scripts/build_kit.py
```

> `patterns.json` 的 `workspace` 指向本仓根（写成相对 `".."`）；换机或改目录只改这一个值。

## 信息安全（提交前自动拦）

- **闸门**：`tools/check_secrets.py` 扫暂存区（本机用户名路径、工作区绝对路径、token、
  `skey`、私钥、`password=`/`api_key=` 赋值、`.env`/`*.pem`/`id_rsa`、页面快照等），命中**阻止提交**。
- 装法（克隆后做一次）：`git config core.hooksPath .githooks`；推前可全量扫：`--history`。
- 规矩：**页面快照不入库**；文档/生成物不写本机绝对路径；`dist/`、`out/`、`projects.json` 等运行时产物一律 ignore。
- 素材图的 EXIF 属原拍摄方，为不损失量图精度不重编码；对外分发请自行去元数据。

## 许可

代码 MIT（见 `hanfu-cad/LICENSE`）。`sources/` 下的图片版权归原权利方，仅作研究与比对留证。
