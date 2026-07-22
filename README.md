# 垃圾投放点智能巡检平台

这是一个用于客户沟通的静态网页原型，用固定点位截图呈现垃圾投放点现场状态识别、画面目标框选、点位数据联动和工单建议流程。

页面支持：

- 使用固定点位原始截图查看输入画面
- 使用已训练的 YOLO11n 分类模型生成状态判断
- 使用已训练的位置检测模型在前端展示可见垃圾物、散落物、堆放物和地面脏污位置
- 展示模型加载状态、推理耗时、框选目标数量和模型输出置信度
- 展示桶内高度、开盖记录、清运计划等现场信号接入项
- 展示满溢风险、周边散落、地面脏污、正常状态和工单建议
- 支持上传现场截图并生成同一套事件判断结果

访问地址：

https://densematrix-labs.github.io/waste-vision-demo/

## 模型

当前页面加载仓库内的两个 YOLO11n 模型进行浏览器端本地推理：

```bash
models/waste-yolo11n-cls.onnx
models/waste-yolo11n-cls.pt
models/labels.json
models/metrics.json
models/public-detection-multiclass/waste-scene-objects-yolo11n-det-multiclass.onnx
models/public-detection-multiclass/waste-scene-objects-yolo11n-det-multiclass.pt
```

ONNX 是 Open Neural Network Exchange 的缩写，可以理解为“神经网络模型的通用运行格式”。本项目不是用 ONNX 训练模型，而是先用 Ultralytics YOLO 训练出 PyTorch `.pt` 权重，再导出为 `.onnx`，这样静态网页可以在浏览器里通过 ONNX Runtime Web 直接执行模型推理。`.onnx` 不是另一套算法，也不是前端假数据；它是训练后模型权重和计算图的可部署版本。

