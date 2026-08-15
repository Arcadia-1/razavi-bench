#!/usr/bin/env python3
"""Run Razavi-Bench Direct QA against a supported multimodal API."""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import mimetypes
import os
import random
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_content(path: Path, api_format: str) -> dict[str, Any]:
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    if api_format == "anthropic_messages":
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded,
            },
        }
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{encoded}"},
    }


def response_text(body: dict[str, Any], api_format: str) -> tuple[str, str]:
    if api_format == "anthropic_messages":
        content = body.get("content") or []
        text = "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
        return text, str(body.get("stop_reason") or "")
    choices = body.get("choices") or []
    if not choices:
        return "", ""
    choice = choices[0] or {}
    content = (choice.get("message") or {}).get("content")
    if isinstance(content, str):
        return content, str(choice.get("finish_reason") or "")
    if isinstance(content, list):
        text = "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
        return text, str(choice.get("finish_reason") or "")
    return "", str(choice.get("finish_reason") or "")


def post_json(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: int,
    api_format: str,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_format == "anthropic_messages":
        headers.update({"x-api-key": api_key, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def load_completed(paths: list[Path]) -> set[tuple[int, str]]:
    completed: set[tuple[int, str]] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                if str(row.get("answer") or "").strip():
                    completed.add((int(row["rollout"]), str(row["task_slug"])))
    return completed


def canonicalize_jsonl(path: Path) -> None:
    if not path.exists():
        return
    rows_by_task: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                row = json.loads(line)
                rows_by_task[str(row["task_slug"])] = row
    rows = sorted(rows_by_task.values(), key=lambda row: str(row["task_slug"]))
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


async def main_async(args: argparse.Namespace) -> int:
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        raise SystemExit(f"missing API key environment variable: {args.api_key_env}")

    task_dirs = sorted(path for path in (REPO_ROOT / "tasks").iterdir() if path.is_dir())
    if len(task_dirs) != 50:
        raise SystemExit(f"expected 50 tasks, found {len(task_dirs)}")
    if args.task_slug:
        tasks_by_slug = {path.name: path for path in task_dirs}
        missing = sorted(set(args.task_slug) - tasks_by_slug.keys())
        if missing:
            raise SystemExit(f"unknown task slug(s): {', '.join(missing)}")
        task_dirs = [tasks_by_slug[slug] for slug in sorted(set(args.task_slug))]

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.raw_dir.resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        rollout: output_dir / f"{args.output_prefix}-rollout-{rollout}.jsonl"
        for rollout in args.rollout
    }
    completed = load_completed(list(output_paths.values())) if args.resume else set()
    jobs = [
        (rollout, task_dir)
        for rollout in args.rollout
        for task_dir in task_dirs
        if (rollout, task_dir.name) not in completed
    ]
    total_expected = len(args.rollout) * len(task_dirs)
    print(
        f"model={args.model} total={total_expected} completed={len(completed)} "
        f"pending={len(jobs)} concurrency={args.concurrency}",
        flush=True,
    )

    semaphore = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    counters = {"completed": len(completed), "failed": 0}
    api_path = "/v1/messages" if args.api_format == "anthropic_messages" else "/chat/completions"
    api_url = args.base_url.rstrip("/") + api_path
    commit = git_commit()

    async def run_one(rollout: int, task_dir: Path) -> None:
        instruction = (task_dir / "instruction.md").read_text(encoding="utf-8")
        images = sorted(task_dir.glob("*.png"))
        content = [image_content(path, args.api_format) for path in images]
        content.append({"type": "text", "text": instruction})
        payload = {
            "model": args.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "stream": False,
        }
        error = ""
        async with semaphore:
            for attempt in range(1, args.attempts + 1):
                started = time.monotonic()
                try:
                    body = await asyncio.to_thread(
                        post_json,
                        api_url,
                        api_key,
                        payload,
                        args.timeout,
                        args.api_format,
                    )
                    elapsed = round(time.monotonic() - started, 3)
                    answer, finish_reason = response_text(body, args.api_format)
                    if not answer.strip():
                        raise ValueError("empty model response")

                    raw_path = raw_dir / f"rollout-{rollout}" / f"{task_dir.name}.json"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_record = {
                        "task_path": str(task_dir.relative_to(REPO_ROOT)),
                        "rollout": rollout,
                        "model": args.model,
                        "temperature": args.temperature,
                        "max_tokens": args.max_tokens,
                        "elapsed_seconds": elapsed,
                        "attempt": attempt,
                        "images": [
                            {
                                "path": str(path.relative_to(REPO_ROOT)),
                                "sha256": sha256_file(path),
                            }
                            for path in images
                        ],
                        "response": body,
                    }
                    raw_path.write_text(
                        json.dumps(raw_record, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    public_record = {
                        "answer": answer,
                        "answer_rounds": 1,
                        "benchmark": "razavi-bench",
                        "experiment": args.experiment,
                        "figures": [path.name for path in images],
                        "internet_or_tool_evidence": False,
                        "model_call_attempts": attempt,
                        "model_family": args.model_family,
                        "model_name": args.model_name,
                        "provider_model": args.model,
                        "question": instruction,
                        "release": commit,
                        "rollout": rollout,
                        "run_date": args.run_date,
                        "task_path": str(task_dir.relative_to(REPO_ROOT)),
                        "task_slug": task_dir.name,
                    }
                    async with write_lock:
                        with output_paths[rollout].open("a", encoding="utf-8") as file:
                            file.write(
                                json.dumps(public_record, ensure_ascii=False, sort_keys=True)
                                + "\n"
                            )
                        counters["completed"] += 1
                        print(
                            f"OK {counters['completed']}/{total_expected} r{rollout} "
                            f"{task_dir.name} images={len(images)} chars={len(answer)} "
                            f"finish={finish_reason} elapsed={elapsed}s attempts={attempt}",
                            flush=True,
                        )
                    return
                except Exception as exc:
                    elapsed = round(time.monotonic() - started, 3)
                    if isinstance(exc, urllib.error.HTTPError):
                        detail = exc.read().decode("utf-8", "replace")[:1000]
                        error = f"HTTP {exc.code}: {detail}"
                    else:
                        error = f"{type(exc).__name__}: {exc}"
                    print(
                        f"RETRY r{rollout} {task_dir.name} attempt={attempt} "
                        f"elapsed={elapsed}s error={error[:300]}",
                        flush=True,
                    )
                    if attempt < args.attempts:
                        await asyncio.sleep(min(60, 2**attempt + random.random() * 2))

        async with write_lock:
            counters["failed"] += 1
            print(
                f"FAILED r{rollout} {task_dir.name} after={args.attempts} "
                f"error={error[:500]}",
                flush=True,
            )

    await asyncio.gather(*(run_one(rollout, task_dir) for rollout, task_dir in jobs))
    for path in output_paths.values():
        canonicalize_jsonl(path)

    metadata = {
        "benchmark": "razavi-bench",
        "experiment": args.experiment,
        "run_date": args.run_date,
        "repo_commit": commit,
        "mode": "direct_multimodal_qa",
        "model_name": args.model_name,
        "provider_model": args.model,
        "api_format": args.api_format,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "reasoning": "provider_default",
        "rollouts": args.rollout,
        "concurrency": args.concurrency,
        "expected_answers": total_expected,
        "completed_answers": counters["completed"],
        "failed_answers": counters["failed"],
        "raw_responses_retained_locally": True,
    }
    (output_dir / f"{args.output_prefix}.metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False), flush=True)
    return 0 if counters["completed"] == total_expected and not counters["failed"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--api-format",
        choices=("openai_chat_completions", "anthropic_messages"),
        default="openai_chat_completions",
    )
    parser.add_argument("--api-key-env", default="RAZAVI_DIRECT_API_KEY")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-family", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-date", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--rollout", type=int, action="append", required=True)
    parser.add_argument("--task-slug", action="append")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-tokens", type=int, default=65536)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
