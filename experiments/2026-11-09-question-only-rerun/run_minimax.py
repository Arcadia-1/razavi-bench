#!/usr/bin/env python3
"""Run MiniMax M3.1 Flash or M3 with the question's own text and its figure, through MiniMax's own API.

The prompt is built by run.py's build(): one user message holding the question text and
its figure, no title, headings or system prompt. Requests go to MiniMax's mainland
platform (https://api.minimaxi.com/v1, MINIMAX_API_KEY, a Token Plan key) rather than
OpenRouter, with reasoning_effort "max" (the highest level, also MiniMax's default; thinking
cannot be turned off) and max_completion_tokens 524,288, the model's output limit as
OpenRouter lists it (MiniMax counts thinking tokens against it and documents no lower cap).
Reasoning comes back in reasoning_content. An answer cut off at that limit is re-run; one
cut off on every attempt is graded as it stands, as in run.py.

`--model m3` runs MiniMax M3 instead: it has no effort levels (reasoning_effort only affects M3.1
Flash) and thinks by default, so nothing is sent for them; reasoning_split true returns the
reasoning in reasoning_content; max_completion_tokens 512,000, its OpenRouter output limit. The
published M3 entry was rerun through OpenRouter (runs/minimax_m3); this run is a cross-check
through MiniMax's own API and writes runs_minimax/minimax_m3/ and answers_minimax_m3.jsonl.

Writes runs_minimax/<model_key>/requests.jsonl and traces.jsonl in run.py's form and
answers_minimax.jsonl (M3.1 Flash). Reruns skip slots already answered with the current question,
figures and settings. MiniMax M3.1 Flash is a local entry (not published).

Usage: python3 run_minimax.py [--model m31-flash|m3] [--probe] [--workers N]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)

URL = "https://api.minimaxi.com/v1/chat/completions"
MODELS = {
    "m31-flash": ("minimax_m31_flash", "MiniMax M3.1 Flash", "answers_minimax.jsonl",
                  {"model": "MiniMax-M3.1-Flash", "reasoning_effort": "max", "max_completion_tokens": 524288}),
    "m3": ("minimax_m3", "MiniMax M3", "answers_minimax_m3.jsonl",
           {"model": "MiniMax-M3", "reasoning_split": True, "max_completion_tokens": 512000}),
}


def configure(name: str) -> None:
    global MODEL_KEY, DISPLAY_NAME, MODEL, SETTINGS, OUT, ANSWERS
    MODEL_KEY, DISPLAY_NAME, answers, SETTINGS = MODELS[name]
    MODEL, OUT, ANSWERS = SETTINGS["model"], HERE / "runs_minimax" / MODEL_KEY, HERE / answers


configure("m31-flash")


def stream(body: dict, timeout: int) -> dict:
    request = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {os.environ['MINIMAX_API_KEY']}"})
    start, first = time.monotonic(), None
    content, reasoning, usage, finish = [], [], None, None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[5:])
            if chunk.get("error") or (chunk.get("base_resp") or {}).get("status_code"):
                raise RuntimeError(json.dumps(chunk.get("error") or chunk.get("base_resp"))[:300])
            usage = chunk.get("usage") or usage
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                think = delta.get("reasoning_content") or delta.get("reasoning") or ""
                text = delta.get("content") or ""
                if (think or text) and first is None:
                    first = time.monotonic() - start
                reasoning.append(think)
                content.append(text)
                finish = choice.get("finish_reason") or finish
    answer = "".join(content).strip()
    if "</think>" in answer:  # reasoning that reached the final text; keep what follows the tag
        answer = answer.rsplit("</think>", 1)[1].strip()
    return {"answer": answer, "reasoning": "".join(reasoning), "usage": usage, "finish_reason": finish,
            "seconds": round(time.monotonic() - start, 2), "first_token_seconds": round(first or 0, 2)}


def current(row: dict, task: dict) -> bool:
    figures = [hashlib.sha256((run.REPO / relative).read_bytes()).hexdigest() for relative in task.get("figures") or []]
    return (run.answered(row) and row.get("settings") == SETTINGS and row.get("question") == run.question_only(task)
            and [f["sha256"] for f in row.get("figures", [])] == figures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=sorted(MODELS), default="m31-flash")
    parser.add_argument("--probe", action="store_true", help="send one figure question once and print the result")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=900, help="per-read socket timeout (seconds)")
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    configure(args.model)
    tasks = {t["task_slug"]: t for t in run.probe.load_tasks(run.REPO)}

    def body_for(slug):
        content, logged = run.build(tasks[slug])
        body = {**SETTINGS, "messages": [{"role": "user", "content": content}], "stream": True,
                "stream_options": {"include_usage": True}}
        return body, {**body, "messages": [{"role": "user", "content": logged}]}, content

    if args.probe:
        body, _, _ = body_for("part1-021-cascode-structure")
        result = stream(body, args.timeout)
        print(json.dumps({k: result[k] for k in ("finish_reason", "usage", "seconds", "first_token_seconds")}),
              "| reasoning chars", len(result["reasoning"]), "| answer:", result["answer"][:300])
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    done = {(r["task_slug"], r["rollout"]) for r in run.read_traces(OUT) if current(r, tasks[r["task_slug"]])}
    jobs = [(slug, rollout) for rollout in run.ROLLOUTS for slug in sorted(tasks) if (slug, rollout) not in done]
    print(f"{len(jobs)} requests to run", flush=True)
    lock = threading.Lock()

    def one(job):
        slug, rollout = job
        body, sent, content = body_for(slug)
        attempts, result = [], None
        for attempt in range(1, args.retries + 1):
            try:
                result = stream(body, args.timeout)
                attempts.append({"attempt": attempt, "seconds": result["seconds"], "finish_reason": result["finish_reason"],
                                 "usage": result["usage"]})
                if result["answer"] and result["finish_reason"] in run.FINISHED:
                    break
            except Exception as error:  # noqa: BLE001 - every failure is recorded and retried
                attempts.append({"attempt": attempt, "error": str(error)[:300]})
                result = None
            time.sleep(min(240, 15 * 2 ** attempt) if "429" in attempts[-1].get("error", "") else 5 * attempt)
        row = {"model_key": MODEL_KEY, "display_name": DISPLAY_NAME, "model": MODEL, "settings": SETTINGS,
               "effort": SETTINGS.get("reasoning_effort", "default"), "max_tokens": SETTINGS["max_completion_tokens"],
               "task_slug": slug, "task_path": tasks[slug]["task_path"], "question": content[0]["text"],
               "rollout": rollout, "figures": [part["image"] for part in sent["messages"][0]["content"][1:]],
               "attempts": attempts, **(result or {})}
        row["ok"] = ok = run.answered(row)
        with lock:
            with (OUT / "requests.jsonl").open("a") as h:
                h.write(json.dumps({"task_slug": slug, "rollout": rollout, "body": sent}, ensure_ascii=False) + "\n")
            with (OUT / "traces.jsonl").open("a") as h:
                h.write(json.dumps(row, ensure_ascii=False) + "\n")
        out_tokens = ((result or {}).get("usage") or {}).get("completion_tokens")
        return slug, rollout, ok, (result or {}).get("seconds"), out_tokens

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n, (slug, rollout, ok, seconds, out_tokens) in enumerate(pool.map(one, jobs), 1):
            print(f"{n:3d} {slug[:34]:34s} r{rollout} ok={ok} {seconds}s out={out_tokens}", flush=True)

    latest = {}
    for r in run.read_traces(OUT):
        if current(r, tasks[r["task_slug"]]):
            latest[(r["task_slug"], r["rollout"])] = r
    with ANSWERS.open("w") as h:
        for (slug, rollout), r in sorted(latest.items()):
            h.write(json.dumps({"benchmark": "razavi-bench", "experiment": "2026-11-09-question-only-rerun", "task_slug": slug,
                                "task_path": r["task_path"], "rollout": rollout, "model_name": MODEL_KEY,
                                "provider_model": MODEL, "reasoning_effort": r["effort"], "finish_reason": r["finish_reason"],
                                "answer_status": "returned" if r["answer"] else "no_final_answer_at_output_limit",
                                "answer": r["answer"]}, ensure_ascii=False) + "\n")
    print(f"answers: {len(latest)} of {len(tasks) * len(run.ROLLOUTS)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
