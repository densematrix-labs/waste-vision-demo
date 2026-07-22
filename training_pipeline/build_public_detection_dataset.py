#!/usr/bin/env python3
import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "external_data"
DATASET = ROOT / "public_yolo_dataset"
ARTIFACTS = ROOT / "public_training_artifacts"
TACO_ANNOTATIONS_URL = "https://raw.githubusercontent.com/pedropro/TACO/master/data/annotations.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
CLASS_NAMES = ["waste_object", "scattered_litter", "pileup", "dirty_ground"]
CLASS_IDS = {name: index for index, name in enumerate(CLASS_NAMES)}
ALYYAN_CLASS_MAP = {
    0: CLASS_IDS["dirty_ground"],
    1: CLASS_IDS["dirty_ground"],
    2: CLASS_IDS["dirty_ground"],
    3: CLASS_IDS["scattered_litter"],
}
VISUAL_POLLUTION_PREFIX_MAP = {
    "streetLitters": CLASS_IDS["scattered_litter"],
    "streetLitters2": CLASS_IDS["scattered_litter"],
    "constructionMat": CLASS_IDS["pileup"],
    "bricks": CLASS_IDS["pileup"],
    "bricks2": CLASS_IDS["pileup"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public YOLO detection supplement dataset.")
    parser.add_argument("--taco-limit", type=int, default=80)
    parser.add_argument("--innovatiana-limit", type=int, default=120)
    parser.add_argument("--alyyan-limit", type=int, default=0)
    parser.add_argument("--dhaka-limit", type=int, default=0)
    parser.add_argument("--geo-waste-limit", type=int, default=0)
    parser.add_argument("--spellsharp-limit", type=int, default=0)
    parser.add_argument("--ahnaftahmeed-limit", type=int, default=0)
    parser.add_argument("--household-limit", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--download-innovatiana", action="store_true")
    return parser.parse_args()


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def download_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            path.write_bytes(response.read())
        return path.stat().st_size > 0
    except Exception:
        if path.exists():
            path.unlink()
        return False


def clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def coco_bbox_to_yolo(bbox: list[float], width: int, height: int, class_id: int = 0) -> str | None:
    if width <= 0 or height <= 0:
        return None
    x, y, w, h = bbox
    if w <= 1 or h <= 1:
        return None
    xc = clip((x + w / 2) / width)
    yc = clip((y + h / 2) / height)
    bw = clip(w / width)
    bh = clip(h / height)
    if bw <= 0 or bh <= 0:
        return None
    return f"{class_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}"


def split_for(index: int) -> str:
    return "val" if index % 5 == 0 else "train"


def add_detection_sample(source_image: Path, yolo_lines: list[str], split: str, name: str) -> bool:
    if not yolo_lines:
        return False
    image_dest = DATASET / "images" / split / f"{name}{source_image.suffix.lower()}"
    label_dest = DATASET / "labels" / split / f"{name}.txt"
    image_dest.parent.mkdir(parents=True, exist_ok=True)
    label_dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source_image, image_dest)
    except OSError:
        shutil.copy2(source_image, image_dest)
    label_dest.write_text("\n".join(yolo_lines) + "\n", encoding="utf-8")
    return True


def build_taco(limit: int, seed: int) -> dict:
    if limit <= 0:
        return {"source": "taco", "attempted": 0, "added": 0, "status": "disabled"}
    annotations = download_json(TACO_ANNOTATIONS_URL)
    images = {item["id"]: item for item in annotations["images"]}
    grouped: dict[int, list[dict]] = {}
    for ann in annotations["annotations"]:
        grouped.setdefault(ann["image_id"], []).append(ann)

    candidates = list(grouped)
    random.Random(seed).shuffle(candidates)
    taco_raw = EXTERNAL / "taco"
    taco_raw.mkdir(parents=True, exist_ok=True)
    added = 0
    attempted = 0
    for image_id in candidates:
        if added >= limit:
            break
        image = images[image_id]
        url = image.get("flickr_640_url") or image.get("flickr_url")
        if not url:
            continue
        attempted += 1
        suffix = Path(image.get("file_name", "image.jpg")).suffix.lower() or ".jpg"
        source_path = taco_raw / f"taco_{image_id}{suffix}"
        if not source_path.exists() and not download_file(url, source_path):
            continue
        width = int(image.get("width") or 0)
        height = int(image.get("height") or 0)
        lines = []
        for ann in grouped[image_id]:
            line = coco_bbox_to_yolo(ann["bbox"], width, height, CLASS_IDS["waste_object"])
            if line:
                lines.append(line)
        if add_detection_sample(source_path, lines, split_for(added), f"taco_{added:04d}"):
            added += 1
    return {"source": "taco", "attempted": attempted, "added": added, "status": "ok" if added else "empty"}


def run_kaggle_download(target: Path) -> tuple[bool, str]:
    target.mkdir(parents=True, exist_ok=True)
    if any(target.rglob("*.txt")) and any(target.rglob("*.jpg")):
        return True, "dataset already present"
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--quiet",
        "kaggle",
    ]
    subprocess.run(command, check=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "kaggle",
            "datasets",
            "download",
            "-d",
            "viswaprakash1990/garbage-detection",
            "-p",
            str(target),
            "--unzip",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.returncode == 0, result.stdout[-2000:]


def find_yolo_pairs(root: Path) -> list[tuple[Path, Path]]:
    pairs = []
    for image in root.rglob("*"):
        if image.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        label = image.with_suffix(".txt")
        if not label.exists():
            parts = list(image.relative_to(root).parts)
            if "images" in parts:
                parts[parts.index("images")] = "labels"
                label = root.joinpath(*parts).with_suffix(".txt")
        if label.exists():
            pairs.append((image, label))
    return pairs


def normalize_yolo(label_path: Path, class_map: dict[int, int] | None = None, default_class: int = 0) -> list[str]:
    lines = []
    for raw in label_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.strip().split()
        if len(parts) < 5:
            continue
        try:
            source_class = int(float(parts[0]))
            nums = [float(value) for value in parts[1:]]
        except ValueError:
            continue
        if any(math.isnan(value) for value in nums):
            continue
        target_class = class_map.get(source_class) if class_map is not None else default_class
        if target_class is None:
            continue
        if len(nums) == 4:
            x, y, w, h = [clip(value) for value in nums]
        elif len(nums) >= 6 and len(nums) % 2 == 0:
            xs = [clip(value) for value in nums[0::2]]
            ys = [clip(value) for value in nums[1::2]]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            w = max_x - min_x
            h = max_y - min_y
            x = min_x + w / 2
            y = min_y + h / 2
        else:
            continue
        if w <= 0 or h <= 0:
            continue
        lines.append(f"{target_class} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    return lines


def build_generic_yolo_source(
    source_name: str,
    raw_root: Path,
    limit: int,
    seed: int,
    target_class: str,
    output_prefix: str,
    mapping_note: str,
) -> dict:
    if limit <= 0:
        return {"source": source_name, "added": 0, "status": "disabled"}
    if not raw_root.exists():
        return {"source": source_name, "added": 0, "status": "not_downloaded"}
    pairs = find_yolo_pairs(raw_root)
    random.Random(seed).shuffle(pairs)
    added = 0
    for image, label in pairs:
        if added >= limit:
            break
        lines = normalize_yolo(label, default_class=CLASS_IDS[target_class])
        if add_detection_sample(image, lines, split_for(added), f"{output_prefix}_{added:04d}"):
            added += 1
    return {
        "source": source_name,
        "available_pairs": len(pairs),
        "added": added,
        "status": "ok" if added else "empty",
        "class_mapping": {"all_source_classes": target_class},
        "mapping_note": mapping_note,
    }


def build_innovatiana(limit: int, seed: int, should_download: bool) -> dict:
    raw_root = EXTERNAL / "innovatiana_garbage_detection"
    if should_download:
        ok, output = run_kaggle_download(raw_root)
        if not ok:
            return {"source": "innovatiana", "added": 0, "status": "download_failed", "details": output}
    if not raw_root.exists():
        return {"source": "innovatiana", "added": 0, "status": "not_downloaded"}
    pairs = find_yolo_pairs(raw_root)
    random.Random(seed).shuffle(pairs)
    added = 0
    for image, label in pairs:
        if added >= limit:
            break
        lines = normalize_yolo(label, default_class=CLASS_IDS["waste_object"])
        if add_detection_sample(image, lines, split_for(added), f"innovatiana_{added:04d}"):
            added += 1
    return {"source": "innovatiana", "available_pairs": len(pairs), "added": added, "status": "ok" if added else "empty"}


def build_alyyan(limit: int, seed: int) -> dict:
    raw_root = EXTERNAL / "candidates" / "alyyan_trash_detection" / "Dataset"
    if limit <= 0:
        return {"source": "alyyan_trash_detection", "added": 0, "status": "disabled"}
    if not raw_root.exists():
        return {"source": "alyyan_trash_detection", "added": 0, "status": "not_downloaded"}
    pairs = find_yolo_pairs(raw_root)
    random.Random(seed).shuffle(pairs)
    added = 0
    for image, label in pairs:
        if added >= limit:
            break
        lines = normalize_yolo(label, class_map=ALYYAN_CLASS_MAP)
        if add_detection_sample(image, lines, split_for(added), f"alyyan_{added:04d}"):
            added += 1
    return {
        "source": "alyyan_trash_detection",
        "available_pairs": len(pairs),
        "added": added,
        "status": "ok" if added else "empty",
        "class_mapping": {
            "dirt": "dirty_ground",
            "liquid": "dirty_ground",
            "marks": "dirty_ground",
            "trash": "scattered_litter",
        },
    }


def visual_pollution_prefix(path: Path) -> str:
    return path.stem.rsplit("-", 1)[0]


def build_visual_pollution_dhaka(limit: int, seed: int) -> dict:
    raw_root = EXTERNAL / "candidates" / "visual_pollution_dhaka" / "vispol-dhaka-streets"
    if limit <= 0:
        return {"source": "visual_pollution_dhaka", "added": 0, "status": "disabled"}
    annotations = raw_root / "annotations"
    images = raw_root / "images"
    if not annotations.exists() or not images.exists():
        return {"source": "visual_pollution_dhaka", "added": 0, "status": "not_downloaded"}
    label_paths = [path for path in annotations.glob("*.txt") if visual_pollution_prefix(path) in VISUAL_POLLUTION_PREFIX_MAP]
    random.Random(seed).shuffle(label_paths)
    added = 0
    skipped_missing_image = 0
    for label in label_paths:
        if added >= limit:
            break
        image = images / f"{label.stem}.jpg"
        if not image.exists():
            skipped_missing_image += 1
            continue
        target_class = VISUAL_POLLUTION_PREFIX_MAP[visual_pollution_prefix(label)]
        lines = normalize_yolo(label, default_class=target_class)
        if add_detection_sample(image, lines, split_for(added), f"dhaka_{added:04d}"):
            added += 1
    return {
        "source": "visual_pollution_dhaka",
        "available_relevant_labels": len(label_paths),
        "skipped_missing_image": skipped_missing_image,
        "added": added,
        "status": "ok" if added else "empty",
        "class_mapping": {
            "streetLitters/streetLitters2": "scattered_litter",
            "constructionMat/bricks/bricks2": "pileup",
            "billboard/wires/towers": "ignored",
        },
    }


def build_geo_waste(limit: int, seed: int) -> dict:
    raw_root = EXTERNAL / "candidates" / "geo_waste_yolo" / "Geo Waste"
    if limit <= 0:
        return {"source": "geo_waste_yolo", "added": 0, "status": "disabled"}
    if not raw_root.exists():
        return {"source": "geo_waste_yolo", "added": 0, "status": "not_downloaded"}
    pairs = find_yolo_pairs(raw_root)
    random.Random(seed).shuffle(pairs)
    added = 0
    for image, label in pairs:
        if added >= limit:
            break
        lines = normalize_yolo(label, default_class=CLASS_IDS["waste_object"])
        if add_detection_sample(image, lines, split_for(added), f"geo_waste_{added:04d}"):
            added += 1
    return {
        "source": "geo_waste_yolo",
        "available_pairs": len(pairs),
        "added": added,
        "status": "ok" if added else "empty",
        "class_mapping": {"all_source_classes": "waste_object"},
        "mapping_note": "Dataset does not include class-name metadata in the downloaded archive; all boxes are used only as generic waste objects.",
    }


def build_spellsharp_garbage_data(limit: int, seed: int) -> dict:
    return build_generic_yolo_source(
        source_name="spellsharp_garbage_data",
        raw_root=EXTERNAL
        / "candidates"
        / "spellsharp_garbage_data"
        / "YOLO-Waste-Detection-1"
        / "YOLO-Waste-Detection-1",
        limit=limit,
        seed=seed,
        target_class="waste_object",
        output_prefix="spellsharp",
        mapping_note="YOLO classes are material/object categories, so they are used only as generic waste objects.",
    )


def build_ahnaftahmeed_trash_detection(limit: int, seed: int) -> dict:
    return build_generic_yolo_source(
        source_name="ahnaftahmeed_trash_detection",
        raw_root=EXTERNAL
        / "candidates"
        / "ahnaftahmeed_trash_detection_image_dataset"
        / "trash-detection.v35.yolov5pytorch",
        limit=limit,
        seed=seed,
        target_class="scattered_litter",
        output_prefix="ahnaftahmeed",
        mapping_note="YOLOv5 labels include polygon segmentation rows; polygons are converted to boxes and used as street scattered litter.",
    )


def build_household_trash_recycling(limit: int, seed: int) -> dict:
    return build_generic_yolo_source(
        source_name="household_trash_recycling",
        raw_root=EXTERNAL / "candidates" / "household_trash_recycling",
        limit=limit,
        seed=seed,
        target_class="waste_object",
        output_prefix="household",
        mapping_note="YOLO classes are household item categories, so they are used only as generic waste objects.",
    )


def write_dataset_yaml() -> None:
    (DATASET / "data.yaml").write_text(
        "\n".join([
            f"path: {DATASET}",
            "train: images/train",
            "val: images/val",
            "names:",
            *[f"  {index}: {name}" for index, name in enumerate(CLASS_NAMES)],
            "",
        ]),
        encoding="utf-8",
    )


def write_report(results: list[dict]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    counts = {}
    class_counts = {name: 0 for name in CLASS_NAMES}
    for split in ("train", "val"):
        counts[split] = len(list((DATASET / "images" / split).glob("*"))) if (DATASET / "images" / split).exists() else 0
        label_dir = DATASET / "labels" / split
        if label_dir.exists():
            for label in label_dir.glob("*.txt"):
                for raw in label.read_text(encoding="utf-8", errors="ignore").splitlines():
                    parts = raw.split()
                    if not parts:
                        continue
                    try:
                        class_id = int(float(parts[0]))
                    except ValueError:
                        continue
                    if 0 <= class_id < len(CLASS_NAMES):
                        class_counts[CLASS_NAMES[class_id]] += 1
    report = {
        "dataset": "public_business_detection_supplement",
        "classes": CLASS_NAMES,
        "counts": counts,
        "class_counts": class_counts,
        "sources": results,
        "blocked": {
            "roboflow_overflow": "ROBOFLOW_API_KEY is not present; export URL requires key or manual download.",
            "mendeley_trash_detection": "Static page does not expose stable direct file URL in this environment; keep as source candidate.",
        },
    }
    (ARTIFACTS / "public_detection_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    reset_dir(DATASET)
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    results = [
        build_taco(args.taco_limit, args.seed),
        build_innovatiana(args.innovatiana_limit, args.seed, args.download_innovatiana),
        build_alyyan(args.alyyan_limit, args.seed),
        build_visual_pollution_dhaka(args.dhaka_limit, args.seed),
        build_geo_waste(args.geo_waste_limit, args.seed),
        build_spellsharp_garbage_data(args.spellsharp_limit, args.seed),
        build_ahnaftahmeed_trash_detection(args.ahnaftahmeed_limit, args.seed),
        build_household_trash_recycling(args.household_limit, args.seed),
    ]
    write_dataset_yaml()
    write_report(results)
    print(json.dumps(json.loads((ARTIFACTS / "public_detection_report.json").read_text(encoding="utf-8")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
