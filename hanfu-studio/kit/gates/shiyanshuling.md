# 闸门 · 试验竖领浅交襟（竖领·默认）（`shiyanshuling`）

## 分类

**有原型**：先跑参照闸门，再跑自洽/对账。
- 第 6 步自检：`python pattern/step6.py`（在 `shiyan-shuling/`）｜最近结果：26/26 PASS；领条 8 边 / 共边 2×30 / 端头 2×30 / 自交 0 / 面积 7023.330613（2026-11-11）
- 模板自检：`python pattern/save_template.py`（在 `shiyan-shuling/`）｜最近结果：11/11 PASS（2026-11-11）

## 跑什么

```bash
cd hanfu-studio
python - <<'PY'
import adapters as A
r = A.generate_all('shiyanshuling', '本案')
print(r['gates']['summary'])
PY
```

（还没有实测记录：先在 studio 里跑一次「一键生成」）

> 口径：**失败不硬打回**——WARN 只报错示意，人工确认后写 `signoff.json`。