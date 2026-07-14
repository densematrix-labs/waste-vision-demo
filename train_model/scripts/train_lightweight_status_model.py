#!/usr/bin/env python3
import ast
import csv
import json
import pickle
import random
import tarfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "train_model" / "data"
WORK_DIR = ROOT / "train_model" / "work"
MODEL_DIR = ROOT / "train_model" / "models"
CLASSES = ["is_full", "is_empty", "is_scattered"]
DISPLAY = {
    "is_full": "满溢风险",
    "is_empty": "未满载",
    "is_scattered": "周边散落",
}


def extract_images() -> Path:
    image_dir = WORK_DIR / "images"
    if image_dir.exists() and len(list(image_dir.glob("*.jpg"))) >= 100:
        return image_dir
    image_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(DATA_DIR / "images.tar.gz", "r:gz") as archive:
        archive.extractall(image_dir)
    return image_dir


def load_labels():
    rows = []
    with open(DATA_DIR / "outdoor_garbage.csv", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            labels = {item["label"] for item in ast.literal_eval(row["annotations"])}
            target = [1 if name in labels else 0 for name in CLASSES]
            rows.append((row["image_name"], target, sorted(labels)))
    return rows


def feature_vector(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"cannot read image: {image_path}")
    image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    features = []
    for channel in range(3):
        hist = cv2.calcHist([hsv], [channel], None, [16], [0, 256]).flatten()
        hist = hist / max(hist.sum(), 1.0)
        features.extend(hist.tolist())
    edges = cv2.Canny(gray, 70, 160)
    features.append(float(edges.mean() / 255.0))
    features.append(float(gray.mean() / 255.0))
    features.append(float(gray.std() / 255.0))
    for grid in (2, 4):
        h, w = gray.shape
        for gy in range(grid):
            for gx in range(grid):
                crop = gray[gy * h // grid:(gy + 1) * h // grid, gx * w // grid:(gx + 1) * w // grid]
                features.append(float(crop.mean() / 255.0))
                features.append(float(crop.std() / 255.0))
    return np.array(features, dtype=np.float32)


def train():
    random.seed(20260713)
    image_dir = extract_images()
    rows = load_labels()
    x = np.stack([feature_vector(image_dir / name) for name, _, _ in rows])
    y = np.array([target for _, target, _ in rows], dtype=np.int64)
    train_x, val_x, train_y, val_y = train_test_split(x, y, test_size=0.2, random_state=20260713)
    model = MultiOutputClassifier(
        RandomForestClassifier(
            n_estimators=240,
            max_depth=8,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=20260713,
        )
    )
    model.fit(train_x, train_y)
    pred = model.predict(val_x)
    metrics = {
        "dataset": "UniqueData/outdoor_garbage",
        "classes": CLASSES,
        "train_images": int(len(train_x)),
        "validation_images": int(len(val_x)),
        "validation_exact_match": float(accuracy_score(val_y, pred)),
        "validation_macro_f1": float(f1_score(val_y, pred, average="macro", zero_division=0)),
        "validation_per_class_f1": {
            name: float(f1_score(val_y[:, index], pred[:, index], zero_division=0))
            for index, name in enumerate(CLASSES)
        },
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "garbage_status_random_forest.pkl"
    with open(model_path, "wb") as file:
        pickle.dump({"model": model, "classes": CLASSES, "metrics": metrics}, file)
    with open(MODEL_DIR / "training_metrics.json", "w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)
    return model, metrics, model_path


def predict_scores(model, image_path: Path) -> dict[str, float]:
    x = feature_vector(image_path).reshape(1, -1)
    probabilities = model.predict_proba(x)
    scores = {}
    for name, proba in zip(CLASSES, probabilities):
        if proba.shape[1] == 1:
            scores[name] = float(proba[0, 0])
        else:
            scores[name] = float(proba[0, 1])
    return scores


def render_result(scores: dict[str, float]):
    source = ROOT / "scene-fixed-input.jpg"
    out = ROOT / "scene-trained-model.jpg"
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
    font_title = ImageFont.truetype(font_path, 34)
    font_body = ImageFont.truetype(font_path, 28)
    panel_x, panel_y, panel_w, panel_h = 34, 34, 520, 238
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=16, fill=(8, 17, 16))
    draw.text((panel_x + 24, panel_y + 22), "巡检模型输出", fill=(237, 248, 243), font=font_title)
    y = panel_y + 82
    for key in ["is_full", "is_scattered", "is_empty"]:
        value = scores[key]
        color = (184, 242, 93) if value >= 0.5 else (138, 163, 155)
        draw.text((panel_x + 24, y), f"{DISPLAY[key]}  {value * 100:.0f}%", fill=color, font=font_body)
        y += 48
    image.save(out, quality=92)


def main():
    model, metrics, model_path = train()
    scores = predict_scores(model, ROOT / "scene-fixed-input.jpg")
    render_result(scores)
    with open(ROOT / "trained-model-output.json", "w", encoding="utf-8") as file:
        json.dump({"model": str(model_path), "metrics": metrics, "scores": scores}, file, ensure_ascii=False, indent=2)
    print(json.dumps({"model": str(model_path), "metrics": metrics, "scores": scores}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
