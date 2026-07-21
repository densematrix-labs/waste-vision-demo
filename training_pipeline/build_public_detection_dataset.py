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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public YOLO detection supplement dataset.")
    parser.add_argument("--taco-limit", type=int, default=80)
    parser.add_argument("--innovatiana-limit", type=int, default=120)
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


def coco_bbox_to_yolo(bbox: list[float], width: int, height: int) -> str | None:
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
    return f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}"


def split_for(index: int) -> str:
    return "val" if index % 5 == 0 else "train"


def add_detection_sample(source_image: Path, yolo_lines: list[str], split: str, name: str) -> bool:
    if not yolo_lines:
        return False
    image_dest = DATASET / "images" / split / f"{name}{source_image.suffix.lower()}"
    label_dest = DATASET / "labels" / split / f"{name}.txt"
    image_dest.parent.mkdir(parents=True, exist_ok=True)
    label_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image, image_dest)
    label_dest.write_text("\n".join(yolo_lines) + "\n", encoding="utf-8")
    return True


def build_taco(limit: int, seed: int) -> dict:
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
            line = coco_bbox_to_yolo(ann["bbox"], width, height)
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
        if not label.exists() and image.parent.name == "images":
            label = image.parent.parent / "labels" / f"{image.stem}.txt"
        if label.exists():
            pairs.append((image, label))
    return pairs


def normalize_yolo_to_trash_object(label_path: Path) -> list[str]:
    lines = []
    for raw in label_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.strip().split()
        if len(parts) != 5:
            continue
        try:
            nums = [float(value) for value in parts[1:]]
        except ValueError:
            continue
        if any(math.isnan(value) for value in nums):
            continue
        x, y, w, h = [clip(value) for value in nums]
        if w <= 0 or h <= 0:
            continue
        lines.append(f"0 {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    return lines


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
        lines = normalize_yolo_to_trash_object(label)
        if add_detection_sample(image, lines, split_for(added), f"innovatiana_{added:04d}"):
            added += 1
    return {"source": "innovatiana", "available_pairs": len(pairs), "added": added, "status": "ok" if added else "empty"}


def write_dataset_yaml() -> None:
    (DATASET / "data.yaml").write_text(
        "\n".join([
            f"path: {DATASET}",
            "train: images/train",
            "val: images/val",
            "names:",
            "  0: trash_object",
            "",
        ]),
        encoding="utf-8",
    )


def write_report(results: list[dict]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    counts = {}
    for split in ("train", "val"):
        counts[split] = len(list((DATASET / "images" / split).glob("*"))) if (DATASET / "images" / split).exists() else 0
    report = {
        "dataset": "public_yolo_detection_supplement",
        "classes": ["trash_object"],
        "counts": counts,
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
    ]
    write_dataset_yaml()
    write_report(results)
    print(json.dumps(json.loads((ARTIFACTS / "public_detection_report.json").read_text(encoding="utf-8")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
