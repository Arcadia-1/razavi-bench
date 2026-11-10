#!/usr/bin/env python3
"""Each finished entry's score over the 50 questions before and after the P2 Q6/Q12 rerun.

"Before" uses the entry's earlier answers to all 50 questions; "after" replaces its answers to
part2-006 and part2-012 with the ones in this folder (API entries) or the latest ones in
../runs_selfhosted (self-hosted entries). A score counts only if it was given to that exact
answer (SHA-256) against the current golden_solution.md; the one exception is "before" for
part2-006, whose reference was rewritten for the new question. Entries whose other 48 questions
are not all graded (batches 4 and 5) are listed with their Q6/Q12 scores only.
Writes combined.csv; with --missing, writes the answers that still need a grade to
missing_grades.jsonl instead of printing the table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
RERUN = HERE.parent
REPO = RERUN.parents[1]
Q = ("part2-006", "part2-012")

# (answers files, score files) per group of entries; later files win for the same answer.
GROUPS = {
    "first ten and batch 2": (["answers.jsonl"], ["scores-gpt-6-luna-max.jsonl", "scores-recal4-gpt-6-luna-max.jsonl"]),
    "batch 3": (["batch3/answers.jsonl"], ["batch3/scores_all10-gpt-6-luna-max.jsonl", "batch3/scores-gpt-6-luna-max.jsonl"]),
    "Hy4": (["batch3/addon_hy4/answers.jsonl"], ["batch3/addon_hy4/scores-gpt-6-luna-max.jsonl"]),
    "batch 4": (["batch4/answers.jsonl"], []),
    "batch 5": (["batch5/answers.jsonl"], []),
    "self-hosted": (["answers_selfhosted.jsonl", "answers_selfhosted_9b.jsonl", "answers_selfhosted_glm.jsonl"],
                    ["scores-selfhosted-gpt-6-luna-max.jsonl", "scores-selfhosted-9b-gpt-6-luna-max.jsonl",
                     "scores-selfhosted-glm-gpt-6-luna-max.jsonl", "scores-recal4-gpt-6-luna-max.jsonl"]),
}
NEW_SCORES = [HERE / "scores-gpt-6-luna-max.jsonl", HERE / "scores-selfhosted-gpt-6-luna-max.jsonl",
              HERE / "scores-stale-gpt-6-luna-max.jsonl"]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--missing", action="store_true")
    args = parser.parse_args()
    golden = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO / "tasks").glob("*/golden_solution.md")}
    index = {m["model_key"]: m for m in json.loads((REPO / "docs/data/direct_qa/index.json").read_text())["models"]}

    # scores keyed by (answer sha, task slug) -> {golden sha: score}; later files win
    graded: dict[tuple[str, str], dict[str, int]] = {}
    files = [RERUN / f for _, (_, scores) in GROUPS.items() for f in scores] + NEW_SCORES
    for path in files:
        for s in read(path):
            graded.setdefault((s["answer_sha256"], s["task_slug"]), {})[s["golden_solution_sha256"]] = s["score_0_to_4"]

    new_answers = {}  # the latest finished answer in this folder's traces (answers.jsonl is written only at the end)
    for d in sorted((HERE / "runs").iterdir()):
        for t in read(d / "traces.jsonl"):
            if t.get("ok"):
                new_answers[(t["model_key"], t["task_slug"], t["rollout"])] = {**t, "model_name": t["model_key"]}
    rows, missing = [], []
    for group, (answer_files, _) in GROUPS.items():
        before, after = {}, {}
        for name in answer_files:
            for r in read(RERUN / name):
                key = (r["model_name"], r["task_slug"], r["rollout"])
                after[key] = r
                if r["task_slug"][:9] in Q and group == "self-hosted":
                    continue  # self-hosted answer files now hold the new Q6/Q12 answers
                before[key] = r
        if group == "self-hosted":  # earlier self-hosted Q6/Q12 answers come from the traces
            for d in (RERUN / "runs_selfhosted").iterdir():
                last = {}
                for t in read(d / "traces.jsonl"):
                    if t.get("ok") and t["task_slug"][:9] in Q:
                        last.setdefault((t["model_key"], t["task_slug"], t["rollout"]), []).append(t)
                for key, ts in last.items():
                    if len(ts) >= 2:
                        before[key] = {**ts[-2], "model_name": key[0]}
        else:
            for key in list(after):
                if key[1][:9] in Q:
                    after[key] = new_answers.get(key)
            models = {k[0] for k in before}
            for key, r in new_answers.items():
                if key[0] in models:
                    after[key] = r
        for model in sorted({k[0] for k in after}):
            res = {}
            for label, answers in (("before", before), ("after", after)):
                vals, gaps = [], []
                for key, r in answers.items():
                    if key[0] != model or r is None:
                        continue
                    by_golden = graded.get((digest(r["answer"]), key[1]), {})
                    score = by_golden.get(golden[key[1]])
                    if score is None and label == "before" and key[1][:9] == "part2-006" and by_golden:
                        score = list(by_golden.values())[-1]
                    if score is None:
                        gaps.append(key)
                    else:
                        vals.append((key, score))
                res[label] = (vals, gaps)
            for key in res["after"][1]:
                r = after[key]
                missing.append({**r, "model_name": key[0]})
            a_vals, a_gaps = res["after"]
            b_vals, _ = res["before"]
            q_after = [s for k, s in a_vals if k[1][:9] in Q]
            q_before = [s for k, s in b_vals if k[1][:9] in Q]
            rows.append({"group": group, "model_key": model, "name": index.get(model, {}).get("display_name", model),
                         "n_after": len(a_vals), "after": 25 * st.fmean(s for _, s in a_vals) if len(a_vals) == 150 else None,
                         "before": 25 * st.fmean(s for _, s in b_vals) if len(b_vals) == 150 else None,
                         "q_before": 25 * st.fmean(q_before) if len(q_before) == 6 else None,
                         "q_after": 25 * st.fmean(q_after) if len(q_after) == 6 else None})
    if args.missing:
        with (HERE / "missing_grades.jsonl").open("w") as h:
            for r in missing:
                if r["task_slug"][:9] in Q or r.get("model_name") not in {x["model_key"] for x in rows if x["group"] in ("batch 4", "batch 5")}:
                    h.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{len(missing)} answers without a current grade; written those outside batches 4-5 and all Q6/Q12")
        return
    fmt = lambda v: f"{v:5.1f}" if v is not None else "  -  "
    print(f"{'entry':28s} {'50 Q before':>11s} {'after':>6s} {'change':>7s}   {'Q6+Q12 before':>13s} {'after':>6s}")
    for r in rows:
        change = f"{r['after'] - r['before']:+6.1f}" if r["after"] is not None and r["before"] is not None else "     -"
        print(f"{r['name'][:28]:28s} {fmt(r['before']):>11s} {fmt(r['after']):>6s} {change:>7s}   {fmt(r['q_before']):>13s} {fmt(r['q_after']):>6s}")
    with (HERE / "combined.csv").open("w", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__":
    main()
