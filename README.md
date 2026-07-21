# 垃圾投放点智能巡检平台

这是一个用于客户沟通的静态网页原型，用固定点位截图呈现垃圾投放点现场状态识别、点位数据联动和工单建议流程。

页面支持：

- 使用固定点位原始截图查看输入画面
- 使用浏览器端轻量识别流程生成状态判断
- 展示桶内高度、开盖记录、清运计划等现场信号接入项
- 展示满溢风险、周边散落、地面脏污、正常状态和工单建议
- 支持上传现场截图并生成同一套事件判断结果

访问地址：

https://densematrix-labs.github.io/waste-vision-demo/

## 口径边界

当前页面不是生产级训练模型交付物，也不应对外表述为已完成 YOLO 或分割模型训练。页面里的识别结果用于说明交互链路、现场事件分类方式和客户沟通口径。

如果需要正式交付“真实训练出来的模型”，应另行完成：

- 客户现场数据清洗和去重
- 正常、满溢、散落、脏污等类别标注
- 框选或分割标注规范
- 训练、验证和留出测试集划分
- 线上推理服务和误报/漏报验收

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
