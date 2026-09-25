#!/usr/bin/env python3
"""Re-derive the published Direct QA "active" scores from a single judge.

Every answer in docs/data/direct_qa/models/*.json keeps each judge's own 0-4
score. This script makes one judge authoritative: it sets each answer's
active_score from that judge, recomputes every model summary (overall, Part 1,
Part 2, per rollout, and per rollout within each part), writes the model files
and docs/data/direct_qa/index.json, and re-ranks the index by the new overall
score. The other judges' scores stay in the files for audit.

Run tools/aggregate_questions.js afterwards to refresh the per-question files.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/data/direct_qa"
PARTS = ("part1", "part2")


def summarize(scores: list[float]) -> dict:
    """Summary block in the published schema for a list of 0-4 answer scores."""
    n = len(scores)
    mean = sum(scores) / n if n else 0.0
    dist = Counter(scores)
    return {
        "response_count": n,
        "correct_count": sum(1 for s in scores if s == 4),
        "incorrect_count": sum(1 for s in scores if s < 4),
        "partial_credit_count": sum(1 for s in scores if 0 < s < 4),
        "zero_count": sum(1 for s in scores if s == 0),
        "mean_score_0_to_4": mean,
        "score_percent": mean / 4 * 100,
        "score_distribution": {_score_key(s): dist[s] for s in sorted(dist)},
    }


def _score_key(score: float) -> str:
    return str(int(score)) if float(score).is_integer() else str(score)


def _plain(score: float) -> int | float:
    return int(score) if float(score).is_integer() else score


def apply(model: dict, judge: str) -> None:
    by_part: dict[str, list[float]] = {p: [] for p in PARTS}
    by_rollout: dict[str, list[float]] = {}
    by_rollout_part: dict[str, dict[str, list[float]]] = {p: {} for p in PARTS}
    for answer in model["answers"]:
        score = answer["scores"][judge]["score_0_to_4"]
        answer["active_score"] = {
            "policy": judge,
            "score_0_to_4": _plain(score),
            "score_percent": _plain(score / 4 * 100),
            "is_full_credit": score == 4,
        }
        rollout = str(answer["rollout"])
        by_part[answer["part"]].append(score)
        by_rollout.setdefault(rollout, []).append(score)
        by_rollout_part[answer["part"]].setdefault(rollout, []).append(score)

    summary = model["summary"]
    overall = [s for p in PARTS for s in by_part[p]]
    for key, scores in (("overall", overall), *((p, by_part[p]) for p in PARTS)):
        active = summarize(scores)
        # The judge's own block was computed upstream from the same answers.
        if summary["scores"][key][judge] != active:
            raise ValueError(f"{model['model_key']} {key}: recomputed scores disagree with {judge} summary")
        summary["scores"][key]["active"] = active
    summary["by_rollout"] = {r: summarize(by_rollout[r]) for r in sorted(by_rollout, key=int)}
    summary["by_rollout_part"] = {
        p: {r: summarize(v) for r, v in sorted(by_rollout_part[p].items(), key=lambda kv: int(kv[0]))}
        for p in PARTS
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--judge", default="deepseek_v4_pro", help="judge key whose scores become the active scores")
    args = parser.parse_args()

    index_path = DATA / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    known_keys = {entry["model_key"] for entry in index["models"]}
    for model_path in sorted((DATA / "models").glob("*.json")):
        if model_path.stem in known_keys:
            continue
        model = json.loads(model_path.read_text(encoding="utf-8"))
        if model["model_key"] != model_path.stem:
            raise ValueError(f"model key does not match filename: {model_path}")
        index["models"].append({
            key: model.get(key)
            for key in ("model_key", "display_name", "provider", "evaluation_model_ids", "thinking_effort", "configuration_note", "mode")
        } | {"detail_file": f"models/{model_path.name}"})
        known_keys.add(model_path.stem)
    for entry in index["models"]:
        model_path = DATA / entry["detail_file"]
        model = json.loads(model_path.read_text(encoding="utf-8"))
        apply(model, args.judge)
        write_json(model_path, model)
        entry["summary"] = model["summary"]

    # Stable sort keeps the previous order for ties.
    index["models"].sort(key=lambda m: -m["summary"]["scores"]["overall"]["active"]["score_percent"])
    index["benchmark"]["active_score_policy"] = args.judge
    index["generated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(index_path, index)
    print(f"Active scores now come from {args.judge} for {len(index['models'])} models")


if __name__ == "__main__":
    main()
