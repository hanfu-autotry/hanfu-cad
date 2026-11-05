# hanfu-studio（父程序 · 壳里没有几何）

- 目录：`hanfu-studio`（相对仓根）
- 出图/导出**一律调各项目自己的脚本**；壳只认「脚本 + 参数 + 产物」。

## 工具

| 用途 | 文件 |
|---|---|
| 界面/父程序 | `studio.py` |
| 矢量预览（SVG→Canvas） | `svgview.py` |
| 适配层（唯一接口） | `adapters.py` |
| 形制核对闸门 | `gates.py` |
| CAD 协同 DXF 读写 | `dxf_io.py` |
| 排料 DXF | `layout_dxf.py` |
| 全链路自检 | `selftest.py` |
| 按窗口截图（自检用） | `shot.py` |
| 打包 | `build_exe.py` |
| 素材包生成 | `kit/scripts/build_kit.py` |

## 命令行自检（打包版）

```bash
hanfu-studio.exe --check-library            # 共享库
hanfu-studio.exe --check-projects           # 项目管理
hanfu-studio.exe --check-cad <样例.dxf>     # CAD 协同
```

## 日志

- `logs/studio-YYYY-MM-DD.log`（打包后 `%LOCALAPPDATA%/hanfu-studio/logs`）
- 出图/产物/导出/异常各一行；脚本失败连 stderr 全文。**排查先读它。**