# RB 客户图位置检测标注规范

## 目标

当前 dashboard 的分类模型可以回答“整张图属于什么状态”，但位置检测模型主要来自公开数据，在 RB 客户固定点位图上会退化成粗粒度的 `waste_object`。客户级检测需要使用 RB 图自标注 bbox 或 segmentation 后重新训练。

第一批标注采用矩形框 bbox，目标是快速训练出客户域 YOLO detection；如果需要“脏污区域边界”更贴合，后续同一批图可追加 polygon segmentation。

## 类别

- `overflow_area`：满溢区域。桶口外溢、桶旁明显堆出容量边界的垃圾区域。框住满溢主体，不框整只桶。
- `scattered_litter`：散落垃圾。地面上零散袋子、纸盒、饮料瓶、小包、碎片等，按单个明显目标或相邻小群组框。
- `pileup`：堆放物。袋装垃圾、纸箱、大件或混合废弃物形成的集中堆放，按整堆框。
- `dirty_ground`：地面脏污。污渍、积水、油污、明显泥渍或大面积脏污区域，尽量框脏污范围，不框正常地面。
- `blocked_opening`：投放口阻挡。箱盖、投放口被袋子、纸箱、物品遮挡，框遮挡物和受影响开口区域。

## 标注规则

- 只标客户关心的异常目标，忽略车辆、行人、树影、摄像头水印、背景文字。
- 一个目标只标一个最合适类别；如果“散落物”已经形成明显一堆，用 `pileup`。
- 只标可见部分，不凭经验补全被遮挡区域。
- 对红色客户原标注框，不直接照抄；以画面实际异常区域为准。
- 空图或无法判断的图在 Label Studio 的 `quality` 里选择 `skip` 或 `unclear`，不要硬标。
- 每张图至少设置一次 `quality`，便于训练前过滤。

## 训练导出

Label Studio 完成后导出 YOLO 格式，类别顺序必须与 `classes.yaml` 一致：

```
0 overflow_area
1 scattered_litter
2 pileup
3 dirty_ground
4 blocked_opening
```

导出后重新划分 train/val/test，再训练 YOLO detection；如果改用 polygon 标注，则训练 YOLO segmentation。
