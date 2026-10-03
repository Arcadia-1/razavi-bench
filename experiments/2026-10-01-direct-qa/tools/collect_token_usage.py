#!/usr/bin/env python3
"""Collect the public token manifest for the 2026-10-01 GPT-6.1 Sol run.

Reads the raw OpenRouter responses retained outside the repository and writes
one numeric usage record per answer next to the public answer JSONL files.
Response bodies, hidden reasoning, and costs are never copied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def usage_record(response: dict) -> dict:
    usage = response.get("usage") or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    record = {
        "cached_input_tokens": prompt_details.get("cached_tokens"),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cache_creation_input_tokens": None,
        "reasoning_output_tokens": completion_details.get("reasoning_tokens"),
    }
    missing = [
        key
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if record[key] is None
    ]
    record["complete"] = not missing
    record["availability"] = "complete" if not missing else "partial"
    record["missing_fields"] = missing
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, required=True, help="directory with rollout-*/<task_slug>.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest: dict[str, dict] = {}
    for path in sorted(args.raw_dir.glob("rollout-*/*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        task_slug = Path(raw["task_path"]).name
        manifest[f"{raw['rollout']}:{task_slug}"] = usage_record(raw["response"])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(manifest)} token records to {args.output}")


if __name__ == "__main__":
    main()
