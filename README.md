# 汉服 CAD · 单仓（父程序 + 三个子程序）

一个仓装四件东西：**一个父程序（壳）+ 三个子程序（版型程序）+ 一份给 AI 的素材包**。

| 目录 | 角色 | 一句话 |
|---|---|---|
| **`hanfu-studio/`** | **父程序** | 图形化版型工作台：选型 / 参数 / 预览 / 手工排料 / CAD 协同。**不含几何**，出图一律调子程序的脚本；内含 `kit/`（给 harness 的素材包） |
| `hanfu-cad/` | 子程序 | 分裁 · 对穿交**半臂**（钱樟墓夹袄，11 码） |
| `hanfu-jiexiu/` | 子程序 | 分裁 · 对穿交**接袖**（长袖，男装 5 码） |
| `hanfu-shenyi/` | 子程序 | 通裁 · **深衣**（V1 原衣 / V2 宽袖礼服 / V3 窄袖便服） |

已注册版型（`hanfu-studio/patterns.json`）：

| id | 裁法 | 项目 | 脚本 |
|---|---|---|---|
| `banbi` | 分裁 | `hanfu-cad` | `pattern/make.py` |
| `jiexiu` | 分裁 | `hanfu-jiexiu` | `pattern/make.py` |
| `shenyi` | 通裁 | `hanfu-shenyi` | `pattern/build_shenyi.py`（V2 / V3） |
| `zhiling` | 通裁 | `hanfu-shenyi` | `pattern/build.py`（V1） |

## 父-子关系（别改口径）

`hanfu-studio` 是**父程序**，三个 `hanfu-*` 是**子程序**：父程序**调用**它们、**从属**关系成立，
但**目录独立、代码不搬进 studio、子程序仍能单独跑**。这不是合并、不是 vendoring、不是冻结。

三条契约（已在代码里成立）：① `make` 号型档走 `--sex/--size/--out`；
② `params` 夹具档走 `HANFU_PARAMS` + `HANFU_OUT`；③ 子程序回传 `sheet.pieces.json`。

## 两个几何根，不硬合并

| | 分裁（半臂 / 接袖） | 通裁（深衣 / 直领交襟） |
|---|---|---|
| 版型是什么 | 一组裁片，每片一条闭合轮廓 | 一块布 + 折叠序列（段 / 折线 / 剪口） |
| DXF | 每片一条轮廓 | **整衣一片**连续闭合外轮廓，折线剪口另设图层 |
| 图纸 | 裁片图（各片排开标尺寸） | 顺序图（材料 → 对折 → 剪开 → 压领 → 平铺） |

## 子程序里的三类文件（读代码前先分清）

1. **版型程序本体** —— `pattern/*.py`。父-子关系**只对这类成立**。
2. **重整前各项目自己长出来的验证脚本与参考** —— `verification/`、`sources/`、`archive/`。
   史料：口径各管各的，父程序不依赖。
3. **studio 重整时改/加进去的东西** —— `export_dxf_whole*.py`、`build.py` 的派生量重算等。
   需求来自父程序，但代码住在子程序里。

## 从哪读起

1. `hanfu-studio/README.md` —— 核心设计（口径）、四层结构、手工编辑、注册版型、项目管理、CAD 协同
2. `hanfu-studio/kit/README.md` —— 给 harness（AI）的素材包：三个入口 + 阅读顺序 + 三条铁律
3. `hanfu-studio/kit/04-口径清单.md` —— **动手前必读**：形制口径、术语黑名单、按裁法分开的闸门判据

## 发行包结构（换台电脑双击即用）

```
hanfu-studio.exe        主程序（单文件）
runtime\                 随包 Python 3.13（embeddable + ezdxf/numpy/Pillow/shapely/fontTools）
```

- 出图/出 DXF 靠 `runtime\python.exe` 跑各子程序的脚本（解释器解析顺序：
  `HANFU_PY` → 随包 `runtime\` → `config.json` 的 python → 本机 venv → `sys.executable`）。
- 重建发行包：`python hanfu-studio/tools/stage_runtime.py`（取 embeddable + 拷依赖），
  再 `python hanfu-studio/build_exe.py`（打包后会自动调它）。
- 本机那份 `~/.workbuddy/.../envs/hanfu` **已删除**，项目不再依赖工作区外的任何解释器。
- 离线重建依赖：把轮子放进 `hanfu-studio/tools/wheels/`（`pip download --only-binary :all:
  --platform win_amd64 --python-version 3.13 -d tools/wheels ezdxf numpy pillow shapely fonttools pyparsing`）。

## 信息安全（提交前自动拦）

- **闸门**：`tools/check_secrets.py` 扫暂存区（本机用户名路径、工作区绝对路径、微博/微信 token、
  `skey`、私钥、`password=`/`api_key=` 赋值、`.env`/`*.pem`/`id_rsa`、页面快照等），命中就**阻止提交**。
- **装法**（克隆后做一次，本仓已配好）：
  ```bash
  git config core.hooksPath .githooks
  ```
- 推之前再全量扫一次（含历史）：`python tools/check_secrets.py --history`
- 规矩：**页面快照不入库**（含会话 token），只留 `.md` 正文摘录；文档/生成物里不写本机绝对路径；
  打包产物（`dist/`、`runtime/`）一律 ignore。

## 跑

```bash
# 父程序（本机带 tkinter 的解释器）
<你的 python 路径> hanfu-studio/studio.py

# 自检（走完所有版型×号型×产物，结果写 logs/）
python hanfu-studio/selftest.py

# 重建 kit 索引（版型/闸门/项目/素材镜像）
cd hanfu-studio/kit && python scripts/build_kit.py
```

> `hanfu-studio/patterns.json` 的 `workspace` 指向本仓根；换机或改目录时只改这一个值。

## 许可

代码 MIT（见 `hanfu-cad/LICENSE`）。`sources/` 下的图片版权归原权利方
（中国丝绸博物馆、微博作者、厂商、知乎文章等），仅作研究与比对留证，不再分发授权。
