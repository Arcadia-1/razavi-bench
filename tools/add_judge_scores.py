#!/usr/bin/env python3
"""Add one judge's scores to the published Direct QA model files.

Reads score JSONL written by tools/evaluate_answers.py, one file per model named
<model_key><suffix> in --scores-dir, and stores them in
docs/data/direct_qa/models/<model_key>.json under answers[].scores[<judge-key>],
with the matching per-part summaries. Each score must belong to the published
answer (same task, rollout and answer SHA-256). Slots published as unanswered
(empty answer text) score 0 without a judge call.

Run tools/apply_active_judge.py --judge <judge-key> afterwards to make the judge
authoritative, then tools/aggregate_questions.js.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "docs/data/direct_qa/models"
PARTS = ("part1", "part2")
UNANSWERED_RATIONALE = (
    "No answer: every attempt ended without a final answer, so this slot scores 0 "
    "without being sent to the judge."
)


def load_summarize():
    spec = importlib.util.spec_from_file_location("apply_active_judge", ROOT / "tools/apply_active_judge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_scores(model: dict, rows: list[dict], judge_key: str, judge_model: str, summarize) -> None:
    by_slot = {}
    for row in rows:
        if row.get("score_0_to_4") is None:
            raise SystemExit(f"{model['model_key']}: unscored row for {row['task_slug']} ({row.get('parse_error')})")
        by_slot[(row["task_slug"], int(row["answer_metadata"]["rollout"]))] = row
    reference = next(iter(by_slot.values()))
    scores_by_part: dict[str, list[float]] = {p: [] for p in PARTS}
    for answer in model["answers"]:
        text = answer["answer"]["text"]
        slot = (answer["question_id"], int(answer["rollout"]))
        if not text.strip():
            score, rationale = 0, UNANSWERED_RATIONALE
            golden, rubric = reference["golden_solution_sha256"], reference["rubric_sha256"]
            golden = next((r["golden_solution_sha256"] for (slug, _), r in by_slot.items() if slug == slot[0]), golden)
        else:
            row = by_slot.get(slot)
            if row is None:
                raise SystemExit(f"{model['model_key']}: no {judge_key} score for {slot}")
            if row["answer_sha256"] != sha256_text(text):
                raise SystemExit(f"{model['model_key']}: answer hash mismatch for {slot}")
            score, rationale = row["score_0_to_4"], row.get("rationale", "")
            golden, rubric = row["golden_solution_sha256"], row["rubric_sha256"]
        answer["scores"][judge_key] = {
            "score_0_to_4": score,
            "is_full_credit": score == 4,
            "rationale": rationale,
            "judge_model": judge_model,
            "golden_solution_sha256": golden,
            "rubric_sha256": rubric,
        }
        scores_by_part[answer["part"]].append(score)
    overall = [s for p in PARTS for s in scores_by_part[p]]
    for key, values in (("overall", overall), *((p, scores_by_part[p]) for p in PARTS)):
        model["summary"]["scores"][key][judge_key] = summarize(values)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--judge-key", required=True, help="key stored under answers[].scores, e.g. gpt_6_luna_max")
    parser.add_argument("--judge-model", required=True, help="judge model id, e.g. openai/gpt-6-luna")
    parser.add_argument("--scores-dir", type=Path, required=True)
    parser.add_argument("--suffix", default=".jsonl", help="score file name after the model key")
    parser.add_argument("--model-key", action="append", default=[], help="limit to these models (default: every published model)")
    args = parser.parse_args()

    summarize = load_summarize()
    keys = args.model_key or sorted(path.stem for path in MODELS.glob("*.json"))
    for key in keys:
        path = args.scores_dir / f"{key}{args.suffix}"
        if not path.exists():
            raise SystemExit(f"missing scores for {key}: {path}")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        model_path = MODELS / f"{key}.json"
        model = json.loads(model_path.read_text(encoding="utf-8"))
        add_scores(model, rows, args.judge_key, args.judge_model, summarize)
        model_path.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{key}: {model['summary']['scores']['overall'][args.judge_key]['score_percent']:.2f}%")


if __name__ == "__main__":
    main()
