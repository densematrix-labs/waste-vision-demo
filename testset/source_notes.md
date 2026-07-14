# 数据源候选说明

已确认或待确认的数据源按治理事件映射如下。

## 可直接进入训练/测试候选

- `UniqueData/outdoor_garbage`
  - 用途：满溢、未满载、周边散落的图像级状态识别。
  - 当前 demo 已使用该数据训练轻量模型。
  - 限制：只有图像级标签，不支持检测框评估。

- `TACO Trash Annotations in Context`
  - 用途：小包垃圾落地、零散垃圾、小目标和复杂环境。
  - 说明：TACO 是公开 litter 数据集，GitHub README 说明包含 diverse environments，手工标注并提供 COCO 格式 annotations。
  - 来源：https://github.com/pedropro/TACO

- `alexNova/MRS-Trash-Detection`
  - 用途：垃圾/袋装物体检测候选，可作为通用检测预训练或补充测试集。
  - 说明：Hugging Face 数据卡显示任务为 Object Detection，标签含 trash/garbage/detection/YOLO/MRS-YOLO，许可证为 apache-2.0。
  - 来源：https://huggingface.co/datasets/alexNova/MRS-Trash-Detection

- `Dataset of Stagnant Water and Wet Surface with Annotations`
  - 用途：地面脏污的负例和边界例，特别是积水、湿地面、反光、雨后地面。
  - 说明：Mendeley 页面说明包含 1976 张 RGB 标注图，两类为 water 和 wet surface，许可为 CC BY 4.0。
  - 来源：https://data.mendeley.com/datasets/y6zyrnxbfm/4

## 需要人工复核或导出权限的数据源

- Roboflow wet-floor / littering behavior 项目
  - 用途：地面脏污、违规投放行为、人和垃圾袋交互。
  - 限制：需要确认导出权限、项目仍公开可用、许可证可用于客户演示。

- 固定点位公开视频/截图
  - 用途：客户输入形态验证、复杂环境、固定区域配置。
  - 限制：未标注样本只能作为测试候选或人工复核素材，不能直接包装成训练集。
