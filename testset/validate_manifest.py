#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIRED_COLUMNS = {
    "asset_id",
    "event_id",
    "split",
    "case_type",
    "source_id",
    "source_url",
    "annotation_mode",
    "has_bbox",
    "can_train",
    "can_show_customer",
}


def load_events() -> set[str]:
    taxonomy = json.loads((ROOT / "taxonomy.json").read_text(encoding="utf-8"))
    return {item["id"] for item in taxonomy["events"]}


def fail(message: str) -> None:
    print(f"manifest invalid: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    manifest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "manifest_template.csv"
    events = load_events()
    with manifest.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            fail(f"missing columns: {sorted(missing)}")
        for line_number, row in enumerate(reader, start=2):
            if row["event_id"] not in events:
                fail(f"line {line_number}: unknown event_id {row['event_id']!r}")
            if row["case_type"] not in {"positive", "negative", "boundary"}:
                fail(f"line {line_number}: invalid case_type {row['case_type']!r}")
            if row["split"] not in {"train", "val", "test", "candidate"}:
                fail(f"line {line_number}: invalid split {row['split']!r}")
            for key in ("has_bbox", "has_region", "has_sequence", "can_train", "can_show_customer"):
                if row.get(key) not in {"true", "false"}:
                    fail(f"line {line_number}: {key} must be true or false")
    print(f"manifest valid: {manifest}")


if __name__ == "__main__":
    main()
