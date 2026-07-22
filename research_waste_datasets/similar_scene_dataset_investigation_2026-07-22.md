# Similar Scene Dataset Investigation - 2026-07-22

Question: find public datasets that are genuinely close to RB fixed-camera waste collection point inspection, especially bin overflow, nearby scattered waste, pileup, dirty ground, and blocked openings.

## Ranking

### 1. StreetView-Waste

- URL: https://streetview-waste.di.ubi.pt/
- GitHub: https://github.com/DiogoJPaulo/StreetView-Waste
- Paper: https://arxiv.org/abs/2511.16440
- Scene fit: high for waste containers and overflow, medium for RB fixed-camera view.
- Labels: container detection bounding boxes, tracking ids, overflow/litter instance masks.
- Scale reported by project: 36,478 fisheye images, 14,219 labeled-object images, 71,170 boxes, 5,149 overflow masks.
- Access: website exposes download links for detection, tracking, segmentation, and full zip, but direct requests return HTTP 401 Digest authentication. The GitHub README says access is managed through a data license agreement.
- License: GitHub code is MIT. Dataset access/license requires the StreetView-Waste agreement.
- Use: highest-value public source if access is approved. Good candidate for `overflow_area` pretraining and segmentation experiments.
- Limitation: collected from a moving waste-collection vehicle, not a fixed CCTV point. It does not cover RB-specific indoor/outdoor collection point framing.

### 2. Roboflow garbage-can-overflow

- URL: https://universe.roboflow.com/mariswary-deepak-4ajr0/garbage-can-overflow
- Dataset page: https://universe.roboflow.com/mariswary-deepak-4ajr0/garbage-can-overflow/dataset/4
- Scene fit: medium-high for bin overflow.
- Labels: object detection boxes.
- Scale: 1,974 images.
- License: CC BY 4.0 on Roboflow dataset page.
- Classes observed from prior review: empty, full, open/closed empty/full, broken trash can, healthy trash can, trash flow.
- Use: best immediately usable public source for `overflow_area` or bin status pretraining if exported from Roboflow.
- Limitation: images are not necessarily fixed collection-point scenes. Needs class remapping and quality filtering.

### 3. Roboflow waste-bin-fill-level-detect2

- URL: https://universe.roboflow.com/image-data-mlcpz/waste-bin-fill-level-detect2-lxsf4-u3odm
- Scene fit: medium for bin fullness.
- Labels: object detection boxes.
- Scale: 469 images.
- Classes shown in search snippets: empty, full, half-full, overflowing.
- Use: small but semantically useful fill-level supplement.
- Limitation: too small to carry the model alone; use only as overflow/fullness supplement.

### 4. Hugging Face UniqueData outdoor_garbage

- URL: https://huggingface.co/datasets/UniqueData/outdoor_garbage
- Scene fit: medium-high for outdoor bins, full/empty/scattered status.
- Labels: image-level XML annotations for `is_full`, `is_empty`, and `is_scattered`.
- Public sample: dataset card exposes 100 examples and says the full commercial dataset contains 10,000 images.
- License: CC BY-ND 4.0 for the sample; commercial usage points to paid dataset.
- Use: useful for status/classification experiments and label taxonomy reference.
- Limitation: not a bbox/segmentation training source for customer demo, and CC BY-ND/commercial terms make it unsuitable as-is for customer-facing model training.

### 5. Kaggle Garbage-Detection (Piles of Garbage)

- URL: https://www.kaggle.com/datasets/hammadarshad18/garbage-detection
- Scene fit: medium for pileup / dumped waste.
- Labels: YOLO text annotations confirmed by file listing.
- License: CC0-1.0.
- Use: useful public supplement for `pileup`.
- Limitation: detects street piles of garbage, not bin overflow or fixed collection point status.

### 6. Kaggle Visual Pollution Dhaka Streets

- URL: https://www.kaggle.com/datasets/yearathossain/visual-pollution-dhaka-streets
- Scene fit: medium for `scattered_litter` and `pileup`.
- Labels: YOLO bounding boxes.
- Scale: 1,400 images, 6 visual pollution classes. The dataset card says `street litter` and `construction materials` each have 300 images.
- License: MIT.
- Use: keep as street litter / construction-material pileup supplement.
- Limitation: street-view domain, not RB collection-point domain.

### 7. Kaggle Garbage Overflow

- URL: https://www.kaggle.com/datasets/bhanu77/garbage-overflow
- Scene fit: potentially medium for overflow.
- Labels: Pascal VOC XML files confirmed by file listing.
- Size: about 15 MB.
- License: `copyright-authors`.
- Use: inspect visually only; use for training only if rights are cleared.
- Limitation: unclear license and small size.

### 8. Kaggle Garbage detection Dataset on an Indian Campus

- URL: https://www.kaggle.com/datasets/shohomde/dmc-project
- Scene fit: high for business logic, low for detection.
- Labels: folder-level classification (`Clean_real` and related directories), not object detection.
- License: not specified in metadata.
- Use: useful as reference for hard classification cases: authorized bin with wrappers or bottles spilled outside is alert; clean authorized bin is not alert; dry leaves or flowers near bin are not alert.
- Limitation: includes AI-generated/augmented images, not bbox/seg; not suitable as detector training data without relabeling.

### 9. Kaggle Waste Bin Detection Dataset (RISS2021)

- URL: https://www.kaggle.com/datasets/elirotondo/waste-bin-detection-dataset-riss-2021
- Scene fit: low-medium.
- Labels: JSON detection labels confirmed by file listing.
- Domain: transit bus waste bin object detection.
- Use: only for bin detector pretraining if container localization becomes useful.
- Limitation: does not address overflow, dirty ground, scattered waste, or RB fixed-point scene.

### 10. TACO / Mendeley / generic trash detection datasets

- TACO: https://github.com/pedropro/TACO
- Mendeley Trash Detection: https://data.mendeley.com/datasets/z732f9pwxt/1
- Hugging Face MRS Trash Detection: https://huggingface.co/datasets/alexNova/MRS-Trash-Detection
- Scene fit: low-medium.
- Labels: object detection or segmentation, mostly material/object categories.
- Use: generic `waste_object` and `scattered_litter` pretraining.
- Limitation: they answer "what object is this trash" rather than "is this collection point overflowing or dirty".

## Hard Conclusion

There is no public dataset found that directly covers all RB customer classes with the right camera domain:

- `overflow_area`
- `scattered_litter`
- `pileup`
- `dirty_ground`
- `blocked_opening`

The best public path is:

1. Use StreetView-Waste if access is approved, especially its overflow segmentation masks.
2. Export Roboflow overflow/fill-level datasets for immediate overflow pretraining.
3. Add CC0/MIT YOLO street pile and street litter datasets for `pileup` and `scattered_litter`.
4. Keep TACO/Mendeley/generic trash detection as low-priority object pretraining only.
5. Use RB self-labeled data as the final domain source for customer-facing detector/segmenter.

## Recommended Training Use

- `overflow_area`: StreetView-Waste segmentation, Roboflow garbage-can-overflow, Roboflow bin-fill-level.
- `scattered_litter`: StreetView-Waste overflow/litter masks, Visual Pollution Dhaka street litter, TACO/MRS generic trash.
- `pileup`: Kaggle Piles of Garbage, Visual Pollution Dhaka construction material, RB self labels.
- `dirty_ground`: public sources are weak; RB polygon labels are required.
- `blocked_opening`: no good public dataset found; RB labels are required.

The current public expanded dataset is useful as a pretraining base, but direct customer-demo quality requires RB self-labeling and domain fine-tuning.
