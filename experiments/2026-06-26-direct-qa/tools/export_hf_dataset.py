#!/usr/bin/env python3
"""Export Hugging Face Dataset Viewer friendly JSONL files."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
EXPERIMENT_DIR = ROOT / "experiments" / "2026-06-26-direct-qa"
FINAL_DEEPSEEK_SCORES = (
    EXPERIMENT_DIR / "judge_outputs" / "deepseek-v4-pro-20260630-123714.jsonl"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def export_tasks() -> None:
    rows = []
    for instruction_path in sorted((ROOT / "tasks").glob("*/instruction.md")):
        task_dir = instruction_path.parent
        slug = task_dir.name
        match = re.match(r"part(?P<part>[12])-(?P<number>\d{3})-", slug)
        if not match:
            raise ValueError(f"Unexpected task slug: {slug}")

        figures = [
            str(path.relative_to(ROOT))
            for path in sorted(task_dir.glob("figure-*.png"))
        ]
        rows.append(
            {
                "benchmark": "razavi-bench",
                "task_slug": slug,
                "part": f"part{match.group('part')}",
                "question_number": int(match.group("number")),
                "task_path": str(task_dir.relative_to(ROOT)),
                "instruction": read_text(instruction_path),
                "golden_solution": read_text(task_dir / "golden_solution.md"),
                "figures": figures,
            }
        )

    write_jsonl(DATA_DIR / "tasks.jsonl", rows)


def export_model_answers() -> None:
    rows = []
    for family in ("claude", "gemini", "gpt"):
        for rollout in (1, 2, 3):
            path = EXPERIMENT_DIR / "model_outputs" / f"{family}-rollout-{rollout}.jsonl"
            with path.open(encoding="utf-8") as f:
                rows.extend(json.loads(line) for line in f)

    rows.sort(key=lambda row: (row["model_family"], row["rollout"], row["task_slug"]))
    write_jsonl(DATA_DIR / "model_answers_2026-06-26-direct-qa.jsonl", rows)


def export_final_scores() -> None:
    rows = []
    with FINAL_DEEPSEEK_SCORES.open(encoding="utf-8") as f:
        rows.extend(json.loads(line) for line in f)

    rows.sort(
        key=lambda row: (
            row["answer_model_family"],
            row["rollout"],
            row["task_slug"],
        )
    )
    write_jsonl(
        DATA_DIR / "judge_scores_deepseek-v4-pro-20260630-123714.jsonl",
        rows,
    )


def main() -> None:
    export_tasks()
    export_model_answers()
    export_final_scores()


if __name__ == "__main__":
    main()
