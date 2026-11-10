#!/usr/bin/env python3
"""Compare each rerun entry's GPT-6 Luna score with its published score.

Reads scores-gpt-6-luna-max.jsonl (evaluate_answers.py on answers.jsonl) and the
published answers in docs/data/direct_qa/models/, and prints, per entry, the
published and rerun scores over all 50 questions, over the 18 questions whose
published title named the circuit, and over the other 32.
"""

from __future__ import annotations

import hashlib
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# Questions whose published prompt title named the circuit or its answer.
LEAKY = {f"part1-{n:03d}" for n in (7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 20, 23, 25, 26, 28, 29, 30)} | {"part2-013"}


def pct(values):
    return 25 * st.fmean(values) if values else float("nan")


def main() -> None:
    # Only scores of the answers now in answers.jsonl, given against the current reference;
    # answers replaced after a question changed keep their old scores in the file.
    answers = {}
    for line in (HERE / "answers.jsonl").read_text().splitlines():
        row = json.loads(line)
        answers[(row["model_name"], row["task_slug"], row["rollout"])] = hashlib.sha256(row["answer"].encode()).hexdigest()
    golden = {path.parent.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (REPO / "tasks").glob("*/golden_solution.md")}
    questions = {path.parent.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (REPO / "tasks").glob("*/instruction.md")}
    latest = {}
    for line in (HERE / "scores-gpt-6-luna-max.jsonl").read_text().splitlines():
        row = json.loads(line)
        key = (row["answer_metadata"]["model_name"], row["task_slug"], row["answer_metadata"]["rollout"])
        if (answers.get(key) == row["answer_sha256"]
                and golden[row["task_slug"]] == row["golden_solution_sha256"]
                and questions[row["task_slug"]] == row["question_sha256"]
                and not row.get("parse_error") and row.get("score_0_to_4") in (0, 1, 2, 3, 4)):
            latest[key] = row["score_0_to_4"]
    missing = len(answers) - len(latest)
    rerun = defaultdict(lambda: defaultdict(list))
    for (model, slug, _), score in latest.items():
        rerun[model][slug].append(score)
    print(f"{len(latest)} current scores; {missing} answers not yet graded against the current reference")

    index = json.loads((REPO / "docs/data/direct_qa/index.json").read_text())
    print(f"{'entry':28s} {'all 50':>16s} {'18 titled':>16s} {'other 32':>16s}  n")
    for model in index["models"]:
        key = model["model_key"]
        if key not in rerun:
            continue
        published = defaultdict(list)
        for answer in json.loads((REPO / "docs/data/direct_qa" / model["detail_file"]).read_text())["answers"]:
            published[answer["question_id"]].append(answer["active_score"]["score_0_to_4"])
        cells = []
        for subset in (lambda s: True, lambda s: s[:9] in LEAKY, lambda s: s[:9] not in LEAKY):
            old = [v for slug, vs in published.items() if subset(slug) for v in vs]
            new = [v for slug, vs in rerun[key].items() if subset(slug) for v in vs]
            cells.append(f"{pct(old):5.1f}->{pct(new):5.1f} {pct(new) - pct(old):+5.1f}")
        print(f"{model['display_name']:28s} {cells[0]:>16s} {cells[1]:>16s} {cells[2]:>16s}  {sum(map(len, rerun[key].values()))}")


if __name__ == "__main__":
    main()
