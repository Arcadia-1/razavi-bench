#!/usr/bin/env python3
"""Rerun a self-hosted Qwen model with the question's own text and its figure, nothing else.

The prompt is built by run.py's build(): one user message holding the question text
and its figure, no title, headings or system prompt. The model is the official BF16
checkpoint (Qwen/Qwen3.8-27B, revision 8c0b3d30) on vLLM, four copies on four B200s of
zinal reached through SSH tunnels (`ssh -f -N zinal-llm` for ports 18000-18001, plus
18012-18013 forwarded to the servers on ports 8002-8003).

Settings: reasoning_effort "xhigh", the highest level the chat template accepts (it
accepts xhigh, medium and low, and adds xhigh's instruction itself when no level is
given); Qwen's recommended thinking-mode sampling (temperature 1.0, top_p 0.95, and
top_k 20 from the checkpoint's generation_config); no max_tokens, so vLLM allows the
whole 262,144-token context less the prompt, the model's own limit. An answer cut off
there on every attempt is graded as it stands, as in run.py.

Writes runs_selfhosted/qwen_38_27b/requests.jsonl and traces.jsonl in run.py's form
(kept apart from runs/, which run.py reads while other entries run) and
answers_selfhosted.jsonl. Reruns skip slots already answered with the current
question, figures and settings.

`--model qwen-9b` runs Qwen 3.5 9B instead (BF16, revision c2022362), on GPUs 0-3 of zinal
switched to it with swap_card.sh (ports 8100-8103, tunnelled to 18100-18103): thinking on, the
model's only reasoning setting; the same sampling and no max_tokens. It writes
runs_selfhosted/qwen_35_9b/ and answers_selfhosted_9b.jsonl.

`--model nemotron` runs Nemotron 3.5 Super VL (BF16, nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16,
revision fb0ee0bc) as two tensor-parallel copies on GPUs 0-1 and 2-3 of zinal (serve_supervl.sh,
ports 8100-8101, tunnelled to 18100-18101): full reasoning, the chat template's default and highest
level; the model card's sampling (temperature 1.0, top_p 0.95); no max_tokens. It writes
runs_selfhosted/nemotron_35_super_vl/ and answers_selfhosted_nemotron.jsonl.

`--model glm` runs GLM 5.3 Flash from its BF16 weights (zai-org/GLM-5.3-Flash-BF16, revision f9fed3bb;
the default repository is FP8) as one tensor-parallel copy on GPUs 0-3 of zinal (serve_glm.sh, port 8200,
tunnelled to 18200): reasoning effort max, the template default; generation_config's sampling
(temperature 1.0, top_p 0.95); no max_tokens. It writes runs_selfhosted/glm_5_3_flash_260828_max/ and
answers_selfhosted_glm.jsonl.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)

# The two self-hosted entries. The 27B's chat template accepts reasoning_effort xhigh, medium
# and low (xhigh, the highest, is sent); the 9B has no effort levels, only thinking on (the
# template default, sent as is). Both use Qwen's thinking-mode sampling, as published.
MODELS = {
    "qwen-27b": {"model_key": "qwen_38_27b", "display_name": "Qwen 3.8 27B", "checkpoint": "Qwen/Qwen3.8-27B",
                 "servers": ["http://localhost:18000", "http://localhost:18001", "http://localhost:18012", "http://localhost:18013"],
                 "settings": {"model": "qwen3.8-27b", "reasoning_effort": "xhigh", "temperature": 1.0, "top_p": 0.95},
                 "answers": "answers_selfhosted.jsonl"},
    "qwen-9b": {"model_key": "qwen_35_9b", "display_name": "Qwen 3.5 9B", "checkpoint": "Qwen/Qwen3.5-9B",
                "servers": ["http://localhost:18100", "http://localhost:18101", "http://localhost:18102", "http://localhost:18103"],
                "settings": {"model": "qwen3.5-9b", "temperature": 1.0, "top_p": 0.95},
                "answers": "answers_selfhosted_9b.jsonl"},
    # Full reasoning is the chat template default (enable_thinking on, medium_effort off), the
    # highest of its off / medium / on levels, so nothing is sent for it. Two TP=2 copies on GPUs 0-3.
    "nemotron": {"model_key": "nemotron_35_super_vl", "display_name": "Nemotron 3.5 Super VL",
                 "checkpoint": "nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16",
                 "servers": ["http://localhost:18100", "http://localhost:18101"],
                 "settings": {"model": "nemotron-3.5-super-vl", "temperature": 1.0, "top_p": 0.95},
                 "answers": "answers_selfhosted_nemotron.jsonl", "max_model_len": None},
    # The chat template sets "Reasoning Effort: Max" unless low or high is asked for, so max, the
    # highest level, is the default and nothing is sent. One TP=4 copy (16 sequences) on GPUs 0-3.
    "glm": {"model_key": "glm_5_3_flash_260828_max", "display_name": "GLM 5.3 Flash",
            "checkpoint": "zai-org/GLM-5.3-Flash-BF16", "servers": ["http://localhost:18200"],
            "settings": {"model": "glm-5.3-flash", "temperature": 1.0, "top_p": 0.95},
            "answers": "answers_selfhosted_glm.jsonl"},
}


def configure(name: str) -> None:
    """Point the module at one entry (its key, servers, settings and output paths)."""
    global MODEL_KEY, DISPLAY_NAME, CHECKPOINT, SERVERS, SETTINGS, OUT, ANSWERS, MAX_MODEL_LEN
    entry = MODELS[name]
    MODEL_KEY, DISPLAY_NAME, CHECKPOINT = entry["model_key"], entry["display_name"], entry["checkpoint"]
    SERVERS, SETTINGS, MAX_MODEL_LEN = entry["servers"], entry["settings"], entry.get("max_model_len", 262144)
    OUT, ANSWERS = HERE / "runs_selfhosted" / MODEL_KEY, HERE / entry["answers"]


configure("qwen-27b")


def check_servers() -> None:
    for server in SERVERS:
        with urllib.request.urlopen(server + "/v1/models", timeout=20) as response:
            model = json.loads(response.read())["data"][0]
        expected = MAX_MODEL_LEN or model["max_model_len"]  # None: the server's own (model default) length
        assert (model["id"], model["root"], model["max_model_len"]) == (SETTINGS["model"], CHECKPOINT, expected), (server, model)
        print(f"{server}: {model['id']} max_model_len {model['max_model_len']}", flush=True)


def stream(server: str, body: dict, timeout: int) -> dict:
    request = urllib.request.Request(server + "/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
    start, first = time.monotonic(), None
    content, reasoning, usage, finish = [], [], None, None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[5:])
            if chunk.get("error"):
                raise RuntimeError(json.dumps(chunk["error"])[:300])
            usage = chunk.get("usage") or usage
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                think = delta.get("reasoning") or delta.get("reasoning_content") or ""
                text = delta.get("content") or ""
                if (think or text) and first is None:
                    first = time.monotonic() - start
                reasoning.append(think)
                content.append(text)
                finish = choice.get("finish_reason") or finish
    answer, cleaned = "".join(content), False
    if "</think>" in answer:  # reasoning that reached the final text; keep what follows the tag
        answer, cleaned = answer.rsplit("</think>", 1)[1].strip(), True
    return {"answer": answer.strip(), "answer_cleaned": cleaned, "reasoning": "".join(reasoning), "usage": usage,
            "finish_reason": finish, "seconds": round(time.monotonic() - start, 2), "first_token_seconds": round(first or 0, 2)}


def current(row: dict, task: dict) -> bool:
    figures = [hashlib.sha256((run.REPO / relative).read_bytes()).hexdigest() for relative in task.get("figures") or []]
    return (run.answered(row) and row.get("settings") == SETTINGS and row.get("question") == run.question_only(task)
            and [f["sha256"] for f in row.get("figures", [])] == figures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=sorted(MODELS), default="qwen-27b")
    parser.add_argument("--servers", nargs="+", help="override the entry's server URLs (e.g. when fewer copies run)")
    parser.add_argument("--workers", type=int, default=150)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    configure(args.model)
    global SERVERS
    SERVERS = args.servers or SERVERS

    check_servers()
    tasks = {t["task_slug"]: t for t in run.probe.load_tasks(run.REPO)}
    OUT.mkdir(parents=True, exist_ok=True)
    done = {(r["task_slug"], r["rollout"]) for r in run.read_traces(OUT) if current(r, tasks[r["task_slug"]])}
    jobs = [(slug, rollout) for rollout in run.ROLLOUTS for slug in sorted(tasks) if (slug, rollout) not in done]
    print(f"{len(jobs)} requests to run on {len(SERVERS)} servers", flush=True)
    lock = threading.Lock()

    def one(numbered):
        number, (slug, rollout) = numbered
        server = SERVERS[number % len(SERVERS)]
        content, logged = run.build(tasks[slug])
        body = {**SETTINGS, "messages": [{"role": "user", "content": content}], "stream": True,
                "stream_options": {"include_usage": True}}
        sent = {**body, "messages": [{"role": "user", "content": logged}]}
        attempts, result = [], None
        for attempt in range(1, args.retries + 1):
            try:
                result = stream(server, body, args.timeout)
                attempts.append({"attempt": attempt, "seconds": result["seconds"], "finish_reason": result["finish_reason"],
                                 "usage": result["usage"]})
                if result["answer"] and result["finish_reason"] in run.FINISHED:
                    break
            except Exception as error:  # noqa: BLE001 - every failure is recorded and retried
                attempts.append({"attempt": attempt, "error": str(error)[:300]})
                result = None
            time.sleep(5 * attempt)
        row = {"model_key": MODEL_KEY, "display_name": DISPLAY_NAME, "model": CHECKPOINT, "settings": SETTINGS,
               "effort": SETTINGS.get("reasoning_effort", "default"), "server": server, "task_slug": slug,
               "task_path": tasks[slug]["task_path"], "question": content[0]["text"], "rollout": rollout,
               "figures": [part["image"] for part in logged[1:]], "attempts": attempts, **(result or {})}
        row["ok"] = ok = run.answered(row)
        with lock:
            with (OUT / "requests.jsonl").open("a") as h:
                h.write(json.dumps({"task_slug": slug, "rollout": rollout, "server": server, "body": sent}, ensure_ascii=False) + "\n")
            with (OUT / "traces.jsonl").open("a") as h:
                h.write(json.dumps(row, ensure_ascii=False) + "\n")
        out_tokens = ((result or {}).get("usage") or {}).get("completion_tokens")
        return slug, rollout, ok, (result or {}).get("seconds"), out_tokens

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n, (slug, rollout, ok, seconds, out_tokens) in enumerate(pool.map(one, enumerate(jobs)), 1):
            print(f"{n:3d} {slug[:34]:34s} r{rollout} ok={ok} {seconds}s out={out_tokens}", flush=True)

    latest = {}
    for r in run.read_traces(OUT):
        if current(r, tasks[r["task_slug"]]):
            latest[(r["task_slug"], r["rollout"])] = r
    with ANSWERS.open("w") as h:
        for (slug, rollout), r in sorted(latest.items()):
            h.write(json.dumps({"benchmark": "razavi-bench", "experiment": "2026-11-09-question-only-rerun", "task_slug": slug,
                                "task_path": r["task_path"], "rollout": rollout, "model_name": MODEL_KEY,
                                "provider_model": f"{CHECKPOINT} (self-hosted)", "reasoning_effort": r["effort"],
                                "finish_reason": r["finish_reason"], "answer": r["answer"]}, ensure_ascii=False) + "\n")
    print(f"answers: {len(latest)} of {len(tasks) * len(run.ROLLOUTS)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
