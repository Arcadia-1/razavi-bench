#!/usr/bin/env python3
"""Direct-QA runner for Meta models through the local Muse Code CLI (`muse exec`).

Writes the same files as direct_qa_openrouter.py (rollout answer JSONL, raw_logs.jsonl,
judge_input.jsonl, validation_report.json), so judging and publishing are unchanged.

Muse Code is a coding agent, so every run is locked down to a single direct answer:
no shell, file writes, web tools or reminder agents, and at most one model step. A run
counts only if it completes with a non-empty answer from exactly one model call, and
the requested reasoning effort must not be downgraded. Token usage comes from the
session log Muse Code keeps under ~/.local/share/muse/sessions.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from direct_qa_openrouter_common import (
    DEFAULT_SMOKE_TASKS,
    REPO_ROOT,
    append_jsonl,
    canonicalize,
    completed,
    load_tasks,
    read_jsonl,
    write_json,
    write_jsonl,
)

SESSIONS = Path.home() / ".local/share/muse/sessions"
LOCKDOWN = [
    "--contributor-mode", "off",
    "--disable-web-tools",
    "--disable-shell",
    "--disable-write",
    "--disable-reminders",
    "--max-model-steps", "1",
]


def session_usages(session_id: str) -> list[dict[str, Any]]:
    """Every provider usage record in the run's session log, one per model call."""
    logs = list(SESSIONS.glob(f"*/*/*/{session_id}/session.jsonl"))
    if not logs:
        return []
    usages = []
    for line in logs[0].read_text(encoding="utf-8").splitlines():
        if '"usage_family":"provider"' not in line.replace(" ", "") and '"input_tokens"' not in line:
            continue
        found = _find_usage(json.loads(line))
        if found:
            usages.append(found)
    return usages


