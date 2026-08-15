#!/usr/bin/env python3
"""Evaluate Razavi-Bench answer JSONL files with a local judge API.

Input JSONL rows must contain at least:

    {"task_path": "tasks/part1-006-device-act-as-current-source", "answer": "..."}

The script reads instruction.md, golden_solution.md, and evaluation_rubric.md
from this repository, calls an OpenAI-compatible judge API, and writes one score
record per input row.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_REPO = Path(__file__).resolve().parents[1]
DEFAULT_API_KEY_ENV = "RAZAVI_JUDGE_API_KEY"

JUDGE_SYSTEM = (
    "You are a fair analog-circuit grading judge. Grade the candidate answer "
    "against the provided rubric and golden solution. If the golden solution "
    "includes a full-credit rule, apply that rule before using general rubric "
    "preferences. If the golden solution explicitly marks a topic as secondary "
    "or not required, do not penalize mistakes in that topic unless they "
    "contradict the essential answer. If the essential answer is correct and "
    "the remaining issues are only secondary, optional, or terminology-level "
    "issues allowed by the golden solution, assign score_0_to_4 = 4. Return "
    "only valid JSON."
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict):
                raise SystemExit(f"{path}:{line_number}: each JSONL row must be an object")
            rows.append(item)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def git_commit(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def git_dirty_status(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "status", "--short"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nested_get(record: dict[str, Any], *path: str) -> Any:
    current: Any = record
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def normalize_record(record: dict[str, Any], repo: Path) -> dict[str, Any]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    task_path = (
        first_text(record, ("task_path", "task"))
        or first_text(metadata, ("task_path", "task"))
        or str(nested_get(record, "result", "metadata", "task_path") or "")
    ).strip()
    if not task_path:
        raise ValueError("missing task_path")
    task_path = task_path.strip("/")
    if task_path.startswith(str(repo)):
        task_path = str(Path(task_path).resolve().relative_to(repo))

    answer = first_text(
        record,
        (
            "answer",
            "answer_text",
            "candidate_answer",
            "final_answer",
            "answer_md",
            "output",
        ),
    )
    if not answer:
        answer = str(nested_get(record, "result", "answer") or nested_get(record, "result", "answer_preview") or "")
    if not answer.strip():
        raise ValueError("missing answer")

    task_dir = repo / task_path
    instruction_path = task_dir / "instruction.md"
    golden_path = task_dir / "golden_solution.md"
    if not instruction_path.exists():
        raise FileNotFoundError(f"missing instruction: {instruction_path}")
    if not golden_path.exists():
        raise FileNotFoundError(f"missing golden solution: {golden_path}")

    question = first_text(record, ("question", "prompt", "problem_statement"))
    if not question:
        question = str(nested_get(record, "task_definition", "problem_statement") or "")
    if not question.strip():
        question = instruction_path.read_text(encoding="utf-8")

    return {
        "source_record": record,
        "task_path": task_path,
        "task_slug": first_text(record, ("task_slug", "slug")) or Path(task_path).name,
        "question": question,
        "answer": answer,
        "instruction_path": instruction_path,
        "golden_path": golden_path,
    }


def source_key(item: dict[str, Any]) -> str:
    record = item["source_record"]
    explicit_id = first_text(record, ("id", "record_id", "source_id"))
    parts = [
        explicit_id,
        item["task_path"],
        first_text(record, ("experiment", "run_id", "run_name", "harness")),
        first_text(record, ("model_family", "answer_model_family", "model_name", "answer_model_name", "model_id")),
        str(record.get("rollout") or ""),
        first_text(record, ("session_id",)),
        sha256_text(item["answer"])[:16],
    ]
    return "|".join(parts)


def build_prompt(item: dict[str, Any], rubric: str, golden_solution: str) -> str:
    return f"""Grade this Razavi-Bench answer.

Scoring rubric:
<rubric>
{rubric}
</rubric>

Golden solution:
<golden_solution>
{golden_solution}
</golden_solution>

Question:
<question>
{item["question"]}
</question>

Candidate answer:
<candidate_answer>
{item["answer"]}
</candidate_answer>

Return exactly one JSON object in this JSON format:
{{"score_0_to_4": 3, "rationale": "concise reason for the score"}}

