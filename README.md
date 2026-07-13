# Waste Vision BBox Demo

垃圾识别 bbox demo：上传图片、切换模型 provider、展示统一 JSON、按原图像素坐标绘制 bbox overlay。

## Run

```bash
docker compose up -d --build
```

Open: http://localhost:8099

## Adapter Contract

模型接入时把 `mockDetect()` 替换为真实 `/api/detect` 调用，保持返回结构：

```json
{
  "image_width": 1280,
  "image_height": 720,
  "provider": "openai",
  "objects": [
    {
      "id": "obj_1",
      "label": "plastic_bottle",
      "label_zh": "透明塑料瓶",
      "category": "recyclable",
      "bbox": { "x1": 120, "y1": 80, "x2": 360, "y2": 410 },
      "confidence": 0.86,
      "reason": "transparent bottle with cap"
    }
  ]
}
```
