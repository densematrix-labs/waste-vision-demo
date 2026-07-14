#!/usr/bin/env python3
import ast
import csv
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTDOOR_CSV = ROOT / "train_model" / "data" / "outdoor_garbage.csv"
OUTDOOR_IMAGE_DIR = ROOT / "train_model" / "work" / "images"
MANIFEST = ROOT / "testset" / "manifest.csv"
TACO_ANNOTATIONS_URL = "https://raw.githubusercontent.com/pedropro/TACO/master/data/annotations.json"

FIELDS = [
    "asset_id",
    "event_id",
    "split",
    "case_type",
    "local_path",
    "source_id",
    "source_url",
    "license_status",
    "media_type",
    "annotation_mode",
    "labels",
    "has_bbox",
    "has_region",
    "has_sequence",
    "can_train",
    "can_show_customer",
    "notes",
]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def outdoor_rows() -> list[dict[str, str]]:
    rows = []
    if not OUTDOOR_CSV.exists():
        return rows
    with OUTDOOR_CSV.open(newline="", encoding="utf-8") as file:
        for index, row in enumerate(csv.DictReader(file), start=1):
            labels = sorted({item["label"] for item in ast.literal_eval(row["annotations"])})
            if "is_full" not in labels and "is_scattered" not in labels:
                continue
            image_name = row["image_name"]
            rows.append({
                "asset_id": f"outdoor_garbage_{index:03d}",
                "event_id": "overflow_pileup",
                "split": "candidate",
                "case_type": "positive",
                "local_path": str((OUTDOOR_IMAGE_DIR / image_name).relative_to(ROOT)),
                "source_id": "unique_outdoor_garbage",
                "source_url": "https://huggingface.co/datasets/UniqueData/outdoor_garbage",
                "license_status": "check_dataset_card_before_customer_delivery",
                "media_type": "image",
                "annotation_mode": "event_state",
                "labels": ";".join(labels),
                "has_bbox": bool_text(False),
                "has_region": bool_text(False),
                "has_sequence": bool_text(False),
                "can_train": bool_text(True),
                "can_show_customer": bool_text(True),
                "notes": "真实标注图像级满溢/散落状态样本",
            })
            if len(rows) >= 50:
                break
    return rows


def taco_rows() -> list[dict[str, str]]:
    with urllib.request.urlopen(TACO_ANNOTATIONS_URL, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    categories = {item["id"]: item["name"] for item in data["categories"]}
    images = {item["id"]: item for item in data["images"]}
    selected = []
    seen_images = set()
    trigger_words = ("bag", "wrapper", "plastic", "carton", "paper", "cup")
    for annotation in data["annotations"]:
        category = categories[annotation["category_id"]]
        if not any(word in category.lower() for word in trigger_words):
            continue
        image = images[annotation["image_id"]]
        if image["id"] in seen_images:
            continue
        seen_images.add(image["id"])
        selected.append({
            "asset_id": f"taco_litter_{len(selected) + 1:03d}",
            "event_id": "bag_on_ground",
            "split": "candidate",
            "case_type": "boundary",
            "local_path": "",
            "source_id": "taco_litter",
            "source_url": image.get("flickr_640_url") or image.get("flickr_url") or "https://tacodataset.org/",
            "license_status": "check_image_license_per_item",
            "media_type": "image",
            "annotation_mode": "bbox",
            "labels": category,
            "has_bbox": bool_text(True),
            "has_region": bool_text(True),
            "has_sequence": bool_text(False),
            "can_train": bool_text(True),
            "can_show_customer": bool_text(True),
            "notes": "TACO 零散垃圾/小目标候选，需人工筛选固定点位相似度",
        })
        if len(selected) >= 50:
            break
    return selected


def main() -> None:
    rows = outdoor_rows() + taco_rows()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {MANIFEST}")


if __name__ == "__main__":
    main()