The score_0_to_4 value must be one integer: 0, 1, 2, 3, or 4.
Do not include markdown fences or any other text.
"""


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        try:
            parsed, _ = decoder.raw_decode(cleaned[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "score_0_to_4" in parsed:
            return parsed

    score_match = re.search(r"score[_ -]?0[_ -]?to[_ -]?4[^0-4]*([0-4])", cleaned, re.I)
    if score_match:
        return {"score_0_to_4": int(score_match.group(1)), "rationale": cleaned[:1000]}
    raise json.JSONDecodeError("No score JSON object found", cleaned, 0)


def normalize_score(parsed: dict[str, Any]) -> dict[str, Any]:
    score = int(parsed["score_0_to_4"])
    if score < 0 or score > 4:
        raise ValueError(f"score out of range: {score}")
    return {
        "score_0_to_4": score,
        "score_0_to_1": score / 4,
        "rationale": str(parsed.get("rationale", "")).strip(),
        "parse_error": "",
    }


def api_headers(api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def post_json(api_url: str, api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=api_headers(api_key),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def response_text_from_chat(body: dict[str, Any]) -> str:
    choices = body.get("choices") or []
    if choices:
        choice = choices[0] or {}
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [part.get("text", "") for part in content if isinstance(part, dict)]
            return "\n".join(text for text in texts if text)
        if isinstance(choice.get("text"), str):
            return choice["text"]
    return ""


def response_text_from_responses(body: dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    texts: list[str] = []
    for item in body.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") in {"output_text", "text"}:
                    text = content.get("text")
                    if isinstance(text, str):
                        texts.append(text)
    return "\n".join(texts)


def call_judge_once(
    *,
    api_url: str,
    api_key: str,
    api_format: str,
    model: str,
    prompt: str,
    timeout: int,
    max_tokens: int,
    temperature: float | None,
    json_mode: bool,
) -> tuple[str, dict[str, Any]]:
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    if api_format == "chat-completions":
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        body = post_json(api_url, api_key, payload, timeout)
        return response_text_from_chat(body), body

    if api_format == "responses":
        payload = {
            "model": model,
            "input": messages,
            "max_output_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if json_mode:
            payload["text"] = {"format": {"type": "json_object"}}
        body = post_json(api_url, api_key, payload, timeout)
        return response_text_from_responses(body), body

    raise ValueError(f"unknown api format: {api_format}")


def call_judge_with_retries(args: argparse.Namespace, api_key: str, prompt: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(args.max_retries):
        try:
            text, raw_body = call_judge_once(
                api_url=args.api_url,
                api_key=api_key,
                api_format=args.api_format,
                model=args.model,
                prompt=prompt,
                timeout=args.timeout,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                json_mode=args.json_mode,
            )
            result = normalize_score(extract_json_object(text))
            if args.include_raw_response:
                result["raw_response"] = raw_body
            return result
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
        ) as exc:
            last_error = exc
            time.sleep(min(2**attempt, 16))

    return {
        "score_0_to_4": None,
        "score_0_to_1": None,
        "rationale": "",
        "parse_error": f"{type(last_error).__name__}: {last_error}",
    }


def answer_metadata(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "benchmark",
        "release",
        "experiment",
        "run_date",
        "run_id",
        "run_name",
        "harness",
        "mode",
        "model_family",
        "model_name",
        "model_id",
        "answer_model_family",
        "answer_model_name",
        "rollout",
        "session_id",
        "task_id",
        "record_id",
        "id",
    )
    return {key: record[key] for key in keys if key in record and record[key] is not None}


def build_score_record(
    *,
    item: dict[str, Any],
    judge_result: dict[str, Any],
    judge_model: str,
    judge_api_format: str,
    repo_commit: str,
    rubric_hash: str,
    golden_hash: str,
    judge_script_hash: str,
) -> dict[str, Any]:
    record = item["source_record"]
    out = {
        "source_key": source_key(item),
        "task_slug": item["task_slug"],
        "task_path": item["task_path"],
        "repo_commit": repo_commit,
        "rubric_sha256": rubric_hash,
        "golden_solution_sha256": golden_hash,
        "question_sha256": sha256_text(item["question"]),
        "answer_sha256": sha256_text(item["answer"]),
        "answer_chars": len(item["answer"]),
        "judge_model": judge_model,
        "judge_api_format": judge_api_format,
        "judge_script_sha256": judge_script_hash,
        "judge_system_sha256": sha256_text(JUDGE_SYSTEM),
        "score_0_to_4": judge_result["score_0_to_4"],
        "score_0_to_1": judge_result["score_0_to_1"],
        "rationale": judge_result["rationale"],
        "parse_error": judge_result["parse_error"],
        "answer_metadata": answer_metadata(record),
    }
    if "raw_response" in judge_result:
        out["raw_response"] = judge_result["raw_response"]
    return out


def load_api_key(args: argparse.Namespace) -> str:
    if args.no_auth:
        return ""
    if args.api_key_file:
        return Path(args.api_key_file).read_text(encoding="utf-8").strip()
    value = os.environ.get(args.api_key_env)
    if value:
        return value.strip()
    raise SystemExit(
        f"Missing API key. Set {args.api_key_env}, pass --api-key-file, or use --no-auth."
    )


def matches_filters(item: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.task_slug and item["task_slug"] not in set(args.task_slug):
        return False
    if args.task_path and item["task_path"] not in set(path.strip("/") for path in args.task_path):
        return False
    return True


async def run(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    rubric_path = repo / "evaluation_rubric.md"
    if not rubric_path.exists():
        raise SystemExit(f"missing rubric: {rubric_path}")
    if not args.api_url:
        raise SystemExit("--api-url is required, or set RAZAVI_JUDGE_API_URL")
    if not args.model:
        raise SystemExit("--model is required, or set RAZAVI_JUDGE_MODEL")

    api_key = load_api_key(args)
    rubric = rubric_path.read_text(encoding="utf-8")
    rubric_hash = sha256_text(rubric)
    repo_commit = git_commit(repo)
    repo_dirty = git_dirty_status(repo)
    judge_script = Path(__file__).resolve()
    judge_script_hash = sha256_file(judge_script)

    items: list[dict[str, Any]] = []
    for line_number, record in enumerate(load_jsonl(input_path), 1):
        try:
            item = normalize_record(record, repo)
        except Exception as exc:
            raise SystemExit(f"{input_path}:{line_number}: {type(exc).__name__}: {exc}") from exc
        if matches_filters(item, args):
            items.append(item)
    if args.limit:
        items = items[: args.limit]
    if not items:
        raise SystemExit("No input records matched the requested filters")

    rows = [
        row for row in load_jsonl(output_path)
        if not row.get("parse_error")
    ] if args.resume and output_path.exists() else []
    done = {row.get("source_key") for row in rows if not row.get("parse_error")}
    pending = [item for item in items if source_key(item) not in done]

    print(f"records={len(items)} pending={len(pending)} output={output_path}", flush=True)
    sem = asyncio.Semaphore(args.concurrency)
    lock = asyncio.Lock()
    completed = 0

    async def score_one(item: dict[str, Any]) -> None:
        nonlocal completed
        golden = item["golden_path"].read_text(encoding="utf-8")
        prompt = build_prompt(item, rubric, golden)
        async with sem:
            result = await asyncio.to_thread(call_judge_with_retries, args, api_key, prompt)
        row = build_score_record(
            item=item,
            judge_result=result,
            judge_model=args.model,
            judge_api_format=args.api_format,
            repo_commit=repo_commit,
            rubric_hash=rubric_hash,
            golden_hash=sha256_text(golden),
            judge_script_hash=judge_script_hash,
        )
        async with lock:
            rows.append(row)
            completed += 1
            if completed % args.flush_every == 0:
                write_jsonl(output_path, rows)
            if completed % args.progress_every == 0 or completed == len(pending):
                print(f"{completed}/{len(pending)} scored; rows={len(rows)}", flush=True)

    await asyncio.gather(*(score_one(item) for item in pending))
    rows.sort(key=lambda row: (row.get("task_path", ""), row.get("source_key", "")))
    write_jsonl(output_path, rows)

    scored = [row for row in rows if row.get("score_0_to_4") is not None]
    if scored:
        mean = sum(float(row["score_0_to_4"]) for row in scored) / len(scored)
        print(f"scored={len(scored)} mean_score_0_to_4={mean:.3f}", flush=True)
    failures = [row for row in rows if row.get("parse_error")]
    if failures:
        print(f"parse_or_call_failures={len(failures)}", flush=True)
    metadata_path = Path(args.metadata_output).resolve() if args.metadata_output else output_path.with_suffix(output_path.suffix + ".metadata.json")
    metadata = {
        "input": str(input_path),
        "output": str(output_path),
        "record_count": len(items),
        "scored_count": len(scored),
        "failure_count": len(failures),
        "repo": str(repo),
        "repo_commit": repo_commit,
        "repo_dirty": repo_dirty,
        "rubric_sha256": rubric_hash,
        "judge_script": str(judge_script),
        "judge_script_sha256": judge_script_hash,
        "judge_system_sha256": sha256_text(JUDGE_SYSTEM),
        "judge_api_url": args.api_url,
        "judge_api_format": args.api_format,
        "judge_model": args.model,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "json_mode": args.json_mode,
        "max_retries": args.max_retries,
        "timeout": args.timeout,
        "concurrency": args.concurrency,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(metadata_path)
    print(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--input", required=True, help="Answer JSONL path")
    parser.add_argument("--output", required=True, help="Score JSONL path")
    parser.add_argument("--metadata-output", help="Judge run metadata JSON path")
    parser.add_argument("--api-url", default=os.environ.get("RAZAVI_JUDGE_API_URL", ""))
    parser.add_argument(
        "--api-format",
        default=os.environ.get("RAZAVI_JUDGE_API_FORMAT", "chat-completions"),
        choices=["chat-completions", "responses"],
    )
    parser.add_argument("--model", default=os.environ.get("RAZAVI_JUDGE_MODEL", ""))
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--api-key-file")
    parser.add_argument("--no-auth", action="store_true")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--json-mode", action="store_true")
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--flush-every", type=int, default=10)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--task-slug", action="append")
    parser.add_argument("--task-path", action="append")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--include-raw-response", action="store_true")
    return parser.parse_args()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
