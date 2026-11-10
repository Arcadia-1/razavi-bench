#!/usr/bin/env python3
"""Rerun benchmark entries with the question's own text and its figure, nothing else.

The published runs sent each task's instruction.md, whose first line is the task
slug (for example "# part1-015-malformed-cmos-inverter"); for 18 questions that
title names the circuit. Here every request is one user message holding only the
question text from instruction.md's "## Question" section, followed by the figure
as an image: no title, no section headings, no image links, no system prompt.
Each entry keeps the model and, where compatible with reasoning, the temperature
of its published run. Models with a reasoning setting run at maximum effort,
and max_tokens is the model's own output
limit on OpenRouter, so that no answer is cut short by the request. The requests
go through OpenRouter. An answer cut off at that limit is re-run; one cut off on
every attempt (a model that loops until its own limit) is graded as it stands.

Writes, per entry, to runs/<model_key>/:
- requests.jsonl: the exact request body of every call, with each image replaced
  by its file, SHA-256, size in bytes and pixel size
- traces.jsonl: one row per call with timing, usage, finish reason and answer
and answers.jsonl at the top level, in the form evaluate_answers.py reads.
Reruns skip the (entry, task, rollout) slots already answered with the entry's
current effort and max_tokens and the task's current figures; answers to an older
configuration or figure stay in traces.jsonl but are re-run and left out of
answers.jsonl.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import struct
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
_spec = importlib.util.spec_from_file_location("probe", REPO / "experiments/2026-11-05-reasoning-traces/probe.py")
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)

ROLLOUTS = (1, 2, 3)
FINISHED = ("stop", "end_turn", None)

# Questions say "the figure", never a figure number or subfigure letter, and no figure
# carries a printed subfigure label or caption (2026-11-09 audit of every figure).
NUMBERED = re.compile(r"Fig(ure|\.)?\s*\d|\([a-z]\)")

# Configuration of each entry, keyed by display name: OpenRouter model, reasoning
# effort (None = the model has no reasoning setting), temperature (None = provider
# default, as published) and max_tokens (the model's max_completion_tokens on
# OpenRouter).
ENTRIES = {
    "Gemma 4 31B IT": ("google/gemma-4-31b-it", "max", 0.0, 16384),
    "Llama 4 Maverick": ("meta-llama/llama-4-maverick", None, 0.0, 32768),
    "Gemini 2.5 Flash-Lite": ("google/gemini-2.5-flash-lite", "max", 0.0, 65535),
    "Qwen 3.7 Flash": ("qwen/qwen3.7-flash", "max", 0.0, 65536),
    "Mistral Large 2512": ("mistralai/mistral-large-2512", None, 0.0, 209715),
    "Qwen2.5-VL-72B Instruct": ("qwen/qwen2.5-vl-72b-instruct", None, 0.0, 115200),
    "Qwen3-VL-235B-A22B Instruct": ("qwen/qwen3-vl-235b-a22b-instruct", None, 0.0, 32768),
    "MiniMax M3": ("minimax/minimax-m3", "max", None, 512000),
    "Nova Pro": ("amazon/nova-pro-v1", None, 0.0, 5120),
    "Mimo 2.6 Pro": ("xiaomi/mimo-v2.6-pro", "max", None, 131072),
    "Nemotron 3.5 Super VL": ("nvidia/nemotron-3.5-super-vl", "max", 1.0, 943718),
    "Claude Haiku 4.5": ("anthropic/claude-haiku-4.5", "max", None, 64000),
    "GPT-4o Mini": ("openai/gpt-4o-mini-2024-07-18", None, 0.0, 16384),
    "GPT-4o (2024-08-06)": ("openai/gpt-4o-2024-08-06", None, 0.0, 16384),
    "GPT-6 Luna": ("openai/gpt-6-luna", "max", None, 128000),
    "GPT-4o (2024-11-20)": ("openai/gpt-4o-2024-11-20", None, 0.0, 16384),
    "Gemini 3.7 Flash": ("google/gemini-3.7-flash", "high", 0.0, 65536),
    "DeepSeek V4.1 Flash 0910": ("deepseek/deepseek-v4.1-flash", "max", None, 943718),
    "GPT-5.4 Mini": ("openai/gpt-5.4-mini", "xhigh", None, 128000),
    "Qwen 3.7 Plus": ("qwen/qwen3.7-plus", "max", 0.0, 131072),
    "Inkling Small": ("thinkingmachines/inkling-small", "max", 0.0, 262144),
    "GPT-4o (2024-05-13)": ("openai/gpt-4o-2024-05-13", None, 0.0, 4096),
    "Gemini 3 Flash": ("google/gemini-3-flash-preview", "high", 0.0, 65536),
    "GLM 5.3 Flash": ("z-ai/glm-5.3-flash", "max", None, 943717),
    "DeepSeek V4.1 Flash 1017": ("deepseek/deepseek-v4.1-flash-1017", "max", None, 943718),
    "GPT-5.6 Luna": ("openai/gpt-5.6-luna", "max", None, 128000),
    "Grok 4.5": ("x-ai/grok-4.5", "high", 0.0, 450000),
    "Gemini 3.6 Flash": ("google/gemini-3.6-flash", "high", 0.0, 65536),
    "Claude Haiku 5.5": ("anthropic/claude-haiku-5.5", "max", None, 128000),
    "Grok 4.6": ("x-ai/grok-4.6", "xhigh", 0.0, 450000),
    "Hy4": ("tencent/hy4", "high", None, 65536),
    "Gemini 3.1 Pro": ("google/gemini-3.1-pro-preview", "high", 0.0, 65536),
    "Step 3.7 Flash": ("stepfun/step-3.7-flash", "high", 0.0, 230400),
    "Kimi K2.7": ("moonshotai/kimi-k2.7-code", None, None, 235929),
    "o3": ("openai/o3", "high", None, 100000),
    "Mistral Large 4": ("mistralai/mistral-large-4-0", "high", None, 262144),
    "Inkling": ("thinkingmachines/inkling", "max", 0.0, 471859),
    "Muse Spark 1.2": ("meta/muse-spark-1.2", "xhigh", None, 943718),
    "Muse Spark 1.3": ("meta/muse-spark-1.3", "max", None, 943718),
    "Qwen 3.8 Max": ("qwen/qwen3.8-max-0902", "xhigh", 0.0, 131072),
    "GPT-6.1 Sol": ("openai/gpt-6.1-sol", "max", None, 128000),
    "Gemini 3.8 Flash": ("google/gemini-3.8-flash", "high", 0.0, 65536),
    "Gemini 4 Argon": ("google/gemini-4-argon", "high", 0.0, 943718),
    "Mistral Medium 3.5": ("mistralai/mistral-medium-3-5", "high", None, 209715),
    "Gemini 3.5 Flash": ("google/gemini-3.5-flash", "high", 0.0, 65536),
    "GPT-6 Sol": ("openai/gpt-6-sol", "max", None, 128000),
    "GPT-5.4": ("openai/gpt-5.4", "xhigh", None, 128000),
    "GPT-5.6 Sol": ("openai/gpt-5.6-sol", "max", None, 128000),
    "GPT-5": ("openai/gpt-5", "high", None, 128000),
    "Gemini 2.5 Pro": ("google/gemini-2.5-pro", "max", 0.0, 65536),
    "Claude Sonnet 4.5": ("anthropic/claude-sonnet-4.5", "max", None, 64000),
    "GPT-5.1": ("openai/gpt-5.1", "high", None, 128000),
    "Grok 4.7": ("x-ai/grok-4.7", "xhigh", 0.0, 450000),
    "GPT-5.5": ("openai/gpt-5.5", "xhigh", None, 128000),
    "GPT-5.3": ("openai/gpt-5.3-codex", "xhigh", None, 128000),
    "Claude Sonnet 4.6": ("anthropic/claude-sonnet-4.6", "max", None, 128000),
    "Claude Opus 5": ("anthropic/claude-opus-5", "max", None, 128000),
    "Claude Opus 4.5": ("anthropic/claude-opus-4.5", "max", None, 64000),
    "GPT-5.6 Terra": ("openai/gpt-5.6-terra", "max", None, 128000),
    "Kimi K3": ("moonshotai/kimi-k3", "max", None, 943718),
    "GPT-5.2": ("openai/gpt-5.2", "xhigh", None, 128000),
    "Kimi 3.1 Pro": ("moonshotai/kimi-k3.1-pro", "max", None, 943718),
}

# Preserve NVIDIA's recommended sampling when moving this entry to OpenRouter.
MODEL_OPTIONS = {"Nemotron 3.5 Super VL": {"top_p": 0.95}}
# Require hosts to support the explicit reasoning and sampling parameters.
for _name in (
    "Inkling Small", "Gemini 3 Flash", "GLM 5.3 Flash", "DeepSeek V4.1 Flash 1017",
    "GPT-5.6 Luna", "Grok 4.5", "Gemini 3.6 Flash", "Claude Haiku 5.5", "Grok 4.6", "Hy4",
    "Gemini 3.1 Pro",
    "Step 3.7 Flash", "Kimi K2.7", "o3", "Mistral Large 4", "Inkling",
    "Muse Spark 1.2", "Muse Spark 1.3", "Qwen 3.8 Max", "GPT-6.1 Sol", "Gemini 3.8 Flash",
    "Gemini 4 Argon", "Mistral Medium 3.5", "Gemini 3.5 Flash", "GPT-6 Sol", "GPT-5.4",
    "GPT-5.6 Sol", "GPT-5", "Gemini 2.5 Pro", "Claude Sonnet 4.5", "GPT-5.1", "Grok 4.7",
    "GPT-5.5", "GPT-5.3", "Claude Sonnet 4.6", "Claude Opus 5", "Claude Opus 4.5",
    "GPT-5.6 Terra", "Kimi K3", "GPT-5.2", "Kimi 3.1 Pro",
):
    MODEL_OPTIONS[_name] = {"provider": {"require_parameters": True}}
# Kimi has a native thinking mode rather than selectable effort levels.
MODEL_OPTIONS["Kimi K2.7"]["reasoning"] = {"enabled": True}


def question_only(task: dict) -> str:
    text = task["instruction"]
    question = text.split("## Question", 1)[1].split("## Figures", 1)[0].strip()
    assert question and "##" not in question and task["task_slug"] not in question, task["task_slug"]
    return question


def png_size(data: bytes) -> tuple[int, int]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def build(task: dict, input_root: Path = REPO) -> tuple[list[dict], list[dict]]:
    """The message content, and the same content as logged (images replaced by their identity)."""
    question = question_only(task)
    assert not NUMBERED.search(question), task["task_slug"]
    content = [{"type": "text", "text": question}]
    logged = [dict(content[0])]
    for relative in task.get("figures") or []:
        data = (input_root / relative).read_bytes()
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(data).decode()}})
        w, h = png_size(data)
        logged.append({"type": "image_url", "image": {"file": relative, "sha256": hashlib.sha256(data).hexdigest(),
                                                      "bytes": len(data), "width": w, "height": h}})
    return content, logged


def answered(row: dict) -> bool:
    """Whether a row holds the model's answer: it finished, or it ran into the model's own
    output limit on every attempt that got a response, so retrying cannot finish it."""
    if not row.get("answer") and not row.get("reasoning"):
        return False
    if row.get("finish_reason") == "length":
        attempts = row.get("attempts", [])
        return (bool(row.get("answer")) or bool(attempts)) and all(
            a.get("finish_reason") == "length" or "error" in a for a in attempts)
    return bool(row.get("answer")) and row.get("finish_reason") in FINISHED


def current(row: dict, task: dict, input_root: Path = REPO) -> bool:
    """Whether an answered row used the entry's current configuration and the task's current text and figures."""
    model, effort, temperature, max_tokens = ENTRIES[row["display_name"]]
    figures = [hashlib.sha256((input_root / relative).read_bytes()).hexdigest() for relative in task.get("figures") or []]
    return (answered(row) and row.get("effort") == (effort or "default") and row.get("max_tokens") == max_tokens
            and row.get("model") == model and row.get("temperature") == temperature
            and row.get("request_options", {}) == MODEL_OPTIONS.get(row["display_name"], {})
            and row.get("question") == question_only(task) and [f["sha256"] for f in row.get("figures", [])] == figures)


def read_traces(directory: Path) -> list[dict]:
    """traces.jsonl rows, each with the question text it was sent (from the matching requests.jsonl line)."""
    if not (directory / "traces.jsonl").exists():
        return []
    traces, requests = probe.read_jsonl(directory / "traces.jsonl"), probe.read_jsonl(directory / "requests.jsonl")
    assert len(traces) == len(requests), directory
    for row, request in zip(traces, requests):
        assert (row["task_slug"], row["rollout"]) == (request["task_slug"], request["rollout"]), directory
        row.setdefault("question", request["body"]["messages"][0]["content"][0]["text"])
    return traces


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", action="append", default=[], help="display name to run (repeatable)")
    parser.add_argument("--task-slug", action="append", default=[], help="restrict generation to these tasks (repeatable)")
    parser.add_argument("--rollout", type=int, choices=ROLLOUTS, action="append", help="restrict generation to these rollouts")
    parser.add_argument("--per-model", type=int, default=8)
    parser.add_argument("--workers", type=int, default=64)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=HERE,
                        help="directory containing runs/ and answers.jsonl (isolates concurrent batches)")
    parser.add_argument("--export-selected", action="store_true",
                        help="export only selected models, retaining other models' traces for audit")
    parser.add_argument("--input-root", type=Path, default=REPO,
                        help="repository-shaped snapshot supplying task text and figures")
    parser.add_argument("--show", help="print the logged request of one task slug and exit")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    input_root = args.input_root.resolve()

    tasks = {t["task_slug"]: t for t in probe.load_tasks(input_root)}
    if args.show:
        content, logged = build(tasks[args.show], input_root)
        print(json.dumps({"messages": [{"role": "user", "content": logged}]}, indent=1, ensure_ascii=False))
        return 0

    index = json.loads((REPO / "docs/data/direct_qa/index.json").read_text())
    keys = {m["display_name"]: m["model_key"] for m in index["models"]}
    names = args.only or list(ENTRIES)
    selected_tasks = args.task_slug or sorted(tasks)
    unknown = set(selected_tasks) - tasks.keys()
    if unknown:
        parser.error(f"unknown task slugs: {sorted(unknown)}")
    key = os.environ["OPENROUTER_API_KEY"]
    lock = threading.Lock()
    jobs = []
    for name in names:
        out = output_dir / "runs" / keys[name]
        out.mkdir(parents=True, exist_ok=True)
        done = {(r["task_slug"], r["rollout"]) for r in read_traces(out)
                if current(r, tasks[r["task_slug"]], input_root)}
        jobs += [(name, keys[name], slug, rollout) for rollout in (args.rollout or ROLLOUTS)
                 for slug in selected_tasks if (slug, rollout) not in done]
    # Interleave entries so that every entry runs at once instead of one after another.
    jobs.sort(key=lambda j: (j[3], j[2], j[0]))
    print(f"{len(jobs)} requests to run", flush=True)
    gates = {name: threading.Semaphore(args.per_model) for name in names}

    def one(job):
        name, model_key, slug, rollout = job
        model, effort, temperature, max_tokens = ENTRIES[name]
        content, logged = build(tasks[slug], input_root)
        body = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens,
                "stream": True, "usage": {"include": True}}
        if temperature is not None:
            body["temperature"] = temperature
        if effort:
            body["reasoning"] = {"effort": effort}
        body.update(MODEL_OPTIONS.get(name, {}))
        sent = {**body, "messages": [{"role": "user", "content": logged}]}
        attempts, result = [], None
        with gates[name]:
            for attempt in range(1, args.retries + 1):
                try:
                    result = probe.stream_call(key, body, args.timeout)
                    attempts.append({"attempt": attempt, "seconds": result["seconds"], "finish_reason": result["finish_reason"], "usage": result["usage"]})
                    if result["answer"] and result["finish_reason"] in FINISHED:
                        break
                except Exception as error:  # noqa: BLE001 - every failure is recorded and retried
                    attempts.append({"attempt": attempt, "error": str(error)[:300]})
                    result = None
                # Rate limits (429) need a longer wait than a dropped stream.
                time.sleep(min(240, 15 * 2 ** attempt) if "429" in attempts[-1].get("error", "") else 2 * attempt)
        # Repeated truncation at the model's own limit is retained for grading.
        row = {"model_key": model_key, "display_name": name, "model": model, "effort": effort or "default",
               "temperature": temperature, "max_tokens": max_tokens, "task_slug": slug, "task_path": tasks[slug]["task_path"],
               "request_options": MODEL_OPTIONS.get(name, {}),
               "question": content[0]["text"],
               "rollout": rollout, "figures": [part["image"] for part in logged[1:]], "attempts": attempts,
               **(result or {})}
        row["ok"] = ok = answered(row)
        out = output_dir / "runs" / model_key
        with lock:
            with (out / "requests.jsonl").open("a") as h:
                h.write(json.dumps({"task_slug": slug, "rollout": rollout, "body": sent}, ensure_ascii=False) + "\n")
            with (out / "traces.jsonl").open("a") as h:
                h.write(json.dumps(row, ensure_ascii=False) + "\n")
        return name, slug, rollout, ok

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            name, slug, rollout, ok = future.result()
            print(f"{name:28s} {slug[:30]:30s} r{rollout} ok={ok}", flush=True)

    latest = {}
    for directory in sorted((output_dir / "runs").iterdir()):
        for r in read_traces(directory):
            if (r.get("display_name") in ENTRIES
                    and (not args.export_selected or r["display_name"] in names)
                    and current(r, tasks[r["task_slug"]], input_root)):
                latest[(r["model_key"], r["task_slug"], r["rollout"])] = r
    answer_path = output_dir / "answers.jsonl"
    temporary_path = answer_path.with_suffix(".jsonl.tmp")
    with temporary_path.open("w") as h:
        for (model_key, slug, rollout), r in sorted(latest.items()):
            h.write(json.dumps({"benchmark": "razavi-bench", "experiment": "2026-11-09-question-only-rerun", "task_slug": slug,
                                "task_path": r["task_path"], "rollout": rollout, "model_name": model_key,
                                "provider_model": r["model"], "reasoning_effort": r["effort"], "finish_reason": r["finish_reason"],
                                "answer_status": "returned" if r["answer"] else "no_final_answer_at_output_limit",
                                "answer": r["answer"]},
                               ensure_ascii=False) + "\n")
    temporary_path.replace(answer_path)
    print(f"answers: {len(latest)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
