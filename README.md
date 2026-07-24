# 垃圾投放点智能巡检平台

这是一个用于客户沟通的静态网页原型。当前定位已经收敛为：展示固定点位截图中的桶外垃圾堆放识别、证据定位、现场说明和处置建议。

页面支持：

- 使用客户 RB 原始固定点位截图作为现场案例
- 展示智能分析的结构化识别结果
- 输出桶外堆放的可复核证据区域
- 对正常巡检画面保持未发现堆放状态，不触发堆放工单
- 展示桶内高度、开盖记录、清运计划等现场信号接入项
- 将视觉判断转换为清运复核和现场处置建议
- 支持上传现场截图并展示同一套智能分析流程

访问地址：

```bash
https://densematrix-labs.github.io/waste-vision-demo/
```

## 演示定位

这个 demo 不是为了证明一个重新训练的小模型超过客户现有模型，而是为了展示智能分析在堆放场景中的价值：

- 客户现有模型可继续负责常规检测和稳定场景
- 云端模型负责处理难识别、语义复杂、需要解释依据的画面
- 输出不仅是分类结果，还包括现场说明、证据区域和处置动作
- 点位业务数据用于约束 VLM 判断，降低把雨后反光、车辆遮挡、临时人员活动误判为异常的风险

## 当前实现

当前 GitHub Pages 页面默认调用真实云端分析代理，不在浏览器暴露服务端密钥。链路为：

```bash
浏览器 → Cloudflare Worker → DenseMatrix LLM Proxy → 多模态模型 → 结构化 JSON → 前端绘制证据区域
```

代理服务负责：

- 接收现场截图
- 调用云端多模态模型
- 返回结构化 JSON，包括事件类型、证据区域、判断依据、置信度和工单建议
- 记录审计日志，便于复核模型输出是否符合现场事实

离线演示模式保留在 `?offline=1`，只用于上游服务不可用时查看页面交互，不作为默认客户演示路径。

## 分析代理

Cloudflare Worker 位于：

```bash
workers/vlm-proxy/
```

部署时设置密钥：

```bash
cd workers/vlm-proxy
npx wrangler secret put LLM_PROXY_API_KEY
npx wrangler deploy
```

默认前端调用地址：

```bash
https://waste-vision-vlm.densematrix.ai/analyze
```

如需临时改用其他代理地址，可在页面加载前设置：

```html
<script>
  window.WASTE_VISION_VLM_API_URL = "https://example.com/analyze";
</script>
```

## 输出结构

页面使用的结构化输出字段包括：

```json
{
  "predictions": [
    { "event": "pileup", "score": 0.9 },
    { "event": "normal", "score": 0.1 }
  ],
  "regions": [
    {
      "label": "pileup",
      "title": "堆放证据",
      "score": 0.9,
      "x1": 270,
      "y1": 150,
      "x2": 560,
      "y2": 355
    }
  ],
  "rationale": "桶旁大面积袋装物和纸箱堆积，超过单次正常投放规模，和清运复核场景高度一致。"
}
```

事件类别：

- `pileup`：桶外垃圾堆放风险
- `normal`：未发现明显异常

证据区域类别：

- `pileup`：袋装、纸箱、大件堆放证据

## 现场画面

页面展示图片全部来自客户提供的 RB 固定点位图片包，公开数据图片只用于研究和训练实验，不进入客户 dashboard：

- `customer-scenes/overflow-yard-pile.jpg`：桶旁堆放，来源 `GS3821437_0_20260626_045618.jpg`
- `customer-scenes/bulky-waste-pile.jpg`：袋装堆放，来源 `GS3821437_0_20260627_215529.jpg`
- `customer-scenes/normal-site.jpg`：正常巡检画面
- `customer-scenes/normal-clean-01.jpg`：正常巡检画面
- `customer-scenes/normal-clean-02.jpg`：正常巡检画面

## 公开数据调查

类似场景公开数据集调查报告在：

```bash
research_waste_datasets/similar_scene_dataset_investigation_2026-07-22.md
```

结论：未找到能直接替代 RB 自标注的完整公开数据集。相关公开数据只作为研究记录和后续训练参考，当前客户演示优先使用 RB 固定点位图片，并聚焦桶外堆放识别。

## 历史训练资产

仓库保留了前期训练和公开数据扩充资产，作为研究记录和可选辅助能力。它们不再是客户演示页面的主链路。

相关目录：

```bash
models/
training_pipeline/
testset/
research_waste_datasets/
```

客户演示页面的当前主线是桶外堆放识别和现场说明；传统检测模型可以作为后续混合方案中的辅助定位或成本优化模块。
