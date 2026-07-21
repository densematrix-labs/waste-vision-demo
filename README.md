# 垃圾投放点智能巡检平台

这是一个用于客户沟通的静态网页原型，用固定点位截图呈现垃圾投放点现场状态识别、点位数据联动和工单建议流程。

页面支持：

- 使用固定点位原始截图查看输入画面
- 使用已训练的 YOLO11n 分类模型生成状态判断
- 展示桶内高度、开盖记录、清运计划等现场信号接入项
- 展示满溢风险、周边散落、地面脏污、正常状态和工单建议
- 支持上传现场截图并生成同一套事件判断结果

访问地址：

https://densematrix-labs.github.io/waste-vision-demo/

## 模型

当前页面加载仓库内的 YOLO11n 分类模型进行浏览器端 ONNX 推理：

```bash
models/waste-yolo11n-cls.onnx
models/waste-yolo11n-cls.pt
models/labels.json
models/metrics.json
```

训练命令在 Docker 内执行：

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace python:3.11-slim bash -lc 'apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 libxcb1 libxext6 && pip install --no-cache-dir ultralytics onnx onnxslim && yolo classify train data=/workspace/yolo_dataset model=yolo11n-cls.pt epochs=80 imgsz=224 batch=4 workers=0 erasing=0.0 degrees=0 translate=0 scale=0 fliplr=0.0 hsv_h=0 hsv_s=0 hsv_v=0 project=/workspace/yolo_runs name=waste_cls exist_ok=True'
```

训练数据当前为 15 张现场图片，类别为 `dirty`、`litter`、`normal`、`overflow`。训练配置关闭随机增强，用于让 demo 中的客户现场样张和上传链路走实际模型推理。内置验证集和训练集目前使用同一批弱标注图片，最终 Top-1 / Top-5 为 100%，该指标只说明模型已拟合这批样张，不代表生产泛化效果。

## 边界

当前模型是 YOLO 分类模型，只输出整张画面的状态类别和置信度。它不是 YOLO detection 或 segmentation 模型，不会输出真实框选坐标或像素级分割结果。

如果需要正式交付“检测框/分割框”的模型，需要补充框选或分割标注，并重新划分训练集、验证集和留出测试集后训练 YOLO detection/segmentation 模型。

## 现场画面

页面使用 4 张代表性固定点位画面：

- `customer-scenes/pileup-bin-area.jpg`：满溢/堆积
- `customer-scenes/ground-litter-zone.jpg`：小包落地
- `customer-scenes/dirty-water-zone.jpg`：地面脏污
- `customer-scenes/normal-site.jpg`：正常画面

## 治理事件测试集

测试集不按“垃圾种类”组织，而按治理事件组织。当前 taxonomy 在：

```bash
testset/taxonomy.json
```

覆盖事件：

- 小包垃圾落地
- 地面脏污
- 垃圾满溢/堆积
- 正常画面
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
