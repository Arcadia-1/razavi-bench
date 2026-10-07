#!/usr/bin/env python3
"""Build docs/data/direct_qa/models/<model_key>.json from a finished Direct QA run.

Merges the public answer JSONL files, one judge's score JSONL, and per-answer
token usage into the razavi-bench.direct-qa model schema. Token usage comes
either from the runner's local raw_logs.jsonl (--raw-log) or from a public
manifest keyed "<rollout>:<task_slug>" (--tokens). Every task must be answered
and scored in every rollout, and each score must match its answer's SHA-256.

Run tools/apply_active_judge.py and tools/aggregate_questions.js afterwards to
derive the active score, per-rollout summaries, and index.json entry.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNANSWERED_RATIONALE = (
    "No answer: every attempt ended without a final answer (for example, reasoning used the "
    "whole max_tokens budget), so this slot scores 0 without being sent to the judge."
)
TOKEN_KEYS = ("cached_input_tokens", "input_tokens", "output_tokens", "total_tokens")


def load_summarize():
    spec = importlib.util.spec_from_file_location(
        "apply_active_judge", ROOT / "tools/apply_active_judge.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def question_text(instruction: str) -> str:
    """Return just the question, whether given a full instruction.md or the runner's
    question field (which already starts after "## Question" but keeps "## Figures")."""
    marker = "## Question"
    text = instruction.split(marker, 1)[1] if marker in instruction else instruction
    for end_marker in ("## Figures", "## Notes", "## Instructions"):
        if end_marker in text:
            text = text.split(end_marker, 1)[0]
    return text.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def usage_record(usage: dict) -> dict:
    """Convert an OpenAI-style usage object into the published token record."""
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


def sum_usage(records: list[dict]) -> dict:
    total = usage_record({})
    for key in ("cached_input_tokens", "input_tokens", "output_tokens", "total_tokens", "reasoning_output_tokens"):
        values = [record[key] for record in records]
        total[key] = None if any(value is None for value in values) else sum(values)
    missing = [key for key in ("input_tokens", "output_tokens", "total_tokens") if total[key] is None]
    total["complete"] = not missing
    total["availability"] = "complete" if not missing else "partial"
    total["missing_fields"] = missing
    return total


def load_tokens(args: argparse.Namespace) -> dict[str, tuple[dict, dict, int]]:
    """Map "<rollout>:<task_slug>" to (billed tokens, selected-response tokens, attempt count).

    Billed tokens include retried attempts (e.g. answers truncated at max_tokens),
    so the published cost covers every call the run paid for.
    """
    if args.tokens:
        manifest = json.loads(args.tokens.read_text(encoding="utf-8"))
        return {key: (record, dict(record), 1) for key, record in manifest.items()}
    tokens: dict[str, tuple[dict, dict, int]] = {}
    failed: dict[str, list[dict]] = {}
    for row in read_jsonl(args.raw_log):
        key = f"{row['rollout']}:{row['task_slug']}"
        attempts = [a for a in row.get("attempts") or [] if a.get("status") == 200]
        if not row.get("ok"):
            # Older raw rows keep usage only on the row; newer ones keep it per attempt.
            usages = [a["usage"] for a in attempts if "usage" in a] or [row.get("usage") or {}]
            failed.setdefault(key, []).extend(usage_record(u) for u in usages)
            continue
        selected = usage_record(row.get("usage") or {})
        earlier = [usage_record(a.get("usage") or {}) for a in attempts[:-1]]
        billed = sum_usage(earlier + [selected]) if earlier else selected
        tokens[f"{row['rollout']}:{row['task_slug']}"] = (billed, dict(selected), max(len(attempts), 1))
    # A slot whose every attempt failed still cost tokens; bill them for --unanswered.
    for key, records in failed.items():
        if key not in tokens:
            tokens[key] = (sum_usage(records), dict(records[-1]), len(records))
    return tokens


def load_scores(path: Path) -> dict[tuple[str, int], dict]:
    scores: dict[tuple[str, int], dict] = {}
    for row in read_jsonl(path):
        rollout = int(row["answer_metadata"]["rollout"])
        scores[(row["task_slug"], rollout)] = row
    return scores


def build(args: argparse.Namespace) -> dict:
    summarize = load_summarize()
    answers = [row for path in args.answers for row in read_jsonl(path)]
    scores = load_scores(args.scores)
    tokens_manifest = load_tokens(args)

    tasks = {row["task_slug"]: row for row in read_jsonl(ROOT / "data/tasks.jsonl")}
    task_slugs = set(tasks)
    rollouts = sorted({int(row["rollout"]) for row in answers})
    unanswered = set()
    for item in args.unanswered:
        rollout, slug = item.split(":", 1)
        if slug not in tasks or (slug, int(rollout)) in {(r["task_slug"], int(r["rollout"])) for r in answers}:
            raise SystemExit(f"--unanswered {item} is not an unanswered task slot")
        unanswered.add((slug, int(rollout)))
        task = tasks[slug]
        answers.append(
            {
                "task_slug": slug,
                "task_path": task["task_path"],
                "rollout": int(rollout),
                "question": task["instruction"],
                "figures": task.get("figures") or [],
                "answer": "",
                "model_call_attempts": tokens_manifest.get(f"{rollout}:{slug}", ({}, {}, 1))[2],
            }
        )
        reference = next((row for (s, _), row in scores.items() if s == slug), None)
        if reference is None:
            raise SystemExit(f"no scored answer to {slug} to take its golden-solution hash from")
        scores[(slug, int(rollout))] = {
            "answer_sha256": sha256_text(""),
            "score_0_to_4": 0,
            "rationale": UNANSWERED_RATIONALE,
            "golden_solution_sha256": reference["golden_solution_sha256"],
            "rubric_sha256": reference["rubric_sha256"],
        }
    expected = {(slug, rollout) for slug in task_slugs for rollout in rollouts}
    answered = {(row["task_slug"], int(row["rollout"])) for row in answers}
    if len(answered) != len(answers):
        raise SystemExit("duplicate answers for the same task and rollout")
    problems = {
        "missing answers": expected - answered,
        "missing scores": expected - set(scores),
        "missing token usage": {
            key for key in expected if f"{key[1]}:{key[0]}" not in tokens_manifest
        },
        "unscored judge rows": {
            key for key, row in scores.items() if key in expected and row.get("score_0_to_4") is None
        },
    }
    for label, keys in problems.items():
        if keys:
            sample = ", ".join(f"{slug} r{rollout}" for slug, rollout in sorted(keys)[:5])
            raise SystemExit(f"{len(keys)} {label} (e.g. {sample})")

    merged: list[dict] = []
    for row in answers:
        slug = row["task_slug"]
        task_path = row["task_path"]
        rollout = int(row["rollout"])
        judge = scores[(slug, rollout)]
        if sha256_text(row["answer"]) != judge["answer_sha256"]:
            raise SystemExit(f"answer hash mismatch for {slug} rollout {rollout}")
        tokens, selected_tokens, attempt_count = tokens_manifest[f"{rollout}:{slug}"]
        figures = [
            name if name.startswith(task_path + "/") else f"{task_path}/{name}"
            for name in sorted(row.get("figures") or [])
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
                    "thinking_effort": args.effort,
                    "api_model": args.api_model,
                    "route": args.route,
                },
                "answer": {
                    "text": row["answer"],
                    "format": "markdown",
                    "sha256": sha256_text(row["answer"]),
                },
                "model_call_count": attempts,
                "internet_or_tool_evidence": bool(row.get("internet_or_tool_evidence")),
                "source_experiment": args.source_experiment,
                "scores": {
                    args.judge_key: {
                        "score_0_to_4": judge["score_0_to_4"],
                        "is_full_credit": judge["score_0_to_4"] == 4,
                        "rationale": judge["rationale"],
                        "golden_solution_sha256": judge["golden_solution_sha256"],
                        "rubric_sha256": judge["rubric_sha256"],
                    }
                },
                "tokens": tokens,
                "selected_response_tokens": selected_tokens,
                "attempt_count": attempt_count,
            }
        )
    merged.sort(key=lambda a: (a["part"], a["question_number"], a["rollout"]))

    def part_scores(part: str | None) -> list[int]:
        return [
            a["scores"][args.judge_key]["score_0_to_4"]
            for a in merged
            if part is None or a["part"] == part
        ]

    scores_by_part = {
        "overall": part_scores(None),
        "part1": part_scores("part1"),
        "part2": part_scores("part2"),
    }
    totals = {key: sum(a["tokens"][key] or 0 for a in merged) for key in TOKEN_KEYS}
    missing_usage = sum(
        1
        for a in merged
        if any(a["tokens"][key] is None for key in ("input_tokens", "output_tokens", "total_tokens"))
    )
    missing_cached = sum(1 for a in merged if a["tokens"]["cached_input_tokens"] is None)

    return {
        "model_key": args.model_key,
        "display_name": args.display_name,
        "provider": args.provider,
        "evaluation_model_ids": [],
        "thinking_effort": args.effort,
        "configuration_note": args.configuration_note,
        "mode": "direct_qa",
        "summary": {
            "rollout_count": len(rollouts),
            "answer_count": len(merged),
            "scores": {
                key: {args.judge_key: summarize(values)}
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-key", required=True, help="e.g. gpt_6_1_sol; also the output file name")
    parser.add_argument("--display-name", required=True, help='e.g. "GPT-6.1 Sol"')
    parser.add_argument("--provider", required=True, help="e.g. openai, google, anthropic")
    parser.add_argument("--effort", required=True, help="reasoning effort shown on the site, e.g. max or high")
    parser.add_argument("--api-model", required=True, help="provider model id, e.g. openai/gpt-6.1-sol")
    parser.add_argument("--route", default="openrouter_chat_completions")
    parser.add_argument("--source-experiment", required=True)
    parser.add_argument("--configuration-note", required=True, help="how the run was configured and priced")
    parser.add_argument("--answers", type=Path, action="append", required=True, help="answer JSONL; repeat once per rollout")
    parser.add_argument("--scores", type=Path, required=True, help="judge score JSONL from evaluate_answers.py")
    parser.add_argument("--judge-key", default="deepseek_v4_pro")
    usage = parser.add_mutually_exclusive_group(required=True)
    usage.add_argument("--raw-log", type=Path, help="raw_logs.jsonl written by direct_qa_openrouter.py")
    usage.add_argument("--tokens", type=Path, help='token manifest keyed "<rollout>:<task_slug>"')
    parser.add_argument(
        "--unanswered",
        action="append",
        default=[],
        metavar="ROLLOUT:TASK_SLUG",
        help="publish this slot as unanswered with score 0 after every retry failed; repeatable",
    )
    parser.add_argument("--output", type=Path, help="defaults to docs/data/direct_qa/models/<model_key>.json")
    args = parser.parse_args()

    model = build(args)
    output = args.output or ROOT / f"docs/data/direct_qa/models/{args.model_key}.json"
    output.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overall = model["summary"]["scores"]["overall"][args.judge_key]
    print(f"wrote {output} with {len(model['answers'])} answers; overall={overall}")


if __name__ == "__main__":
    main()