def _find_usage(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        usage = value.get("usage")
        if isinstance(usage, dict) and "input_tokens" in usage and "output_tokens" in usage:
            return usage
        for child in value.values():
            found = _find_usage(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_usage(child)
            if found:
                return found
    return None


def openai_usage(usage: dict[str, Any]) -> dict[str, Any]:
    """Express a Muse usage record in the OpenAI-style shape the publish tools read."""
    cached = usage.get("cache_read_tokens") or usage.get("cached_tokens") or 0
    return {
        "prompt_tokens": usage["input_tokens"],
        "completion_tokens": usage["output_tokens"],
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        "prompt_tokens_details": {"cached_tokens": cached},
        "completion_tokens_details": {"reasoning_tokens": usage.get("reasoning_tokens")},
    }


def run_once(args: argparse.Namespace, prompt: str, images: list[Path]) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix="razavi-muse-") as workdir:
        prompt_file = Path(workdir) / "prompt.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        empty = Path(workdir) / "empty"
        empty.mkdir()
        command = [
            args.muse, "exec", "--json",
            "--model", args.model,
            "--reasoning-effort", args.effort,
            "--session-id", session_id,
            *LOCKDOWN,
            *[part for image in images for part in ("--image", str(image))],
            "--prompt-file", str(prompt_file),
        ]
        try:
            proc = subprocess.run(command, cwd=empty, capture_output=True, text=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "session_id": session_id, "usages": session_usages(session_id)}
    if "is not available" in proc.stderr and "effort" in proc.stderr:
        raise SystemExit(f"Muse Code downgraded reasoning effort {args.effort!r}: {proc.stderr.strip()[:300]}")
    terminal = {}
    for line in proc.stdout.splitlines():
        payload = (json.loads(line).get("payload") or {}) if line.startswith("{") else {}
        if payload.get("kind") == "run_terminal":
            terminal = payload
    usages = session_usages(session_id)
    answer = terminal.get("text") or ""
    error = None
    if terminal.get("terminal") != "completed":
        error = f"run ended {terminal.get('terminal')!r}: {(terminal.get('reason') or proc.stderr.strip()[-300:])}"
    elif not answer.strip():
        error = "empty answer"
    elif len(usages) != 1:
        error = f"expected one model call, found {len(usages)}"
    return {"ok": error is None, "answer": answer, "error": error, "session_id": session_id, "usages": usages,
            "finish_reason": "stop" if error is None else (terminal.get("terminal") or "error")}


def answer_task(args: argparse.Namespace, task: dict[str, Any]) -> dict[str, Any]:
    images = [args.repo_root / relative for relative in task.get("figures") or []]
    attempts = []
    for attempt in range(1, args.max_retries + 1):
        result = run_once(args, task["instruction"], images)
        attempts.append({
            "attempt": attempt,
            "status": 200,
            "finish_reason": result["finish_reason"] if "finish_reason" in result else "error",
            "session_id": result["session_id"],
            "error": result.get("error"),
            # Usage is kept per attempt so discarded attempts are billed too.
            "usage": openai_usage(result["usages"][0]) if len(result["usages"]) == 1 else
                     _sum_openai([openai_usage(u) for u in result["usages"]]),
        })
        if result["ok"]:
            return {"ok": True, "answer": result["answer"], "usage": attempts[-1]["usage"], "attempts": attempts, "error": None}
        time.sleep(2 * attempt)
    return {"ok": False, "answer": "", "usage": attempts[-1]["usage"], "attempts": attempts, "error": attempts[-1]["error"]}


def _sum_openai(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {}
    return {
        "prompt_tokens": sum(r["prompt_tokens"] for r in records),
        "completion_tokens": sum(r["completion_tokens"] for r in records),
        "total_tokens": sum(r["total_tokens"] for r in records),
        "prompt_tokens_details": {"cached_tokens": sum(r["prompt_tokens_details"]["cached_tokens"] for r in records)},
        "completion_tokens_details": {"reasoning_tokens": sum(r["completion_tokens_details"]["reasoning_tokens"] or 0 for r in records)},
    }


def execute(args: argparse.Namespace, smoke: bool) -> dict[str, Any]:
    args.repo_root = args.repo_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(args.repo_root, args.task_slug or (list(DEFAULT_SMOKE_TASKS) if smoke else None))
    rollouts = sorted(set(args.rollout or [1]))
    paths = {r: output / "model_outputs" / f"{args.output_prefix}-rollout-{r}.jsonl" for r in rollouts}
    done = completed(list(paths.values())) if args.resume else set()
    jobs = [(r, t) for r in rollouts for t in tasks if (r, t["task_slug"]) not in done]
    raw_path = output / "raw_logs.jsonl"
    failures = []
    print(f"model={args.model} effort={args.effort} expected={len(tasks) * len(rollouts)} completed={len(done)} pending={len(jobs)}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(answer_task, args, task): (rollout, task) for rollout, task in jobs}
        for future in concurrent.futures.as_completed(futures):
            rollout, task = futures[future]
            result = future.result()
            figures = list(task.get("figures") or [])
            append_jsonl(raw_path, {
                "experiment": args.experiment, "task_slug": task["task_slug"], "rollout": rollout, "figures": figures,
                "ok": result["ok"], "request": {"route": "muse_code_exec", "effort": args.effort, "lockdown": LOCKDOWN},
                "response_model": args.model, "finish_reason": "stop" if result["ok"] else "error",
                "answer": result["answer"], "usage": result["usage"], "attempts": result["attempts"], "error": result["error"],
            })
            if result["ok"]:
                append_jsonl(paths[rollout], {
                    "benchmark": "razavi-bench", "experiment": args.experiment, "run_date": args.run_date,
                    "task_slug": task["task_slug"], "task_path": task["task_path"], "part": task["part"],
                    "question_number": task["question_number"],
                    "question": task["instruction"].split("## Question\n\n", 1)[-1].strip(),
                    "figures": figures, "rollout": rollout, "answer": result["answer"],
                    "provider_model": args.model, "model_name": args.model_name, "model_family": args.model_family,
                    "reasoning_effort": args.effort, "model_call_attempts": len(result["attempts"]),
                    "internet_or_tool_evidence": False,
                })
            else:
                failures.append({"task_slug": task["task_slug"], "rollout": rollout, "error": result["error"]})
            print(f"{'ok  ' if result['ok'] else 'FAIL'} r{rollout} {task['task_slug']} attempts={len(result['attempts'])}", flush=True)

    for path in paths.values():
        canonicalize(path)
    rows = sorted((row for path in paths.values() for row in read_jsonl(path)), key=lambda row: (row["task_slug"], row["rollout"]))
    write_jsonl(output / "judge_input.jsonl", rows)
    report = {
        "status": "pass" if not failures and len(rows) == len(tasks) * len(rollouts) else "fail",
        "experiment": args.experiment, "model": args.model, "route": "muse_code_exec", "effort": args.effort,
        "lockdown": LOCKDOWN, "expected_answers": len(tasks) * len(rollouts), "valid_answers": len(rows),
        "failures": failures, "judge_input": str(output / "judge_input.jsonl"),
    }
    write_json(output / "validation_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("probe", "run"))
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--model", required=True, help="Muse Code model id, e.g. muse-wonder-full-1.0")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-family", default="meta")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-date", required=True)
    parser.add_argument("--effort", required=True, help="Muse Code reasoning effort, e.g. max")
    parser.add_argument("--task-slug", action="append", default=[])
    parser.add_argument("--rollout", action="append", type=int, default=[])
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--muse", default="muse", help="path to the muse executable")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    report = execute(args, args.command == "probe")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
