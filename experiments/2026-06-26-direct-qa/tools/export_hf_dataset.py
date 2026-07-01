#!/usr/bin/env python3
"""Export the Hugging Face Dataset Viewer task table."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
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


def main() -> None:
    export_tasks()


if __name__ == "__main__":
    main()
