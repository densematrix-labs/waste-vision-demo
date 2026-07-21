#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker run --rm \
  -v "$ROOT:/workspace" \
  -v "$HOME/.kaggle:/root/.kaggle:ro" \
  -w /workspace \
  python:3.11-slim \
  bash -lc '
    apt-get update >/tmp/apt.log &&
    apt-get install -y --no-install-recommends libglib2.0-0 libgl1 libxcb1 libxext6 >/tmp/apt-install.log &&
    pip install --no-cache-dir ultralytics onnx onnxslim >/tmp/pip.log &&
    python training_pipeline/build_public_detection_dataset.py --download-innovatiana --taco-limit 80 --innovatiana-limit 120 &&
    yolo detect train data=/workspace/public_yolo_dataset/data.yaml model=yolo11n.pt epochs=30 imgsz=320 batch=8 workers=0 project=/workspace/public_yolo_runs name=trash_object exist_ok=True &&
    yolo export model=/workspace/public_yolo_runs/trash_object/weights/best.pt format=onnx imgsz=320 opset=12 simplify=True
  '
