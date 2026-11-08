#!/usr/bin/env python3
"""Replace the GPT-6 Luna scores of Part 1 Q2 and Q22 in every published model file.

Reads gpt-6-luna-max.scores.jsonl (written by tools/evaluate_answers.py from
judge_input.jsonl), checks that each score belongs to the published answer (same
task, rollout and answer SHA-256), replaces answers[].scores.gpt_6_luna_max for those
slots, and recomputes the judge's per-part summaries. Every other score is kept.
Run tools/apply_active_judge.py and tools/aggregate_questions.js afterwards.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODELS = ROOT / "docs/data/direct_qa/models"
JUDGE_KEY, JUDGE_MODEL = "gpt_6_luna_max", "openai/gpt-6-luna"
SLUGS = {
    "part1-002-student-says-transconductance-mosfet-goes-up-as",
    "part1-022-explain-why-miller-effect-less-pronounced-cascode",
}
PARTS = ("part1", "part2")


def load_summarize():
    spec = importlib.util.spec_from_file_location("apply_active_judge", ROOT / "tools/apply_active_judge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize


def main() -> None:
    summarize = load_summarize()
    scores: dict[tuple[str, str, int], dict] = {}
    for line in (HERE / "gpt-6-luna-max.scores.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("score_0_to_4") is None:
            raise SystemExit(f"unscored row: {row['source_key']} ({row.get('parse_error')})")
        meta = row["answer_metadata"]
        scores[(meta["model_name"], row["task_slug"], int(meta["rollout"]))] = row
    used = 0
    for path in sorted(MODELS.glob("*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
        changed = []
        for answer in model["answers"]:
            if answer["question_id"] not in SLUGS:
                continue
            row = scores.get((model["model_key"], answer["question_id"], int(answer["rollout"])))
            if row is None:
                raise SystemExit(f"{model['model_key']}: no new score for {answer['question_id']} rollout {answer['rollout']}")
            if row["answer_sha256"] != hashlib.sha256(answer["answer"]["text"].encode("utf-8")).hexdigest():
                raise SystemExit(f"{model['model_key']}: answer hash mismatch for {answer['question_id']} rollout {answer['rollout']}")
            old = answer["scores"][JUDGE_KEY]["score_0_to_4"]
            answer["scores"][JUDGE_KEY] = {
                "score_0_to_4": row["score_0_to_4"],
                "is_full_credit": row["score_0_to_4"] == 4,
                "rationale": row.get("rationale", ""),
                "judge_model": JUDGE_MODEL,
                "golden_solution_sha256": row["golden_solution_sha256"],
                "rubric_sha256": row["rubric_sha256"],
            }
            changed.append(row["score_0_to_4"] - old)
            used += 1
        by_part = {p: [a["scores"][JUDGE_KEY]["score_0_to_4"] for a in model["answers"] if a["part"] == p] for p in PARTS}
        for key, values in (("overall", by_part["part1"] + by_part["part2"]), *by_part.items()):
            model["summary"]["scores"][key][JUDGE_KEY] = summarize(values)
        path.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{model['model_key']:36s} {sum(changed):+d} points over {len(changed)} answers")
    if used != len(scores):
        raise SystemExit(f"{len(scores) - used} scores were not used")


if __name__ == "__main__":
    main()
