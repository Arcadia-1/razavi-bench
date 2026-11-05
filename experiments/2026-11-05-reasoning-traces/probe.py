#!/usr/bin/env python3
"""Time models on two look-alike question pairs and keep their reasoning text.

Each model answers Q14 and Q20 (a CMOS inverter and an NMOS cascode, both
textbook circuits) and Q15 and Q21 (circuits drawn to look like them but wired
with different device types) in three trials, with the reasoning effort and
output limit of its published Razavi-Bench run. Requests are streamed through
OpenRouter so that the wall-clock time of every answer can be recorded, along
with the reasoning text for models that return it.

Writes traces.jsonl (one row per request, with timing, usage, reasoning and
answer) and answers.jsonl (the answers in the form evaluate_answers.py reads).
Reruns skip the trials already answered.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
from direct_qa_openrouter_common import build_content, load_tasks, read_jsonl  # noqa: E402

TASKS = [
    "part1-014-cmos-inverter",
    "part1-015-malformed-cmos-inverter",
    "part1-020-nmos-cascode-gain-stage",
    "part1-021-cascode-structure",
]
TRIALS = (1, 2, 3)

# (benchmark model key, OpenRouter id, effort or None for the provider default, max_tokens)
MODELS = [
    ("gemini_4_argon", "google/gemini-4-argon", "high", 65536),
    ("claude_opus_55", "anthropic/claude-opus-5.5", "max", 128000),
    ("gpt_6_astra", "openai/gpt-6-astra", "max", 128000),
    ("claude_opus_5_xhigh", "anthropic/claude-opus-5", "xhigh", 128000),
    ("gpt_6_1_sol", "openai/gpt-6.1-sol", "max", 128000),
    ("claude_fable_51", "anthropic/claude-fable-5.1", "max", 128000),
    ("hy4", "tencent/hy4", "high", 65536),
    ("kimi_31_pro", "moonshotai/kimi-k3.1-pro", "max", 131072),
    ("gemini_37_flash", "google/gemini-3.7-flash", "high", 65536),
    ("gemini_38_flash", "google/gemini-3.8-flash", "high", 65536),
    ("claude_haiku_55", "anthropic/claude-haiku-5.5", "max", 128000),
    ("muse_spark_13", "meta/muse-spark-1.3", "max", 131072),
    ("glm_5_3_flash_260828_max", "z-ai/glm-5.3-flash", "max", 131072),
    ("gpt_6_luna", "openai/gpt-6-luna", "max", 128000),
    ("deepseek_v41_flash_1017", "deepseek/deepseek-v4.1-flash", "max", 131072),
    ("grok_46", "x-ai/grok-4.6", "xhigh", 128000),
    ("qwen_37_plus", "qwen/qwen3.7-plus", None, 131072),
    ("qwen_37_flash", "qwen/qwen3.7-flash", None, 65536),
    ("gemini_25_pro", "google/gemini-2.5-pro", "max", 65536),
    ("gpt_5", "openai/gpt-5", "high", 128000),
    ("o3", "openai/o3", "high", 100000),
    ("llama_4_maverick", "meta-llama/llama-4-maverick", None, 16384),
    ("gpt_4o_2024_11_20", "openai/gpt-4o-2024-11-20", None, 16384),
    ("gemma_4_31b_it", "google/gemma-4-31b-it", None, 16384),
]
URL = "https://openrouter.ai/api/v1/chat/completions"


def stream_call(key: str, body: dict, timeout: int) -> dict:
    """Stream one request; return text, reasoning, usage and timings."""
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    start = time.monotonic()
    first = None
    content, reasoning, summary = [], [], []
    usage, finish, model = {}, None, None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("error"):
                raise RuntimeError(json.dumps(chunk["error"])[:300])
            model = chunk.get("model") or model
            usage = chunk.get("usage") or usage
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                piece = delta.get("content") or ""
                think = delta.get("reasoning") or ""
                for detail in delta.get("reasoning_details") or []:
                    if detail.get("type") == "reasoning.summary" and detail.get("summary"):
                        summary.append(detail["summary"])
                if (piece or think) and first is None:
                    first = time.monotonic() - start
                content.append(piece)
                reasoning.append(think)
                finish = choice.get("finish_reason") or finish
    return {
        "answer": "".join(content).strip(),
        "reasoning": "".join(reasoning),
        "reasoning_summary": "".join(summary),
        "usage": usage,
        "finish_reason": finish,
        "response_model": model,
        "seconds": round(time.monotonic() - start, 2),
        "first_token_seconds": None if first is None else round(first, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-model", type=int, default=3, help="concurrent requests per model")
    parser.add_argument("--workers", type=int, default=48)
    parser.add_argument("--timeout", type=int, default=900, help="seconds to wait for any chunk")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--only", action="append", default=[], help="model key to run (repeatable)")
    args = parser.parse_args()
    key = os.environ["OPENROUTER_API_KEY"]

    tasks = {t["task_slug"]: t for t in load_tasks(REPO, TASKS)}
    traces_path = HERE / "traces.jsonl"
    done = {
        (r["model_key"], r["task_slug"], r["trial"])
        for r in (read_jsonl(traces_path) if traces_path.exists() else [])
        if r.get("ok")
    }
    models = [m for m in MODELS if not args.only or m[0] in args.only]
    jobs = [(m, slug, trial) for m in models for slug in TASKS for trial in TRIALS if (m[0], slug, trial) not in done]
    print(f"{len(jobs)} requests to run, {len(done)} already done", flush=True)
    gates = {m[0]: threading.Semaphore(args.per_model) for m in models}
    lock = threading.Lock()

    def one(job):
        (model_key, model_id, effort, max_tokens), slug, trial = job
        task = tasks[slug]
        content, figures = build_content(REPO, task)
        body = {
            "model": model_id,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "stream": True,
            "usage": {"include": True},
        }
        if effort:
            body["reasoning"] = {"effort": effort}
        attempts = []
        result = None
        with gates[model_key]:
            for attempt in range(1, args.retries + 1):
                try:
                    result = stream_call(key, body, args.timeout)
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
            "task_slug": slug, "task_path": task["task_path"], "trial": trial, "figures": figures,
            "ok": ok, "attempts": attempts, **(result or {}),
        }
        with lock:
            with traces_path.open("a") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return model_key, slug, trial, ok, (result or {}).get("seconds")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for model_key, slug, trial, ok, seconds in pool.map(one, jobs):
            print(f"{model_key:28s} {slug[:28]:28s} t{trial} ok={ok} {seconds}s", flush=True)

    # The judge's input: the latest successful answer of every (model, task, trial).
    latest = {}
    for row in read_jsonl(traces_path):
        if row.get("ok"):
            latest[(row["model_key"], row["task_slug"], row["trial"])] = row
    with (HERE / "answers.jsonl").open("w") as handle:
        for (model_key, slug, trial), row in sorted(latest.items()):
            handle.write(json.dumps({
                "benchmark": "razavi-bench", "experiment": "2026-11-05-reasoning-traces",
                "task_slug": slug, "task_path": row["task_path"], "rollout": trial,
                "model_name": model_key, "provider_model": row["model"], "reasoning_effort": row["effort"],
                "answer": row["answer"],
            }, ensure_ascii=False) + "\n")
    print(f"answers: {len(latest)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
