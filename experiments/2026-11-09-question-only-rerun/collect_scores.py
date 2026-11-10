#!/usr/bin/env python3
"""Collect every rerun entry's final 150 scores and its published score, across all batches.

An entry's rerun answers are the latest answer for each (task, rollout) from, in order:
answers.jsonl (first ten and batch 2), batch3, batch3/addon_hy4, batch4, batch5, batch6
(answers.jsonl or answers_partial.jsonl, whichever is fuller), the self-hosted answer files, and
q6q12/answers.jsonl, which holds every API entry's answers to the restored P2 Q6 and Q12.
A score counts only if it was given to that exact answer (SHA-256) against the task's current
golden_solution.md. The self-hosted Nemotron run is a cross-check of batch 2's and is left out.
batch6 stored Claude Opus 5 (max effort) under the dropped key claude_opus_5_medium; it is
relabelled claude_opus_5 here. Writes rerun_scores.csv; entries without a published run
(NEW_ENTRIES) have an empty published score. Published scores, names and release dates are read
from commit PUBLISHED, the last one before the rerun replaced the website's data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics as st
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PUBLISHED = "728956d"  # website data as published before this rerun replaced it
RELABEL = {"claude_opus_5_medium": "claude_opus_5"}
DROPPED = {"claude_opus_5_xhigh", "claude_opus_5_high", "claude_opus_5_medium", "gpt_6_sol_thinking_high",
           "minimax_01", "claude_sonnet_4", "doubao_seed_21_pro_260915_max"}
ANSWERS = ["answers.jsonl", "batch3/answers.jsonl", "batch3/addon_hy4/answers.jsonl", "batch4/answers.jsonl",
           "batch5/answers.jsonl", "batch6/answers.jsonl|batch6/answers_partial.jsonl", "batch7/answers.jsonl", "batch8/answers.jsonl", "batch9/answers.jsonl", "batch10/answers.jsonl",
           "answers_selfhosted.jsonl", "answers_selfhosted_9b.jsonl", "answers_selfhosted_glm.jsonl",
           "q6q12/answers.jsonl"]
SCORES = ["scores-gpt-6-luna-max.jsonl", "scores-recal4-gpt-6-luna-max.jsonl", "scores-selfhosted-gpt-6-luna-max.jsonl",
          "scores-selfhosted-9b-gpt-6-luna-max.jsonl", "scores-selfhosted-glm-gpt-6-luna-max.jsonl",
          "batch3/scores_all10-gpt-6-luna-max.jsonl", "batch3/scores-gpt-6-luna-max.jsonl",
          "batch3/addon_hy4/scores-gpt-6-luna-max.jsonl", "batch4/scores-gpt-6-luna-max.jsonl",
          "batch5/scores-gpt-6-luna-max.jsonl", "batch6/partial-scores-gpt-6-luna-max.jsonl",
          "batch6/scores-gpt-6-luna-max.jsonl", "batch7/scores-gpt-6-luna-max.jsonl", "batch8/scores-gpt-6-luna-max.jsonl", "batch9/scores-gpt-6-luna-max.jsonl", "batch10/scores-gpt-6-luna-max.jsonl", "q6q12/scores-gpt-6-luna-max.jsonl",
          "q6q12/scores-selfhosted-gpt-6-luna-max.jsonl"]
SOURCE = {"answers.jsonl": "first ten / batch 2", "batch3": "batch 3", "batch4": "batch 4", "batch5": "batch 5",
          "batch6": "batch 6", "batch7": "batch 7", "batch8": "batch 8", "batch9": "batch 9", "batch10": "batch 10", "answers_selfhosted": "self-hosted"}
EFFORT_RANK = {"none": 0, "minimal": 1, "low": 2, "medium": 3, "high": 4, "xhigh": 5, "max": 6}
# Published at their models' only or default-top reasoning setting, labelled "default" or otherwise.
# Entries with no published run, added for the rerun: key -> (display name, provider, release date).
NEW_ENTRIES = {"claude_fable_52": ("Claude Fable 5.2", "anthropic", "2026-11-09")}
SAME_SETTING = {"qwen_38_27b", "qwen_35_9b", "kimi_k27", "nemotron_35_super_vl"}


def published(path: str) -> str:
    return subprocess.run(["git", "show", f"{PUBLISHED}:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def collect() -> list[dict]:
    golden = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO / "tasks").glob("*/golden_solution.md")}
    answers, source, effort = {}, {}, {}
    for spec in ANSWERS:
        candidates = [HERE / p for p in spec.split("|") if (HERE / p).exists()]
        path = max(candidates, key=lambda c: len(read(c)), default=None)  # the fuller of final and partial
        if path is None:
            continue
        label = next((v for k, v in SOURCE.items() if str(path.relative_to(HERE)).startswith(k)), None)
        for r in read(path):
            model = RELABEL.get(r["model_name"], r["model_name"])
            if model == "glm_5_3_flash_260828_max" and not path.name.startswith("answers_selfhosted"):
                continue  # GLM's answers are the self-hosted run's
            answers[(model, r["task_slug"], r["rollout"])] = hashlib.sha256(r["answer"].encode()).hexdigest()
            if label:
                source[model] = label
            if r["task_slug"][:9] not in ("part2-006", "part2-012"):
                effort[model] = r.get("reasoning_effort")
    by_model, any_model = {}, {}
    for name in SCORES:
        for s in read(HERE / name):
            if golden[s["task_slug"]] != s["golden_solution_sha256"]:
                continue
            model = RELABEL.get(s["answer_metadata"]["model_name"], s["answer_metadata"]["model_name"])
            by_model[(model, s["answer_sha256"], s["task_slug"])] = s["score_0_to_4"]
            any_model[(s["answer_sha256"], s["task_slug"])] = s["score_0_to_4"]
    scores: dict[str, list[int]] = {}
    for (model, slug, rollout), digest in answers.items():
        score = by_model.get((model, digest, slug), any_model.get((digest, slug)))
        if score is not None:
            scores.setdefault(model, []).append(score)
    index = {m["model_key"]: m for m in json.loads(published("docs/data/direct_qa/index.json"))["models"]}
    released = {r["model_key"]: r["release_date"] for r in csv.DictReader(published("docs/data/direct_qa/model_release_dates.csv").splitlines())}
    rows = []
    for model in sorted(index):
        if model in DROPPED:
            continue
        detail = json.loads(published("docs/data/direct_qa/" + index[model]["detail_file"]))
        published_effort = detail.get("thinking_effort")
        rerun_effort = effort.get(model)
        values = scores.get(model, [])
        raised = (model not in SAME_SETTING and rerun_effort not in (None, "default")
                  and EFFORT_RANK.get(published_effort, -1) < EFFORT_RANK.get(rerun_effort, -1))
        rows.append({"model_key": model, "name": index[model]["display_name"], "provider": index[model].get("provider"),
                     "release_date": released.get(model, ""), "source": source.get(model, ""),
                     "published": round(25 * st.fmean(a["active_score"]["score_0_to_4"] for a in detail["answers"]), 2),
                     "rerun": round(25 * st.fmean(values), 2) if len(values) == 150 else "",
                     "graded": len(values), "published_effort": published_effort, "rerun_effort": rerun_effort or "",
                     "effort_raised": raised})
    for model, (name, provider, day) in NEW_ENTRIES.items():
        values = scores.get(model, [])
        rows.append({"model_key": model, "name": name, "provider": provider, "release_date": day,
                     "source": source.get(model, ""), "published": "",
                     "rerun": round(25 * st.fmean(values), 2) if len(values) == 150 else "",
                     "graded": len(values), "published_effort": "", "rerun_effort": effort.get(model) or "",
                     "effort_raised": False})
    return rows


def main() -> None:
    rows = collect()
    with (HERE / "rerun_scores.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    done = [r for r in rows if r["rerun"] != ""]
    print(f"{len(done)} of {len(rows)} entries complete")
    for r in rows:
        if r["rerun"] == "":
            print(f"   not complete: {r['name']} ({r['graded']} graded)")


if __name__ == "__main__":
    main()
