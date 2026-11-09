#!/usr/bin/env python3
"""Write blind_references/: the benchmark's tasks with every statement about the article's answers removed.

38 of the 50 reference answers quote the answer Razavi scored and his score, or give a rule pinned to
it ("..., Razavi's score"). Grading the article's own answers against those references is partly
circular. This control drops each sentence that mentions ChatGPT or Gemini, or that states Razavi's
score or verdict on an answer; sentences about the circuit itself, including Razavi's own analysis,
stay. Sentences are split on terminal punctuation outside double quotes and backticks.
instruction.md and evaluation_rubric.md are copied unchanged.
"""

import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "blind_references"
VERDICT = re.compile(r"ChatGPT|Gemini|Razavi scores|Razavi's score|Razavi answers|Razavi rejects|Razavi's scored answer|scores that answer")


def sentences(paragraph: str) -> list[str]:
    out, start, quote, tick = [], 0, False, False
    for i, ch in enumerate(paragraph):
        if ch == '"':
            quote = not quote
        elif ch == "`":
            tick = not tick
        elif ch in ".!?" and not quote and not tick and (i + 1 == len(paragraph) or paragraph[i + 1] == " "):
            nxt = paragraph[i + 2: i + 3]
            if i + 1 == len(paragraph) or re.match(r"[A-Z`(\"\-]", nxt) and not re.search(r"\b(e\.g|i\.e|vs|approx)\.$", paragraph[: i + 1]):
                out.append(paragraph[start: i + 1].strip()); start = i + 1
    if paragraph[start:].strip():
        out.append(paragraph[start:].strip())
    return out


def blind(text: str) -> tuple[str, int]:
    kept, removed = [], 0
    for block in re.split(r"\n\s*\n", text):
        lines = block.splitlines()
        if lines and (lines[0].startswith("#") or all(l.lstrip().startswith("- ") for l in lines if l.strip())):
            items = [l for l in lines if not (l.lstrip().startswith("- ") and VERDICT.search(l))]
            removed += len(lines) - len(items)
            if items: kept.append("\n".join(items))
            continue
        parts = sentences(" ".join(l.strip() for l in lines))
        good = [s for s in parts if not VERDICT.search(s)]
        removed += len(parts) - len(good)
        if good: kept.append(" ".join(good))
    return "\n\n".join(kept) + "\n", removed


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copy(REPO / "evaluation_rubric.md", OUT / "evaluation_rubric.md") if OUT.mkdir(parents=True) is None else None
    total = 0
    for task in sorted(p for p in (REPO / "tasks").iterdir() if p.is_dir()):
        (OUT / "tasks" / task.name).mkdir(parents=True)
        shutil.copy(task / "instruction.md", OUT / "tasks" / task.name / "instruction.md")
        text, removed = blind((task / "golden_solution.md").read_text())
        (OUT / "tasks" / task.name / "golden_solution.md").write_text(text)
        assert not VERDICT.search(text), task.name
        total += removed
        if removed: print(f"{task.name[:9]}: removed {removed}")
    print(f"removed {total} sentences")


if __name__ == "__main__":
    main()
