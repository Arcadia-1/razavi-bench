#!/usr/bin/env python3
"""Build the homepage release-date lookup from the canonical CSV and ranking."""

import argparse
import csv
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "docs/data/direct_qa/index.json"
DEFAULT_DATES = ROOT / "docs/data/direct_qa/model_release_dates.csv"
DEFAULT_OUTPUT = ROOT / "docs/data/direct_qa/model_release_dates.json"


def write_dates(index_path: Path, dates_path: Path, output_path: Path) -> int:
    models = json.loads(index_path.read_text())["models"]
    model_names = {model["model_key"]: model["display_name"] for model in models}
    if len(model_names) != len(models):
        raise ValueError("Duplicate model keys in ranking")

    with dates_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    dates = {}
    for row in rows:
        key = row["model_key"]
        if key in dates:
            raise ValueError(f"Duplicate release date for {key}")
        if key in model_names and row["display_name"] != model_names[key]:
            raise ValueError(f"Display-name mismatch for {key}")
        dates[key] = date.fromisoformat(row["release_date"]).isoformat()

    missing = sorted(set(model_names) - set(dates))
    extra = sorted(set(dates) - set(model_names))
    if missing or extra:
        raise ValueError(f"Release-date coverage mismatch: missing={missing}, extra={extra}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dates, indent=2, sort_keys=True) + "\n")
    return len(dates)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--dates", type=Path, default=DEFAULT_DATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    count = write_dates(args.index, args.dates, args.output)
    print(f"wrote {args.output} ({count} dates)")


if __name__ == "__main__":
    main()
