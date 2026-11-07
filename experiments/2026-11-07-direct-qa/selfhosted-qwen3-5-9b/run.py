#!/usr/bin/env python3
"""Answer all 50 tasks three times with the self-hosted Qwen3.5-9B, thinking on (its default).

Local test, not for the leaderboard. The vLLM server runs on zinal; reach it through
`ssh -f -N zinal-llm` (localhost:18001). The 9B server has no effort levels, only thinking
on or off, so no effort is sent. Requests are streamed so long reasoning does
not drop an idle connection. Writes traces.jsonl (one row per request: timing, usage,
reasoning, answer; resumable) and answers.jsonl (the latest successful answer of every
task and trial, in the form tools/evaluate_answers.py reads).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools"))
from direct_qa_openrouter_common import build_content, load_tasks, read_jsonl  # noqa: E402

URL = "http://localhost:18001/v1/chat/completions"
MODEL = "qwen3.5-9b"
EFFORT = "default"
MAX_TOKENS = 245_760          # 240K of the 262,144-token context, leaving room for the prompt
SAMPLING = {"temperature": 1.0, "top_p": 0.95}   # Qwen's recommended thinking-mode sampling
EXPERIMENT = "2026-11-07-direct-qa-selfhosted-qwen35-9b"


def stream(body: dict, timeout: int) -> dict:
    request = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    start = time.time()
    first = None
    content, reasoning, usage, finish = [], [], None, None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[5:])
            if chunk.get("usage"):
                usage = chunk["usage"]
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                think = delta.get("reasoning") or delta.get("reasoning_content") or ""
                text = delta.get("content") or ""
                if (think or text) and first is None:
                    first = time.time() - start
                reasoning.append(think)
                content.append(text)
                finish = choice.get("finish_reason") or finish
    return {"answer": "".join(content), "reasoning": "".join(reasoning), "usage": usage, "finish_reason": finish,
            "seconds": round(time.time() - start, 2), "first_token_seconds": round(first or 0, 2)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    traces_path = HERE / "traces.jsonl"
    done = {(r["task_slug"], r["trial"]) for r in read_jsonl(traces_path) if r.get("ok")} if traces_path.exists() else set()
    tasks = load_tasks(REPO)
    jobs = [(task, trial) for trial in (1, 2, 3) for task in tasks if (task["task_slug"], trial) not in done]
    print(f"{len(jobs)} answers to generate", flush=True)
    lock = threading.Lock()

    def one(job):
        task, trial = job
        content, figures = build_content(REPO, task)
        body = {"model": MODEL, "messages": [{"role": "user", "content": content}], "max_tokens": MAX_TOKENS,
                "stream": True, "stream_options": {"include_usage": True}, **SAMPLING}
        row = {"task_slug": task["task_slug"], "task_path": f"tasks/{task['task_slug']}", "trial": trial,
               "figures": figures, "ok": False, "attempts": []}
        for attempt in range(1, args.retries + 1):
            try:
                result = stream(body, args.timeout)
                row["attempts"].append({"attempt": attempt, "seconds": result["seconds"], "usage": result["usage"],
                                        "finish_reason": result["finish_reason"]})
                if result["answer"].strip() and result["finish_reason"] == "stop":
                    row.update(result, ok=True)
                    break
            except Exception as error:  # noqa: BLE001
                row["attempts"].append({"attempt": attempt, "error": str(error)[:300]})
                time.sleep(5 * attempt)
        with lock, traces_path.open("a") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return task["task_slug"], trial, row["ok"], row.get("seconds"), (row.get("usage") or {}).get("completion_tokens")

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        for n, (slug, trial, ok, seconds, out) in enumerate(pool.map(one, jobs), 1):
            print(f"{n:3d} {slug[:40]:40s} t{trial} ok={ok} {seconds}s out={out}", flush=True)

    latest = {}
    for row in read_jsonl(traces_path):
        if row.get("ok"):
            latest[(row["task_slug"], row["trial"])] = row
    with (HERE / "answers.jsonl").open("w") as handle:
        for (slug, trial), row in sorted(latest.items()):
            handle.write(json.dumps({
                "benchmark": "razavi-bench", "experiment": EXPERIMENT, "task_slug": slug, "task_path": row["task_path"],
                "rollout": trial, "model_name": "qwen_35_9b", "provider_model": "Qwen/Qwen3.5-9B (self-hosted)",
                "reasoning_effort": EFFORT, "answer": row["answer"],
            }, ensure_ascii=False) + "\n")
    print(f"answers: {len(latest)} of 150", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
