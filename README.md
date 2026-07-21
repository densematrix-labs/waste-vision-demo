# 垃圾厢房智能巡检演示

这是一个面向客户展示的网页演示，用固定点位截图呈现垃圾厢房治理事件巡检效果。

页面支持：

- 使用固定点位原始截图查看输入画面
- 使用巡检模型演示输出生成状态识别结果图
- 展示桶内高度、开盖记录、清运计划等现场信号接入项
- 展示满溢风险、周边散落、地面脏污和工单建议
- 增加客户现场训练图集样例，可切换查看满溢/堆积、小包落地、地面脏污、箱盖阻挡等场景

公开演示地址：

https://densematrix-labs.github.io/waste-vision-demo/

样例画面来源：Semarang PantauSemar TPS BULU LOR 公开固定点位页面。

## 训练模型

本仓库包含一套真实训练链路，训练脚本在：

```bash
train_model/scripts/train_lightweight_status_model.py
```

训练数据使用 Hugging Face 上的公开真实标注数据集 `UniqueData/outdoor_garbage`，标签为：

- `is_full`：满溢
- `is_empty`：未满载
- `is_scattered`：周边散落

该数据集是图像级状态标注，不是位置标注。因此页面展示的是状态识别结果。

训练产物：

- `train_model/models/garbage_status_random_forest.pkl`
- `train_model/models/training_metrics.json`
- `scene-trained-model.jpg`

下载数据后可重新训练：

```bash
mkdir -p train_model/data
curl -L -o train_model/data/images.tar.gz https://huggingface.co/datasets/UniqueData/outdoor_garbage/resolve/main/data/images.tar.gz
curl -L -o train_model/data/outdoor_garbage.csv https://huggingface.co/datasets/UniqueData/outdoor_garbage/resolve/main/data/outdoor_garbage.csv
python3 train_model/scripts/train_lightweight_status_model.py
```

当前演示模型使用 100 张真实标注样例训练，用于跑通真实训练与推理流程。客户页统一使用“巡检模型演示输出/样例输出”口径，客户点位数据到位后，可按同一链路替换为客户现场数据训练。

## 客户样例

页面已加入 RB 6-7 月训练图集中的 4 张代表性现场图：

- `customer-scenes/pileup-bin-area.jpg`：满溢/堆积
- `customer-scenes/ground-litter-zone.jpg`：小包落地
- `customer-scenes/dirty-water-zone.jpg`：地面脏污
- `customer-scenes/bin-lid-blocked.jpg`：箱盖阻挡

## 治理事件测试集

测试集不按“垃圾种类”组织，而按客户治理事件组织。当前 taxonomy 在：

```bash
testset/taxonomy.json
```

覆盖事件：

- 小包垃圾落地
- 地面脏污
- 垃圾满溢/堆积
- 箱盖被压/阻挡
- 违规投放行为
- 保洁/工作人员场景
- 复杂环境

每类事件至少收 20 张真实或近真实样本，目标 50 张以上，并同时覆盖正例、负例和边界例。数据登记模板在：

```bash
testset/manifest_template.csv
```

校验登记表：

```bash
python3 testset/validate_manifest.py testset/manifest_template.csv
```