分类模型训练命令在 Docker 内执行：

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace python:3.11-slim bash -lc 'apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 libxcb1 libxext6 && pip install --no-cache-dir ultralytics onnx onnxslim && yolo classify train data=/workspace/yolo_dataset model=yolo11n-cls.pt epochs=80 imgsz=224 batch=4 workers=0 erasing=0.0 degrees=0 translate=0 scale=0 fliplr=0.0 hsv_h=0 hsv_s=0 hsv_v=0 project=/workspace/yolo_runs name=waste_cls exist_ok=True'
```

分类结果来源：页面里的“满溢、散落、脏污、正常”来自 `waste-yolo11n-cls.onnx` 的运行时输出，不是前端按图片名称主观写死。这个模型由 YOLO11n-cls 训练，训练数据当前为 19 张客户 RB 现场图片，类别为 `dirty`、`litter`、`normal`、`overflow`。训练配置关闭随机增强，用于让 demo 中的客户现场样张和上传链路走实际模型推理。内置验证集和训练集目前使用同一批弱标注图片，最终 Top-1 / Top-5 为 100%，该指标只说明模型已拟合这批样张，不代表生产泛化效果。

画面框选来源：页面里的框来自 `waste-scene-objects-yolo11n-det-multiclass.onnx` 的运行时输出。该 detection 模型输入尺寸为 320，输出 4 个业务位置类别：`waste_object`（可见垃圾物）、`scattered_litter`（散落物）、`pileup`（堆放物）、`dirty_ground`（地面脏污）。它不负责整图状态分类；前端只把重叠过滤后的坐标画出来。

## 边界

当前页面已经展示目标检测模型的真实输出框，但检测框来自公开数据补充训练的四分类位置检测模型，用于增强“垃圾物体、散落物、堆放物、地面脏污在哪里”的可视化说服力。它还不是经过客户业务框标注训练出来的满/空/溢出专用 detection 或 segmentation 模型。

如果需要正式交付“满溢区域 / 空桶 / 溢出 / 脏污区域”等业务框，需要对客户 RB 图补充框选或分割标注，并重新划分训练集、验证集和留出测试集后训练 YOLO detection/segmentation 模型。

## 公开数据补充训练

已新增公开数据融合与目标检测模型，用于补充“可见垃圾物、散落物、堆放物、地面脏污位置检测”能力，不直接替代客户 RB 图训练出来的场景分类模型。公开数据图片只进入训练集，不在客户演示页面展示。

已并入的数据：

- Innovatiana Garbage Detection：通过 Kaggle 下载，抽取 500 张，统一映射为 `waste_object`
- Alyyan Trash Detection：通过 Kaggle 下载，抽取 900 张，`trash` 映射为 `scattered_litter`，`dirt/liquid/marks` 映射为 `dirty_ground`
- Visual Pollution Dhaka Streets：通过 Kaggle 下载，抽取 500 张，`streetLitters` 映射为 `scattered_litter`，`constructionMat/bricks` 映射为 `pileup`
- Geo Waste YOLO：通过 Kaggle 下载，抽取 500 张；下载包未提供类别名元数据，因此保守映射为 `waste_object`

训练产物：

```bash
models/public-detection/trash-object-yolo11n-det.pt
models/public-detection/trash-object-yolo11n-det.onnx
models/public-detection/trash-object-yolo11n-det-metrics.json
models/public-detection/trash-object-yolo11n-det-results.csv
models/public-detection-expanded/trash-object-yolo11n-det-expanded.pt
models/public-detection-expanded/trash-object-yolo11n-det-expanded.onnx
models/public-detection-expanded/trash-object-yolo11n-det-expanded-metrics.json
models/public-detection-expanded/trash-object-yolo11n-det-expanded-results.csv
models/public-detection-multiclass/waste-scene-objects-yolo11n-det-multiclass.pt
models/public-detection-multiclass/waste-scene-objects-yolo11n-det-multiclass.onnx
models/public-detection-multiclass/waste-scene-objects-yolo11n-det-multiclass-metrics.json
models/public-detection-multiclass/waste-scene-objects-yolo11n-det-multiclass-results.csv
```

当前 expanded 模型使用 2,464 张训练图、616 张验证图，验证集 4,045 个实例，验证结果为 Precision 0.629、Recall 0.451、mAP50 0.500、mAP50-95 0.303。该模型可以作为散落垃圾检测补充资产；由于 Roboflow overflow 数据尚未导出，它还不能可靠承担“满/空/溢出”的场景状态判断。

当前 multiclass 位置检测模型使用 1,920 张训练图、480 张验证图，验证集 2,528 个实例，数据框数量为 `waste_object` 4,739、`scattered_litter` 2,170、`pileup` 512、`dirty_ground` 3,906。1 epoch CPU baseline 的验证结果为 Precision 0.304、Recall 0.139、mAP50 0.100、mAP50-95 0.040。该结果说明四类检测链路已经跑通，但精度仍是 baseline；要进入客户可信展示，需要继续增加客户 RB 的 bbox/seg 标注并用更多 epoch/GPU 训练。

浏览器端“秒出结果”是因为页面加载的是本地 ONNX Runtime Web，YOLO11n 小模型在 224/320 输入尺寸上通常可在几十到数百毫秒内完成推理。页面已展示模型加载状态、总推理耗时、检测耗时和检测框数量，避免被误解为写死结果。

公开数据训练脚本和 source manifest 在：

```bash
training_pipeline/
```

Roboflow overflow 数据需要 `ROBOFLOW_API_KEY` 或手动导出；Mendeley 数据源页面未在当前环境暴露稳定下载直链，先作为候选源保留。

## 现场画面

页面使用 4 张代表性固定点位画面：

- `customer-scenes/overflow-yard-pile.jpg`：满溢/堆积
- `customer-scenes/overflow-bin-row.jpg`：桶口外溢
- `customer-scenes/dirty-ground-scatter.jpg`：地面散落
- `customer-scenes/bulky-waste-pile.jpg`：大件堆放

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
