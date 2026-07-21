# Public Dataset Recommendation for Waste-Vision YOLO Training

## Summary

The public data landscape splits into two groups:

- Scene-anomaly data that matches the customer use case: garbage can full/empty/scattered/overflow. This is the most valuable, but most usable sources are Roboflow exports or paid commercial datasets.
- General waste-material data: plastic, paper, glass, metal, organic, etc. This is useful for pretraining or detecting loose trash objects, but it does not directly teach the model "overflow", "dirty ground", or "normal fixed-point site".

Do not blindly merge material-classification datasets into the current four-class anomaly model. It will likely improve object awareness but may worsen customer-facing anomaly decisions unless we remap labels carefully.

## Best Candidates

### 1. Roboflow garbage can overflow

- URL: https://universe.roboflow.com/mariswary-deepak-4ajr0/garbage-can-overflow
- Task: object detection
- Size: 1,974 images
- License shown: CC BY 4.0
- Classes include empty, full, open/closed empty/full, broken trash can, healthy trash can, and trash flow.
- Fit: best public match for customer-facing bin fullness / overflow behavior.
- Integration: export as YOLO format from Roboflow, map full/open_full/close_full/trash flow to `overflow`, empty/open_empty/close_empty/healthy to `normal`, and keep broken trash can out unless the customer wants device damage detection.

### 2. TACO: Trash Annotations in Context

- URL: https://github.com/pedropro/TACO
- Zenodo: https://zenodo.org/records/3354286
- Task: object detection / instance segmentation in COCO-style annotations
- Size: about 1,500 images, 4,784 annotations; Zenodo package is about 1.1 GB.
- Fit: strong for litter/trash-in-the-wild detection, weak for fixed garbage-room fullness.
- Integration: convert COCO annotations to YOLO detection or segmentation. Map all visible loose trash instances to `litter`; do not use it for `overflow`, `dirty`, or `normal`.

### 3. Mendeley Trash Detection Dataset

- URL: https://data.mendeley.com/datasets/z732f9pwxt/1
- Task: object detection
- License shown: CC BY 4.0
- Classes: biodegradable, cardboard, glass, metal, paper, plastic, and all.
- Labels are already in YOLO format.
- Fit: useful as a YOLO detection pretraining supplement for visible waste items; not enough for overflow/cleanliness status.
- Integration: map all waste-object boxes into a generic `litter` detector, or keep material subclasses for a second-stage material classifier.

### 4. Innovatiana Garbage Detection Dataset

- URL: https://www.innovatiana.com/en/datasets/garbage-detection
- Task: object detection
- Size: about 20,900 files, organized train/valid/test
- License shown: CC BY 4.0
- Labels are YOLOv5-compatible TXT.
- Fit: good ready-to-train detection data for common waste objects; domain is sorting/recycling rather than fixed garbage rooms.
- Integration: same as Mendeley, use for object-level litter/material detection, not overflow classification.

### 5. UCI RealWaste

- URL: https://archive.ics.uci.edu/dataset/908/realwaste
- Task: image classification
- Size: 4,752 images, 656.6 MB
- Classes: cardboard, food organics, glass, metal, miscellaneous trash, paper, plastic, textile trash, vegetation.
- Fit: useful for material classification pretraining; weak for customer scene anomaly detection.
- Integration: keep separate from the anomaly classifier, or use as transfer-learning pretraining only.

## Exclude or Defer

### TrashCan 1.0

- URL: https://conservancy.umn.edu/items/6dd6a960-c44a-4510-a679-efb8c82ebfb7
- Task: underwater trash instance segmentation
- Size: 7,212 images
- License note: free for academic teaching/research; commercial use requires JAMSTEC permission.
- Decision: do not use for this customer-facing commercial demo unless permission is obtained. Domain is also underwater, so it is visually mismatched.

### Unidata Outdoor Garbage Dataset

- URL: https://unidata.pro/datasets/outdoor-garbage/
- Task: detection/classification
- Size: 5,000+ images
- Classes include full, empty, scattered.
- Decision: very relevant, but full dataset is paid / agreement-based. Use only if we decide to purchase or request access.

## Recommended Training Plan

1. Keep the customer RB images as the domain anchor.
   - These define the actual camera angle, bin style, lighting, ground texture, and target business labels.

2. Use public data in two separate channels.
   - Scene-status channel: Roboflow garbage can overflow plus customer images for `overflow` and `normal`.
   - Object/litter channel: TACO, Mendeley Trash Detection, and Innovatiana for generic trash-object boxes.

3. Train two models instead of forcing one label taxonomy.
   - YOLO classification: `overflow`, `litter`, `dirty`, `normal` for current UI state.
   - YOLO detection/segmentation: `trash_object`, `bin`, possibly `spill/dirty_area` if we annotate it, for visible localization.

4. Add customer labels before claiming production quality.
   - Classification only needs image-level labels.
   - Detection needs bounding boxes.
   - Segmentation needs masks.

5. Keep attribution and source manifests with the trained model.
   - Every public dataset must have source URL, license, classes used, mapping rules, and date accessed.

## Immediate Repo Impact

The current repo already includes customer images in `yolo_dataset/` and trains an actual YOLO classification prototype. The next engineering step is not to commit public dataset images into the GitHub Pages repo, but to create a separate training-data workspace or DVC-style artifact store and keep only:

- source manifests,
- conversion scripts,
- label mapping files,
- trained model artifacts,
- reproducible Docker training commands.
