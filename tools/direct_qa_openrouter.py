#!/usr/bin/env python3
"""Public OpenRouter Direct-QA CLI."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
from typing import Any

from direct_qa_openrouter_common import (
    DEFAULT_BASE_URL,
    DEFAULT_SMOKE_TASKS,
    REPO_ROOT,
    append_jsonl,
    build_content,
    call_model,
    canonicalize,
    completed,
    endpoint as endpoint_for,
    load_tasks,
    model_reasoning,
    payload as build_payload,
    read_jsonl,
    redact,
    resolve_effort,
    write_json,
    write_jsonl,
)


def raw_record(task: dict[str, Any], rollout: int, figures: list[str], result: dict[str, Any], summary: dict[str, Any], experiment: str) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "task_slug": task["task_slug"],
        "rollout": rollout,
        "figures": figures,
        "ok": result["ok"],
        "request": summary,
        "response_model": result.get("response_model"),
        "finish_reason": result.get("finish_reason"),
        "answer": result.get("answer") or "",
        "usage": result.get("usage") or {},
        "attempts": result.get("attempts") or [],
        "error": result.get("error"),
    }


def public_record(task: dict[str, Any], rollout: int, figures: list[str], result: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    return {
        "benchmark": "razavi-bench",
        "experiment": args.experiment,
        "run_date": args.run_date,
        "task_slug": task["task_slug"],
        "task_path": task["task_path"],
        "part": task["part"],
        "question_number": task["question_number"],
        "question": task["instruction"].split("## Question\n\n", 1)[-1].strip(),
        "figures": figures,
        "rollout": rollout,
        "answer": result["answer"],
        "provider_model": args.model,
        "model_name": args.model_name,
        "model_family": args.model_family,
        "reasoning_effort": args.effort,
        "model_call_attempts": len(result.get("attempts") or []),
        "internet_or_tool_evidence": False,
    }


def check_effort(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve --effort against the efforts OpenRouter lists for the model, before any paid call."""
    if args.skip_effort_check:
        return {"checked": False, "effort": args.effort, "reason": "--skip-effort-check"}
    reasoning = model_reasoning(args.base_url, args.model)
    requested = args.effort
    args.effort, notice = resolve_effort(requested, reasoning)
    if notice:
        print(f"note: {notice}", flush=True)
    return {
        "checked": True,
        "requested": requested,
        "effort": args.effort,
        "supported_efforts": (reasoning or {}).get("supported_efforts"),
        "notice": notice,
    }


def execute(args: argparse.Namespace, smoke: bool = False) -> dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("missing OPENROUTER_API_KEY")
    if min(args.concurrency, args.timeout, args.max_tokens, args.max_retries) < 1:
        raise ValueError("numeric arguments must be positive")

    effort_check = check_effort(args)

    root = args.repo_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(root, args.task_slug or (list(DEFAULT_SMOKE_TASKS) if smoke else None))
    rollouts = sorted(set(args.rollout or [1]))
    paths = {rollout: output / "model_outputs" / f"{args.output_prefix}-rollout-{rollout}.jsonl" for rollout in rollouts}
    done = completed(list(paths.values())) if args.resume else set()
    jobs = [(rollout, task) for rollout in rollouts for task in tasks if (rollout, task["task_slug"]) not in done]
    url = endpoint_for(args.base_url)
    raw_path = output / "raw_logs.jsonl"
    failures = []
    print(f"model={args.model} expected={len(tasks) * len(rollouts)} completed={len(done)} pending={len(jobs)}", flush=True)

    def one(job):
        rollout, task = job
        content, figures = build_content(root, task)
        body = build_payload(args.model, content, args.effort, args.max_tokens)
        result = call_model(url, key, body, args.timeout, args.max_retries)
        request = {"reasoning": body.get("reasoning"), "content_blocks": [part["type"] for part in content]}
        return rollout, task, figures, result, request

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            rollout, task, figures, result, request = future.result()
            append_jsonl(raw_path, raw_record(task, rollout, figures, result, request, args.experiment))
            if result["ok"]:
                append_jsonl(paths[rollout], public_record(task, rollout, figures, result, args))
            else:
                failures.append({"task_slug": task["task_slug"], "rollout": rollout, "error": result["error"]})

    for path in paths.values():
        canonicalize(path)
    rows = sorted((row for path in paths.values() for row in read_jsonl(path)), key=lambda row: (row["task_slug"], row["rollout"]))
    judge_input = output / "judge_input.jsonl"
    write_jsonl(judge_input, rows)
    report = {
        "status": "pass" if not failures and len(rows) == len(tasks) * len(rollouts) else "fail",
        "experiment": args.experiment,
        "model": args.model,
        "base_url": args.base_url,
        "effort": args.effort,
        "max_tokens": args.max_tokens,
        "expected_answers": len(tasks) * len(rollouts),
        "valid_answers": len(rows),
        "text_answers": sum(not row["figures"] for row in rows),
        "image_answers": sum(bool(row["figures"]) for row in rows),
        "effort_check": effort_check,
        "failures": failures,
        "judge_input": str(judge_input),
    }
    write_json(output / "validation_report.json", report)
    return report


