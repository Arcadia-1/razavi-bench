#!/usr/bin/env python3
"""Measure how much the prompt title helps: the 18 questions whose title names the circuit.

Every benchmark prompt starts with the task's slug as a title, for example
"# part1-015-malformed-cmos-inverter", and for 18 questions that title names the
circuit or hints at the answer. Eight models answer those 18 questions in three
trials twice, now and with the benchmark's reasoning settings: once with the
prompt exactly as the benchmark sent it ("title" arm), and once with the title
reduced to the question's own text, without the title, the section headings
or the image links ("question_only" arm); both arms attach the same figures. Running both arms
at the same time keeps model or provider changes since the benchmark runs out of
the comparison.

Writes traces.jsonl (one row per request) and answers.jsonl (the answers in the
form evaluate_answers.py reads, with the arm in the model name). Reruns skip the
trials already answered.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import os
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROBE = REPO / "experiments/2026-11-05-reasoning-traces/probe.py"

# Reuse the reasoning-trace probe's request code and per-model benchmark settings.
_spec = importlib.util.spec_from_file_location("probe", PROBE)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)

TASKS = [
    "part1-007-pmos-common-source-source-degeneration",
    "part1-008-source-follower",
    "part1-009-common-gate-source-input",
    "part1-010-source-input-shorted-to-ground",
    "part1-012-source-input-resistive-feedback",
    "part1-013-source-follower-current-source-load",
    "part1-014-cmos-inverter",
    "part1-015-malformed-cmos-inverter",
    "part1-016-common-source-diode-connected-load",
    "part1-017-pmos-input-invalid-pulldown",
    "part1-020-nmos-cascode-gain-stage",
    "part1-023-common-gate-pmos-load",
    "part1-025-series-nmos-effective-long-channel",
    "part1-026-source-follower-drives-common-gate",
    "part1-028-current-input-positive-feedback",
    "part1-029-feedback-transimpedance-amplifier",
    "part1-030-pmos-current-input-feedback",
    "part2-013-dynamic-latch-divide-by-two",
]
TRIALS = (1, 2, 3)
ARMS = ("title", "question_only")
# Spanning the score range; most of the leaky questions are already near 100% for the leaders.
MODEL_KEYS = (
    "gemini_4_argon", "gpt_6_1_sol", "gemini_37_flash", "claude_haiku_55",
    "gemini_25_pro", "qwen_37_flash", "llama_4_maverick", "gpt_4o_2024_11_20",
)
MODELS = [m for m in probe.MODELS if m[0] in MODEL_KEYS]
assert len(MODELS) == len(MODEL_KEYS)


def question_only(task: dict) -> dict:
    """Only the question's own text: no title, no section headings, no image links.

    The figures are still attached as images by build_content."""
    text = task["instruction"]
    assert text.startswith("# part") and "## Question" in text, text[:80]
    question = text.split("## Question", 1)[1].split("## Figures", 1)[0].strip()
    assert question and "##" not in question, question
    return {**task, "instruction": question}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-model", type=int, default=4, help="concurrent requests per model")
    parser.add_argument("--workers", type=int, default=48)
    parser.add_argument("--timeout", type=int, default=900, help="seconds to wait for any chunk")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true", help="print the two prompts of one task and exit")
    args = parser.parse_args()

    tasks = {t["task_slug"]: t for t in probe.load_tasks(REPO, TASKS)}
    if args.dry_run:
        task = tasks["part1-015-malformed-cmos-inverter"]
        for arm, t in (("title", task), ("question_only", question_only(task))):
            print(f"===== {arm}\n{t['instruction']}\n")
        print(f"{len(MODELS)} models x {len(TASKS)} questions x {len(TRIALS)} trials x {len(ARMS)} arms "
              f"= {len(MODELS) * len(TASKS) * len(TRIALS) * len(ARMS)} requests")
        return 0

    key = os.environ["OPENROUTER_API_KEY"]
    traces_path = HERE / "traces.jsonl"
    done = {
        (r["model_key"], r["arm"], r["task_slug"], r["trial"])
        for r in (probe.read_jsonl(traces_path) if traces_path.exists() else [])
        if r.get("ok")
    }
    # Interleave models and arms so that every model runs at once and both arms of a
    # model run side by side, rather than one model after another.
    jobs = [(m, arm, slug, trial) for slug in TASKS for trial in TRIALS for arm in ARMS for m in MODELS
            if (m[0], arm, slug, trial) not in done]
    print(f"{len(jobs)} requests to run, {len(done)} already done", flush=True)
    gates = {m[0]: threading.Semaphore(args.per_model) for m in MODELS}
    lock = threading.Lock()

    def one(job):
        (model_key, model_id, effort, max_tokens), arm, slug, trial = job
        task = tasks[slug] if arm == "title" else question_only(tasks[slug])
        content, figures = probe.build_content(REPO, task)
        body = {
            "model": model_id,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "stream": True,
            "usage": {"include": True},
        }
        if effort:
            body["reasoning"] = {"effort": effort}
        attempts, result = [], None
        with gates[model_key]:
            for attempt in range(1, args.retries + 1):
                try:
                    result = probe.stream_call(key, body, args.timeout)
                    attempts.append({"attempt": attempt, "seconds": result["seconds"], "finish_reason": result["finish_reason"], "usage": result["usage"]})
                    if result["answer"] and result["finish_reason"] in ("stop", "end_turn", None):
                        break
                except Exception as error:  # noqa: BLE001 - every failure is recorded and retried
                    attempts.append({"attempt": attempt, "error": str(error)[:300]})
                    result = None
                time.sleep(2 * attempt)
        ok = bool(result and result["answer"])
        row = {
            "model_key": model_key, "model": model_id, "effort": effort or "default", "max_tokens": max_tokens,
            "arm": arm, "first_line": task["instruction"].splitlines()[0],
            "task_slug": slug, "task_path": task["task_path"], "trial": trial, "figures": figures,
            "ok": ok, "attempts": attempts, **(result or {}),
        }
        with lock:
            with traces_path.open("a") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return model_key, arm, slug, trial, ok

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for model_key, arm, slug, trial, ok in pool.map(one, jobs):
            print(f"{model_key:22s} {arm:7s} {slug[:28]:28s} t{trial} ok={ok}", flush=True)

    # The judge's input: the latest successful answer of every (model, arm, task, trial).
    # The arm goes into the model name so the two arms are scored as separate entries.
    latest = {}
    for row in probe.read_jsonl(traces_path):
        if row.get("ok"):
            latest[(row["model_key"], row["arm"], row["task_slug"], row["trial"])] = row
    with (HERE / "answers.jsonl").open("w") as handle:
        for (model_key, arm, slug, trial), row in sorted(latest.items()):
            handle.write(json.dumps({
                "benchmark": "razavi-bench", "experiment": "2026-11-09-title-leak-pilot",
                "task_slug": slug, "task_path": row["task_path"], "rollout": trial,
                "model_name": f"{model_key}:{arm}", "provider_model": row["model"], "reasoning_effort": row["effort"],
                "answer": row["answer"],
            }, ensure_ascii=False) + "\n")
    print(f"answers: {len(latest)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
