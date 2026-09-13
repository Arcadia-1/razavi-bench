import argparse
import asyncio
import getpass
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable


EXPERIMENT = "2026-06-26-direct-qa"
DEFAULT_REPO = Path(__file__).resolve().parents[3]
MODEL_OUTPUT_PATTERN = "*-rollout-*.jsonl"

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


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def score_key(row: dict) -> tuple[str, int, str]:
    return (row["answer_model_family"], int(row["rollout"]), row["task_slug"])


def source_key(row: dict) -> tuple[str, int, str]:
    return (row["model_family"], int(row["rollout"]), row["task_slug"])


def is_success(row: dict) -> bool:
    return row.get("score_0_to_4") is not None and not row.get("parse_error")


def existing_success_rows(path: Path) -> list[dict]:
    return [row for row in load_jsonl(path) if is_success(row)]


def build_prompt(record: dict, rubric: str, golden_solution: str) -> str:
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
{record["question"]}
</question>

Candidate answer:
<candidate_answer>
{record["answer"]}
</candidate_answer>

Return exactly one JSON object in this JSON format:
{{"score_0_to_4": 3, "rationale": "concise reason for the score"}}

The score_0_to_4 value must be one integer: 0, 1, 2, 3, or 4.
Do not include markdown fences or any other text.
"""


def extract_json_object(text: str) -> dict:
    cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
    try:
        return json.loads(cleaned)
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
        return {
            "score_0_to_4": int(score_match.group(1)),
            "rationale": cleaned[:500],
        }
    raise json.JSONDecodeError("No score JSON object found", cleaned, 0)


def post_chat(api_key: str, api_url: str, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_score_response(parsed: dict) -> dict:
    score = int(parsed["score_0_to_4"])
    if score < 0 or score > 4:
        raise ValueError(f"score out of range: {score}")
    return {
        "score_0_to_4": score,
        "score_0_to_1": score / 4,
        "rationale": str(parsed.get("rationale", "")).strip(),
        "parse_error": "",
    }


def call_with_retries(
    chat_fn: Callable[[str, str, list[dict], int], str],
    api_key: str,
    model: str,
    prompt: str,
    timeout: int,
    max_retries: int,
) -> dict:
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    last_error = None
    for attempt in range(max_retries):
        try:
            content = chat_fn(api_key, model, messages, timeout)
            return normalize_score_response(extract_json_object(content))
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


def build_score_record(
    source_record: dict,
    judge_model: str,
    judge_run_date: str,
    rubric_hash: str,
    golden_hash: str,
    result: dict,
) -> dict:
    return {
        "experiment": EXPERIMENT,
        "judge_run_date": judge_run_date,
        "judge_model": judge_model,
        "rubric_sha256": rubric_hash,
        "golden_solution_sha256": golden_hash,
        "benchmark": source_record["benchmark"],
        "release": source_record["release"],
        "run_date": source_record["run_date"],
        "task_slug": source_record["task_slug"],
        "task_path": source_record["task_path"],
        "answer_model_family": source_record["model_family"],
        "answer_model_name": source_record["model_name"],
        "rollout": source_record["rollout"],
        "score_0_to_4": result["score_0_to_4"],
        "score_0_to_1": result["score_0_to_1"],
        "rationale": result["rationale"],
        "parse_error": result["parse_error"],
    }


def matches_record_filters(record: dict, args: argparse.Namespace) -> bool:
    if args.task_slug and record["task_slug"] not in set(args.task_slug):
        return False
    if args.model_family and record["model_family"] not in set(args.model_family):
        return False
    if args.rollout and int(record["rollout"]) not in set(args.rollout):
        return False
    return True


def load_source_records(experiment_dir: Path, args: argparse.Namespace) -> list[dict]:
    records = []
    model_output_dir = experiment_dir / "model_outputs"
    for path in sorted(model_output_dir.glob(MODEL_OUTPUT_PATTERN)):
        records.extend(load_jsonl(path))
    records = [record for record in records if matches_record_filters(record, args)]
    return records[: args.limit] if args.limit else records


def has_record_filter(args: argparse.Namespace) -> bool:
    return bool(args.task_slug or args.model_family or args.rollout or args.limit)


async def run_judge(args: argparse.Namespace, chat_fn: Callable[[str, str, list[dict], int], str], api_env: str) -> None:
    repo = Path(args.repo).resolve()
    experiment_dir = repo / "experiments" / EXPERIMENT
    output_dir = experiment_dir / "judge_outputs"
    rubric = (repo / "evaluation_rubric.md").read_text(encoding="utf-8")
    rubric_hash = sha256_text(rubric)
    api_key = os.environ.get(api_env) or getpass.getpass(f"{api_env}: ")
    if not api_key.strip():
        raise SystemExit(f"{api_env} is required")

    source_records = load_source_records(experiment_dir, args)
    if not source_records:
        raise SystemExit("No source records matched the requested filters")
    output_path = output_dir / f"{args.output_name}.jsonl"
    if args.refresh_matched and not has_record_filter(args):
        raise SystemExit("--refresh-matched requires at least one task/model/rollout/limit filter")

    rows = existing_success_rows(output_path) if (args.resume or args.refresh_matched) else []
    source_keys = {source_key(record) for record in source_records}
    if args.refresh_matched:
        before_count = len(rows)
        rows = [row for row in rows if score_key(row) not in source_keys]
        removed_count = before_count - len(rows)
        pending_records = source_records
        print(f"refreshing {len(pending_records)} matched records; removed {removed_count} existing rows", flush=True)
    else:
        done = {score_key(row) for row in rows}
        pending_records = [record for record in source_records if source_key(record) not in done]

    sem = asyncio.Semaphore(args.concurrency)
    rows_lock = asyncio.Lock()
    pending_total = len(pending_records)
    completed = 0

    async def score_one(record: dict) -> None:
        nonlocal completed
        golden_path = repo / record["task_path"] / "golden_solution.md"
        golden = golden_path.read_text(encoding="utf-8")
        prompt = build_prompt(record, rubric, golden)
        async with sem:
            result = await asyncio.to_thread(
                call_with_retries,
                chat_fn,
                api_key,
                args.model,
                prompt,
                args.timeout,
                args.max_retries,
            )
        score_record = build_score_record(
            record,
            args.model,
            args.judge_run_date,
            rubric_hash,
            sha256_text(golden),
            result,
        )
        async with rows_lock:
            rows.append(score_record)
            completed += 1
            if completed % args.flush_every == 0:
                write_jsonl(output_path, rows)
            if completed % args.progress_every == 0 or completed == pending_total:
                print(f"{completed}/{pending_total} scored; rows={len(rows)}", flush=True)

    await asyncio.gather(*(score_one(record) for record in pending_records))
    rows.sort(key=lambda row: (
        row["answer_model_family"],
        int(row["rollout"]),
        row["task_slug"],
    ))
    write_jsonl(output_path, rows)
    print(output_path)
    print(f"rows={len(rows)}")


def add_common_args(
    parser: argparse.ArgumentParser,
    default_model: str,
    default_output_name: str,
    default_max_tokens: int,
) -> None:
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--model", default=default_model)
    parser.add_argument("--output-name", default=default_output_name)
    parser.add_argument("--judge-run-date", default="2026-06-30")
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-tokens", type=int, default=default_max_tokens)
    parser.add_argument("--flush-every", type=int, default=25)
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--task-slug",
        action="append",
        help="Score only this task slug. May be repeated.",
    )
    parser.add_argument(
        "--model-family",
        action="append",
        help="Score only this answer model family, such as gpt, gemini, or claude. May be repeated.",
    )
    parser.add_argument(
        "--rollout",
        action="append",
        type=int,
        help="Score only this rollout number. May be repeated.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--refresh-matched",
        action="store_true",
        help=(
            "Load the existing output JSONL, remove rows selected by the current "
            "filters, re-score those rows, and write the merged JSONL back."
        ),
    )
