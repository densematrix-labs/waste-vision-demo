#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TACO_LIMIT="${TACO_LIMIT:-1000}"
INNOVATIANA_LIMIT="${INNOVATIANA_LIMIT:-1000}"
EPOCHS="${EPOCHS:-15}"
IMGSZ="${IMGSZ:-320}"
BATCH="${BATCH:-8}"
RUN_NAME="${RUN_NAME:-trash_object_public_expanded}"

docker run --rm \
  -v "$ROOT:/workspace" \
  -v "$HOME/.kaggle:/root/.kaggle:ro" \
  -e TACO_LIMIT="$TACO_LIMIT" \
  -e INNOVATIANA_LIMIT="$INNOVATIANA_LIMIT" \
  -e EPOCHS="$EPOCHS" \
  -e IMGSZ="$IMGSZ" \
  -e BATCH="$BATCH" \
  -e RUN_NAME="$RUN_NAME" \
  -w /workspace \
  python:3.11-slim \
  bash -lc '
    apt-get update >/tmp/apt.log &&
    apt-get install -y --no-install-recommends libglib2.0-0 libgl1 libxcb1 libxext6 >/tmp/apt-install.log &&
    pip install --no-cache-dir ultralytics onnx onnxslim >/tmp/pip.log &&
    python training_pipeline/build_public_detection_dataset.py --download-innovatiana --taco-limit "$TACO_LIMIT" --innovatiana-limit "$INNOVATIANA_LIMIT" &&
    yolo detect train data=/workspace/public_yolo_dataset/data.yaml model=yolo11n.pt epochs="$EPOCHS" imgsz="$IMGSZ" batch="$BATCH" workers=0 project=/workspace/public_yolo_runs name="$RUN_NAME" exist_ok=True &&
    yolo export model="/workspace/public_yolo_runs/$RUN_NAME/weights/best.pt" format=onnx imgsz="$IMGSZ" opset=12 simplify=True
  '
