#!/usr/bin/env python3
"""Compare the two arms of the title-leak pilot from GPT-6 Luna's scores.

Reads scores-gpt-6-luna-max.jsonl (evaluate_answers.py on answers.jsonl, where
each model name carries its arm as "model:arm") and prints the mean score of each
arm overall, per question and per model, with a bootstrap 95% interval for the
difference (resampling question-model cells, each holding three trials per arm).
"""

from __future__ import annotations

import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    cells: dict[tuple[str, str], dict[str, list[int]]] = defaultdict(lambda: {"title": [], "question_only": []})
    for line in (HERE / "scores-gpt-6-luna-max.jsonl").read_text().splitlines():
        row = json.loads(line)
        model, arm = row["answer_metadata"]["model_name"].split(":")
        cells[(row["task_slug"], model)][arm].append(row["score_0_to_4"])
    complete = {k: v for k, v in cells.items() if len(v["title"]) == 3 and len(v["question_only"]) == 3}
    print(f"{len(complete)} complete question-model cells of {len(cells)}")

    def pct(values):
        return 25 * st.fmean(values)

    def diff(keys):
        t = [s for k in keys for s in complete[k]["title"]]
        q = [s for k in keys for s in complete[k]["question_only"]]
        return pct(t), pct(q), pct(q) - pct(t)

    keys = sorted(complete)
    t, q, d = diff(keys)
    rng = random.Random(0)
    boot = sorted(diff([rng.choice(keys) for _ in keys])[2] for _ in range(4000))
    print(f"overall: title {t:.1f}%, question only {q:.1f}%, difference {d:+.1f} points "
          f"(95% interval {boot[100]:+.1f} to {boot[3899]:+.1f})")

    print("\nper question (question only minus title):")
    for slug in sorted({k[0] for k in keys}):
        t, q, d = diff([k for k in keys if k[0] == slug])
        print(f"  {slug[:44]:44s} {t:6.1f} -> {q:6.1f}  {d:+6.1f}")
    print("\nper model:")
    for model in sorted({k[1] for k in keys}):
        t, q, d = diff([k for k in keys if k[1] == model])
        print(f"  {model:22s} {t:6.1f} -> {q:6.1f}  {d:+6.1f}")


if __name__ == "__main__":
    main()
