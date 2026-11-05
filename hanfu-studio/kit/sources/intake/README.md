# intake · harness 投放口

新素材放这里；确认对象后挪进 `<对象>/<类型>/`。

必须同时登记一行（否则不算「有根据的素材」）：

```
subject,type,file,project,origin_path,note,anchor_ok,kb,sha1
02-深衣_通裁,剪裁与平铺,新图.jpg,<项目>,<来源URL或路径>,量幅数与开口,PARTIAL,120,<sha1>
```

规则：
1. 先想「这是哪件衣/哪座墓的参考」，再想类型；分不清对象就放 `99-来历待考/`。
2. 说清「能用它量什么」；只能定性写 `anchor_ok=NO`。
3. 不覆盖同名旧素材（同名加 `_v2`）。
4. 重跑 `build_kit.py` 只重建 INDEX，不清空 intake/。
