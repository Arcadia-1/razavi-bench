#!/usr/bin/env python3
"""Build public Direct QA summaries from per-answer judge scores."""

import csv
import json
from collections import defaultdict
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parents[1]
REPO = EXPERIMENT.parents[1]
JUDGE_OUTPUTS = EXPERIMENT / "judge_outputs"
SCORES = EXPERIMENT / "judge_scores"
MODELS = {
    "GPT-5.2": "disabled",
    "Claude Sonnet 4.6": "disabled",
    "Doubao Seed 2.1 Pro": "default",
    "GPT-4o": "default",
    "GPT-5.3": "default",
    "Grok 4.5": "default",
    "Gemini 3.6 Flash": "default",
    "Inkling Small": "default",
    "Inkling": "disabled",
    "Llama 4 Maverick": "default",
    "Qwen 3.7 Flash": "default",
    "Qwen 3.7 Plus": "default",
    "Step 3.7 Flash": "default",
    "GPT-5.6 Terra": "max",
}
JUDGES = {"MiniMax-M3": "MiniMax M3", "deepseek-v4-pro": "DeepSeek V4 Pro"}
PARTS = {"part1-": "part1", "part2-": "part2"}


def load(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def part(slug):
    for prefix, name in PARTS.items():
        if slug.startswith(prefix):
            return name
    raise ValueError(slug)


def mean(values):
    return sum(values) / len(values)


def main():
    values = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    score_paths = sorted((JUDGE_OUTPUTS / "minimax-m3-vela-20260801").glob("*.scores.jsonl"))
    score_paths += sorted((JUDGE_OUTPUTS / "minimax-m3-openai-20260801").glob("*.scores.jsonl"))
    score_paths += sorted((JUDGE_OUTPUTS / "deepseek-v4-pro-20260801").glob("*.scores.jsonl"))
    for path in score_paths:
        for row in load(path):
            if row.get("parse_error") or row.get("score_0_to_4") is None:
                raise ValueError(f"invalid score: {path}")
            metadata = row["answer_metadata"]
            model, judge, rollout = metadata["model_name"], row["judge_model"], int(metadata["rollout"])
            if model not in MODELS or judge not in JUDGES:
                raise ValueError(f"unexpected model/judge: {model}/{judge}")
            values[model][judge][rollout][part(row["task_slug"])].append(int(row["score_0_to_4"]))

    summary, aggregate = [], []
    for model in sorted(values):
        judge_means = {}
        for judge in JUDGES:
            rollups = values[model][judge]
            if sorted(rollups) != [1, 2, 3]:
                raise ValueError(f"missing rollout: {model}/{judge}")
            per_rollout = []
            for rollout in (1, 2, 3):
                p1, p2 = rollups[rollout]["part1"], rollups[rollout]["part2"]
                if len(p1) != 30 or len(p2) != 20:
                    raise ValueError(f"incomplete scores: {model}/{judge}/r{rollout}")
                row = {"model": model, "judge": JUDGES[judge], "rollout": rollout,
                       "part1": mean(p1) * 25, "part2": mean(p2) * 25,
                       "overall": mean(p1 + p2) * 25}
                summary.append(row)
                per_rollout.append(row)
            judge_means[judge] = {metric: mean([row[metric] for row in per_rollout]) for metric in ("part1", "part2", "overall")}
            aggregate.append({"model": model, "judge": JUDGES[judge], **judge_means[judge]})
        combined = {metric: mean([judge_means[judge][metric] for judge in JUDGES]) for metric in ("part1", "part2", "overall")}
        aggregate.append({"model": model, "judge": "Mean of DeepSeek and MiniMax", **combined})

    write_csv(SCORES / "summary.csv", ["model", "judge", "rollout", "part1", "part2", "overall"], summary)
    write_csv(SCORES / "aggregate.csv", ["model", "judge", "part1", "part2", "overall"], aggregate)
    index = json.loads((REPO / "docs/data/direct_qa/index.json").read_text(encoding="utf-8"))
    comparison_rows = []
    for model in index["models"]:
        scores = model["summary"]["scores"]
        comparison_rows.append({
            "rank": "",
            "model": model["display_name"],
            "thinking_effort": model["thinking_effort"],
            "part1": scores["part1"]["active"]["score_percent"],
            "part2": scores["part2"]["active"]["score_percent"],
            "overall": scores["overall"]["active"]["score_percent"],
        })
    comparison_rows.sort(key=lambda row: float(row["overall"]), reverse=True)
    for rank, row in enumerate(comparison_rows, 1):
        row["rank"] = rank
    write_csv(SCORES / "comparison.csv", ["rank", "model", "thinking_effort", "part1", "part2", "overall"], comparison_rows)
    print(json.dumps({"models": len(values), "comparison_rows": len(comparison_rows)}, indent=2))


if __name__ == "__main__":
    main()
