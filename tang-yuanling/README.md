# tang-yuanling · 唐圆领（默认口径子程序）

逐步绘图做出来的版型，单号「本案」。几何底子是 `../ming-gaojiaoling/pattern/_template_back.json`
（**只读**，不改 ming 一行）。

> 子程序之一，口径＝**默认**。父程序在 `../hanfu-studio/`，注册 id `tangyuanling`。

## 口径（用户逐步定稿）

- **领口**：P ＝ (NECK/2 ＋ 30, L)，`P_SHIFT=30`（「P 右移 3cm」）；P′ 关于前中缝对称；
  以 PP′ 为直径作圆、圆心 (0, L)、r＝80，取**下半圆**。
- **续衽左缘**：过 P′ 的直线；`XUREN_TILT_DEG`（None ＝ ∥ 衣身左缘；数值 ＝ 与竖直夹角），
  两端恒为 P′ 与「左缘 ∩ 下摆」（二分求交）。
- **续衽面积**：沿闭合边界分段线积分 `A = ½∮(x dy − y dx)`；四段＝下摆／中缝／领口弧／左缘。
  （下摆本身**是一条**简单三次贝塞尔，不分段。）
- **领子**：A、B 沿左缘直线随便取（暂定 P′ 为 AB 中点），|AB| ＝ 领宽 70；
  **领子＝三段连续、开放、不闭合**的一条带子：
  ① 外襟 P′→P（πr）② 外襟 P→后片→内襟 P′（2r）③ 内襟 P′→P（πr），
  `L = ∫ds = 2πr + 2r = 662.654825`，展开 **662.65 × 70**。
- **后片不挖领**：顶边中段保持模板 y＝L 的水平直线，领子段 ② 沿它装。

## 四片

| 片 | qty | 来源 |
|---|---|---|
| 领条 | 1 | 三段开放长条 662.65×70 |
| 前片原生 | 2 | 外襟衣身本体（中缝右边、含袖），骨架照抄模板后片半，只把领口换成圆领 |
| 前片续衽 | 2 | 四段边界围出的越中片 |
| 后片（半·模板原样） | 2 | 直接搬模板 cmds ＋ 刀口 ＋ 直丝，不拼整片 |

内襟＝前片原生镜像、内襟续衽＝续衽镜像，故 qty 记 2，不另画。

## 文件与产物

```
pattern/geo.py     几何全在这里（纯函数，脚本只消费）
pattern/step1..6.py 逐步绘图脚本（领口点 → 领口圆 → 续衽左缘 → 上领子 → 平铺 → 裁片）
pattern/make.py    studio 入口（kind=make，4 旋钮 P_SHIFT / COLLAR_W / COLLAR_SPLIT / XUREN_TILT_DEG）
pattern/sheet.py   裁片图排版器（拷自 ming-gaojiaoling）
pattern/唐圆领_本案.svg / .pieces.json   定稿产物
out/               过程图、平铺预览、领子完整数据、续衽分段积分数据、裁片图
```

```bash
python pattern/make.py --sex — --size 本案 --out pattern   # 定稿裁片图
python pattern/make.py --dump-params                      # 4 个旋钮的当前值
python pattern/step6.py                                   # 过程稿裁片图 ＋ 裁片数据.json
python pattern/step5.py --tilt 20                         # 平铺预览（续衽左缘倾角可调）
```

## 边界

模板后片颈侧点是 ±50，而 P 已右移到 ±80；后领段两端与后片领口名义点不重合，
当前按「P 直连 P′、长 2r」处理，**未改后片**。
