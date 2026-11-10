#!/usr/bin/env python3
"""Compare GPT-6 Luna's scores of the article answers with Razavi's, question by question.

Reads article_answers.jsonl (Razavi's scores), the scores given against the current references
(scores-gpt-6-luna-max*.jsonl) and against blind_references/ (scores-blind-gpt-6-luna-max.jsonl). Each answer was graded three times; the per-question Luna score is the median of the
three. Prints agreement statistics and the per-question table, and writes per_question.csv.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Score files of each run, and the references they must have been given against (scores given
# against an older reference, such as before the 2026-11-09 calibration rules, are dropped).
RUNS = {"current": (["scores-gpt-6-luna-max.jsonl", "scores-gpt-6-luna-max.recal4.jsonl", "scores-gpt-6-luna-max.q6q12.jsonl"], HERE.parents[1]),
        "blind": (["scores-blind-gpt-6-luna-max.jsonl"], HERE / "blind_references")}


def main() -> None:
    razavi, label = {}, {}
    for row in map(json.loads, open(HERE / "article_answers.jsonl")):
        razavi[row["task_slug"]] = row["razavi_score"]; label[row["task_slug"]] = row["article_question"]
    judged = {}
    for name, (paths, root) in RUNS.items():
        golden = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / "tasks").glob("*/golden_solution.md")}
        latest = {}
        for path in paths:
            if (HERE / path).exists():
                for s in map(json.loads, open(HERE / path)):
                    if s["golden_solution_sha256"] == golden[s["task_slug"]]:
                        latest[(s["task_slug"], s["answer_metadata"]["rollout"])] = s["score_0_to_4"]
        per = {}
        for (slug, _), score in latest.items():
            per.setdefault(slug, []).append(score)
        judged[name] = per
    slugs = sorted(razavi)
    for name, per in judged.items():
        complete = [s for s in slugs if len(per.get(s, [])) == 3]
        med = {s: st.median(per[s]) for s in complete}
        print(f"\n== {name} references: {len(complete)}/50 questions graded 3 times")
        for part, pre in (("Part 1 (ChatGPT)", "part1"), ("Part 2 (Gemini 3.1 Pro)", "part2"), ("all 50", "")):
            qs = [s for s in complete if s.startswith(pre)]
            if not qs:
                continue
            r = [razavi[s] for s in qs]; l = [med[s] for s in qs]
            every = [v for s in qs for v in per[s]]
            exact = sum(a == b for a, b in zip(r, l)); within = sum(abs(a - b) <= 1 for a, b in zip(r, l))
            print(f"  {part:24s} Razavi {25 * st.fmean(r):5.1f}%  Luna {25 * st.fmean(every):5.1f}%  "
                  f"exact {exact}/{len(qs)}  within 1: {within}/{len(qs)}  mean |diff| {st.fmean(abs(a - b) for a, b in zip(r, l)):.2f}")
        stable = sum(len(set(per[s])) == 1 for s in complete)
        print(f"  judge repeats identical on {stable}/{len(complete)} questions")
    print(f"\n{'question':10s} {'Razavi':>6s}  " + "  ".join(f"{n:>13s}" for n in judged))
    rows = []
    for s in slugs:
        cells = []
        for name, per in judged.items():
            v = per.get(s, [])
            cells.append(f"{'/'.join(map(str, sorted(v))):>7s} ({st.median(v) - razavi[s]:+.0f})" if len(v) == 3 else f"{'...':>13s}")
        flag = " <-" if any(len(per.get(s, [])) == 3 and abs(st.median(per[s]) - razavi[s]) >= 2 for per in judged.values()) else ""
        print(f"{label[s]:10s} {razavi[s]:6d}  " + "  ".join(cells) + flag)
        rows.append({"question": label[s], "task_slug": s, "razavi": razavi[s],
                     **{f"luna_{n}": "/".join(map(str, sorted(per.get(s, [])))) for n, per in judged.items()}})
    with (HERE / "per_question.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__":
    main()
