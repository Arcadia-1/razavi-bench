#!/usr/bin/env python3
"""Build docs/data/direct_qa/models/gpt_6_1_sol.json for the 2026-10-01 run.

Merges the public answer JSONL files, the DeepSeek V4 Pro judge scores, and the
public token manifest into the razavi-bench.direct-qa model schema. Run
tools/apply_active_judge.py afterwards to derive the active score, per-rollout
summaries, and index.json entry.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODEL_KEY = "gpt_6_1_sol"
EXPERIMENT_DIR = ROOT / "experiments/2026-10-01-direct-qa"


def load_summarize():
    spec = importlib.util.spec_from_file_location(
        "apply_active_judge", ROOT / "tools/apply_active_judge.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize


def question_text(instruction: str) -> str:
    marker = "## Question"
    if marker in instruction:
        text = instruction.split(marker, 1)[1]
        for end_marker in ("## Figures", "## Notes", "## Instructions"):
            if end_marker in text:
                text = text.split(end_marker, 1)[0]
        return text.strip()
    return instruction.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_answers() -> list[dict]:
    rows: list[dict] = []
    for rollout in (1, 2, 3):
        path = EXPERIMENT_DIR / f"model_outputs/openrouter-gpt-6-1-sol-reasoning-max-rollout-{rollout}.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_scores() -> dict[tuple[str, int], dict]:
    path = (
        EXPERIMENT_DIR
        / "judge_outputs/openrouter-deepseek-v4-pro-no-thinking-20261001"
        / "openrouter-gpt-6-1-sol.scores.jsonl"
    )
    scores: dict[tuple[str, int], dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rollout = int(row["answer_metadata"]["rollout"])
        scores[(row["task_slug"], rollout)] = row
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / f"docs/data/direct_qa/models/{MODEL_KEY}.json",
    )
    args = parser.parse_args()

    summarize = load_summarize()
    answers = load_answers()
    scores = load_scores()
    tokens_manifest = json.loads(
        (EXPERIMENT_DIR / "model_outputs/openrouter-gpt-6-1-sol-tokens.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(answers) == 150, len(answers)
    assert len(scores) == 150, len(scores)

    merged: list[dict] = []
    for row in answers:
        slug = row["task_slug"]
        task_path = row["task_path"]
        rollout = int(row["rollout"])
        judge = scores[(slug, rollout)]
        if sha256_text(row["answer"]) != judge["answer_sha256"]:
            raise SystemExit(f"answer hash mismatch for {slug} rollout {rollout}")
        tokens = tokens_manifest[f"{rollout}:{slug}"]
        figures = [
            f"{task_path}/{name}" for name in sorted(row.get("figures") or [])
        ]
        attempts = int(row.get("model_call_attempts") or 1)
        merged.append(
            {
                "question_id": slug,
                "part": slug.split("-", 1)[0],
                "question_number": int(slug.split("-")[1]),
                "question": question_text(row["question"]),
                "figures": figures,
                "rollout": rollout,
                "configuration": {
                    "model_id": None,
                    "thinking_effort": "max",
                    "api_model": "openai/gpt-6.1-sol",
                    "route": "openrouter_chat_completions",
                },
                "answer": {
                    "text": row["answer"],
                    "format": "markdown",
                    "sha256": sha256_text(row["answer"]),
                },
                "model_call_count": attempts,
                "internet_or_tool_evidence": bool(row.get("internet_or_tool_evidence")),
                "source_experiment": "2026-10-01-direct-qa-openrouter-gpt-6-1-sol-reasoning-max",
                "scores": {
                    "deepseek_v4_pro": {
                        "score_0_to_4": judge["score_0_to_4"],
                        "is_full_credit": judge["score_0_to_4"] == 4,
                        "rationale": judge["rationale"],
                        "golden_solution_sha256": judge["golden_solution_sha256"],
                        "rubric_sha256": judge["rubric_sha256"],
                    }
                },
                "tokens": tokens,
                "selected_response_tokens": dict(tokens),
                "attempt_count": 1,
            }
        )
    merged.sort(key=lambda a: (a["part"], a["question_number"], a["rollout"]))

    scores_by_part = {
        "overall": [a["scores"]["deepseek_v4_pro"]["score_0_to_4"] for a in merged],
        "part1": [a["scores"]["deepseek_v4_pro"]["score_0_to_4"] for a in merged if a["part"] == "part1"],
        "part2": [a["scores"]["deepseek_v4_pro"]["score_0_to_4"] for a in merged if a["part"] == "part2"],
    }
    totals = {
        key: sum(a["tokens"][key] or 0 for a in merged)
        for key in ("cached_input_tokens", "input_tokens", "output_tokens", "total_tokens")
    }
    missing_usage = sum(
        1
        for a in merged
        if any(a["tokens"][key] is None for key in ("input_tokens", "output_tokens", "total_tokens"))
    )
    missing_cached = sum(1 for a in merged if a["tokens"]["cached_input_tokens"] is None)

    model = {
        "model_key": MODEL_KEY,
        "display_name": "GPT-6.1 Sol",
        "provider": "openai",
        "evaluation_model_ids": [],
        "thinking_effort": "max",
        "configuration_note": (
            "GPT-6.1 Sol answered all 50 tasks in three rollouts through OpenRouter's "
            "OpenAI-compatible chat completions route at maximum reasoning effort. "
            "Answers were graded by DeepSeek V4 Pro through OpenRouter with reasoning "
            "disabled. Cost uses OpenRouter's published GPT-6.1 Sol API price "
            "($2 input, $0.10 cached input, $10 output per 1M tokens)."
        ),
        "mode": "direct_qa",
        "summary": {
            "rollout_count": 3,
            "answer_count": len(merged),
            "scores": {
                key: {"deepseek_v4_pro": summarize(values)}
                for key, values in scores_by_part.items()
            },
            "by_rollout": {},
            "tokens": {
                "response_count": len(merged),
                "usage_record_count": len(merged),
                "complete_usage_count": len(merged) - missing_usage,
                "missing_usage_count": missing_usage,
                "missing_cached_input_count": missing_cached,
                "complete": missing_usage == 0 and missing_cached == 0,
                "totals": totals,
                "known_totals": dict(totals),
            },
            "by_rollout_part": {"part1": {}, "part2": {}},
        },
        "answers": merged,
    }
    args.output.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"wrote {args.output} with {len(merged)} answers; "
        f"overall={scores_by_part['overall'] and sum(scores_by_part['overall'])/len(scores_by_part['overall'])/4*100:.2f}%"
    )


if __name__ == "__main__":
    main()