def audit(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    output = args.output_dir.resolve()
    tasks = load_tasks(root, args.task_slug or None)
    task_map = {task["task_slug"]: task for task in tasks}
    rollouts = sorted(set(args.rollout or [1]))
    rows = [row for rollout in rollouts for row in read_jsonl(output / "model_outputs" / f"{args.output_prefix}-rollout-{rollout}.jsonl")]
    raw_rows = read_jsonl(output / "raw_logs.jsonl")
    answers = {(row["rollout"], row["task_slug"]): row for row in rows}
    raws = {(row["rollout"], row["task_slug"]): row for row in raw_rows}
    expected = {(rollout, slug) for rollout in rollouts for slug in task_map}
    failures = []
    for key in sorted(expected):
        answer, raw, task = answers.get(key), raws.get(key), task_map[key[1]]
        if answer is None:
            failures.append({"key": list(key), "reason": "missing_answer"})
            continue
        if not answer["answer"].strip() or answer["reasoning_effort"] != args.effort:
            failures.append({"key": list(key), "reason": "invalid_answer"})
        if answer["figures"] != task.get("figures", []):
            failures.append({"key": list(key), "reason": "figure_mismatch"})
        if raw is None or not raw.get("ok") or raw.get("finish_reason") != "stop" or raw.get("answer") != answer["answer"]:
            failures.append({"key": list(key), "reason": "invalid_raw_log"})
        if int((raw or {}).get("usage", {}).get("total_tokens") or 0) <= 0:
            failures.append({"key": list(key), "reason": "missing_usage"})
    report = {
        "status": "pass" if not failures and len(rows) == len(expected) else "fail",
        "expected_records": len(expected),
        "answer_records": len(rows),
        "raw_records": len(raw_rows),
        "effort": args.effort,
        "failures": failures,
    }
    write_json(output / "audit.json", report)
    return report


def add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-family", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-date", required=True)
    parser.add_argument("--task-slug", action="append", default=[])
    parser.add_argument("--rollout", action="append", type=int, default=[])
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--effort",
        default="top",
        help='reasoning effort: "top" (the highest the model lists, the default), "default" (provider default), or a listed effort such as high',
    )
    parser.add_argument(
        "--skip-effort-check",
        action="store_true",
        help="do not check --effort against OpenRouter's model list (for endpoints that are not OpenRouter)",
    )
    parser.add_argument("--max-tokens", type=int, default=131072)
    parser.add_argument("--timeout", type=int, default=5400)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--resume", action="store_true")


def add_audit_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--task-slug", action="append", default=[])
    parser.add_argument("--rollout", action="append", type=int, default=[])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "probe"):
        add_run_args(commands.add_parser(name))
    add_audit_args(commands.add_parser("audit"))
    args = parser.parse_args()
    report = audit(args) if args.command == "audit" else execute(args, args.command == "probe")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
