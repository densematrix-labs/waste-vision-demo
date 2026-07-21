# Public Dataset Training Pipeline

This pipeline keeps public source images out of the GitHub Pages tree. It builds a reproducible external-data workspace and writes only scripts, manifests, reports, and model artifacts to the repo when selected.

## Policy

- Customer RB images remain the domain anchor for the scene classifier.
- Roboflow overflow data is used only for `overflow` / `normal` scene-status expansion after export access is available.
- TACO, Mendeley, and Innovatiana data are used only for object-level `trash_object` detection support.
- Public source images are stored under ignored directories: `external_data/` and `public_yolo_dataset/`.

## Run

```bash
bash training_pipeline/train_public_detection.sh
```

The script uses Docker, mounts Kaggle credentials read-only, builds `public_yolo_dataset/`, trains a YOLO detection baseline, and exports ONNX.

## Current Access Notes

- TACO can be downloaded directly from official annotation/image URLs.
- Innovatiana maps to Kaggle dataset `viswaprakash1990/garbage-detection`; Kaggle credentials are required.
- Roboflow `garbage-can-overflow` requires `ROBOFLOW_API_KEY` or manual export.
- Mendeley `z732f9pwxt` is confirmed CC BY 4.0, but the static page does not expose a stable direct archive URL in this environment.

## Current Baseline

The expanded public detection baseline uses only object-level data sources:

- TACO: 80 images added.
- Innovatiana Garbage Detection: 3,000 images added from 10,464 available image/label pairs.
- Combined YOLO dataset: 2,464 train images and 616 validation images.

The trained artifact is a YOLO11n detection model with one class, `trash_object`.

Final validation metrics:

- Precision: 0.629
- Recall: 0.451
- mAP50: 0.500
- mAP50-95: 0.303

Compared with the first 200-image baseline:

- Dataset size: 200 images -> 3,080 images
- Validation instances: 140 -> 4,045
- mAP50: 0.407 -> 0.500
- mAP50-95: 0.238 -> 0.303

Expanded artifacts:

- `models/public-detection-expanded/trash-object-yolo11n-det-expanded.pt`
- `models/public-detection-expanded/trash-object-yolo11n-det-expanded.onnx`
- `models/public-detection-expanded/trash-object-yolo11n-det-expanded-metrics.json`
- `models/public-detection-expanded/trash-object-yolo11n-det-expanded-val-pred.jpg`

Customer scene smoke test at confidence 0.15:

- `customer-scenes/bulky-waste-pile.jpg`: 4 detections
- `customer-scenes/dirty-ground-scatter.jpg`: 7 detections
- `customer-scenes/overflow-bin-row.jpg`: 3 detections
- `customer-scenes/overflow-yard-pile.jpg`: 9 detections

This is a trash-object detection supplement. It is not wired into the customer UI because the UI currently needs scene-level status, and overflow / empty / full still needs Roboflow export or customer box labels.
