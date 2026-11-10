#!/usr/bin/env python3
"""Write data/tasks.jsonl and docs/data/tasks.jsonl from tasks/.

One row per task. `prompt` is exactly the text a model is sent: the "## Question"
section of instruction.md, with no title, headings or figure section. `figures` are
the images sent after it, in that order, in the same user message. `instruction` keeps
the whole instruction.md and `golden_solution` the reference answer, for graders.

The export refuses a prompt that names the task, cites a figure number or a subfigure
letter, so that nothing outside the question text can reach the model.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (ROOT / "data/tasks.jsonl", ROOT / "docs/data/tasks.jsonl")
NUMBERED = re.compile(r"Fig(ure|\.)?\s*\d|\([a-z]\)")


def prompt_text(instruction: str) -> str:
    """The "## Question" section of an instruction.md, as sent to the model."""
    question = instruction.split("## Question", 1)[1].split("## Figures", 1)[0].strip()
    if not question or "##" in question:
        raise ValueError("instruction.md has no single question section")
    return question


def rows() -> list[dict]:
    out = []
    for instruction_path in sorted((ROOT / "tasks").glob("*/instruction.md")):
        task_dir = instruction_path.parent
        slug = task_dir.name
        match = re.match(r"part(?P<part>[12])-(?P<number>\d{3})-", slug)
        if not match:
            raise ValueError(f"unexpected task slug: {slug}")
        instruction = instruction_path.read_text(encoding="utf-8").strip()
        prompt = prompt_text(instruction)
        if slug in prompt or NUMBERED.search(prompt):
            raise ValueError(f"{slug}: the prompt names the task or cites a figure number or subfigure letter")
        out.append({
            "benchmark": "razavi-bench",
            "task_slug": slug,
            "part": f"part{match.group('part')}",
            "question_number": int(match.group("number")),
            "task_path": str(task_dir.relative_to(ROOT)),
            "prompt": prompt,
            "instruction": instruction,
            "golden_solution": (task_dir / "golden_solution.md").read_text(encoding="utf-8").strip(),
            "figures": [str(p.relative_to(ROOT)) for p in sorted(task_dir.glob("figure-*.png"))],
        })
    return out


def main() -> None:
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows())
    for path in OUTPUTS:
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
