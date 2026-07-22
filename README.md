# 垃圾投放点智能巡检平台

这是一个用于客户沟通的静态网页原型。当前定位已经调整为：展示视觉大模型对客户现有算法难以稳定判断的固定点位截图进行异常识别、证据定位、风险解释和处置建议。

页面支持：

- 使用客户 RB 原始固定点位截图作为现场案例
- 展示视觉大模型的结构化研判结果
- 输出满溢、散落、堆放、地面脏污等可复核证据区域
- 展示桶内高度、开盖记录、清运计划等现场信号接入项
- 将视觉判断转换为清运复核、保洁复核和现场处置建议
- 支持上传现场截图并展示同一套 VLM 研判流程

访问地址：

```bash
https://densematrix-labs.github.io/waste-vision-demo/
```

## 演示定位

这个 demo 不是为了证明一个重新训练的小模型超过客户现有模型，而是为了展示 VLM 在疑难画面中的价值：

- 客户现有模型可继续负责常规检测和稳定场景
- VLM 负责处理难识别、语义复杂、需要解释依据的画面
- 输出不仅是分类结果，还包括异常依据、证据区域、风险等级和处置动作
- 点位业务数据用于约束 VLM 判断，降低把雨后反光、车辆遮挡、临时人员活动误判为异常的风险

## 当前实现

当前 GitHub Pages 版本是纯静态页面。为了避免在浏览器暴露服务端密钥，页面内置了四张客户 RB 图的结构化 VLM 研判结果，用于演示客户沟通口径和交互流程。

真实上传图片的在线 VLM 分析不能直接放在静态网页里调用，需要通过服务端代理或 Cloudflare Worker 转发。代理服务应完成：

- 接收现场截图
- 调用视觉大模型
- 返回结构化 JSON，包括事件类型、证据区域、判断依据、置信度和工单建议
- 记录审计日志，便于复核模型输出是否符合现场事实

## VLM 输出结构

页面使用的结构化输出字段包括：

```json
{
  "predictions": [
    { "event": "overflow", "score": 0.88 },
    { "event": "litter", "score": 0.74 }
  ],
  "regions": [
    {
      "label": "overflow_area",
      "title": "满溢证据",
      "score": 0.84,
      "x1": 270,
      "y1": 150,
      "x2": 560,
      "y2": 355
    }
  ],
  "rationale": "桶旁大面积袋装物和纸箱堆积，超过单次正常投放规模，和清运复核场景高度一致。"
}
```

推荐事件类别：

- `overflow`：满溢风险
- `litter`：周边散落或袋装堆放
- `dirty`：地面脏污、积水、油污、污痕
- `normal`：未发现明显异常

推荐证据区域类别：

- `overflow_area`：桶口外溢或桶旁满溢证据
- `scattered_litter`：落地散落证据
- `pileup`：袋装、纸箱、大件堆放证据
- `dirty_ground`：地面脏污证据
- `blocked_opening`：投放口或箱盖阻挡证据

## 现场画面

页面展示的 4 张图全部来自客户提供的 RB 固定点位图片包，公开数据图片只用于研究和训练实验，不进入客户 dashboard：

- `customer-scenes/overflow-yard-pile.jpg`：满溢/堆积，来源 `GS3821437_0_20260626_045618.jpg`
- `customer-scenes/overflow-bin-row.jpg`：桶口外溢，来源 `GS3821436_0_20260620_045443.jpg`
- `customer-scenes/dirty-ground-scatter.jpg`：地面脏污，来源 `GT9455976_0_20260615_134504.jpg`
- `customer-scenes/bulky-waste-pile.jpg`：袋装堆放，来源 `GS3821437_0_20260627_215529.jpg`

## 公开数据调查

类似场景公开数据集调查报告在：

```bash
research_waste_datasets/similar_scene_dataset_investigation_2026-07-22.md
```

结论：未找到能直接替代 RB 自标注的完整公开数据集。最接近的是 StreetView-Waste，但需要授权；Roboflow overflow/fill-level 可以补充满溢场景；Kaggle pile/litter 类数据可以补充堆放和散落；`dirty_ground` 和 `blocked_opening` 仍主要依赖 RB 客户图自标注。

## 历史训练资产

仓库保留了前期训练和公开数据扩充资产，作为研究记录和可选辅助能力。它们不再是客户演示页面的主链路。

相关目录：

```bash
models/
training_pipeline/
testset/
research_waste_datasets/
```

客户演示页面的当前主线是 VLM 疑难研判；传统检测模型可以作为后续混合方案中的辅助定位或成本优化模块。
