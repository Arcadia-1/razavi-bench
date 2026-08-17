#!/usr/bin/env python3
"""Run visual-extraction or reviewed-visual-facts reasoning ablations."""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import hashlib
import io
import json
import mimetypes
import os
import random
import re
import subprocess
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TOOLS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_ROOT.parent
VISUAL_FACTS_PATH = REPO_ROOT / "data" / "visual_facts.jsonl"
TRACK_VISUAL = "visual-extraction"
TRACK_REASONING = "netlist-and-visual-annotations-circuit-reasoning"
VISUAL_EXTRACTION_PROMPT = """请阅读这张原理图，并按以下要求输出：
1. 强制输出 CDL/SPICE 标准格式的连接记录；MOS 管端口顺序统一为 D G S B，地节点统一写为 0。
2. 强制使用自然语言描述图片中的器件和连接关系，描述格式不限。
3. 你可以自行决定是否补充 CDL 无法表达的视觉事实或其他结构化记录，格式不限。对于不确定或根据惯例推断的信息，必须明确说明。如果图片包含多个子图，请分别描述。"""
FIGURES_SECTION = re.compile(r"\n## Figures\s*\n.*\Z", re.DOTALL)
TOPOLOGY_TOKEN_COUNTS = {
    "B": 3,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 4,
    "G": 5,
    "H": 4,
    "I": 3,
    "K": 3,
    "L": 3,
    "M": 6,
    "R": 3,
    "S": 6,
    "T": 5,
    "V": 3,
    "W": 5,
}


class ApiError(RuntimeError):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status


@dataclass(frozen=True)
class Job:
    rollout: int
    item_id: str
    input_text: str
    source_figure_path: Path | None
    source_figure_sha256: str | None
    crop_box: tuple[int, int, int, int] | None
    task_path: str | None
    visual_unit_ids: tuple[str, ...]
    netlist_paths: tuple[str, ...]
    input_type: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def load_visual_facts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with VISUAL_FACTS_PATH.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise SystemExit(
                    f"{VISUAL_FACTS_PATH}:{line_number}: row must be an object"
                )
            rows.append(row)
    if len(rows) != 41:
        raise SystemExit(f"expected 41 visual units, found {len(rows)}")
    return rows


def cropped_png(path: Path, crop_box: tuple[int, int, int, int]) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required for visual-extraction mode; install it with "
            "`python -m pip install Pillow`."
        ) from exc

    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError(f"source figure is not a PNG: {path}")
        full_box = (0, 0, image.width, image.height)
        if crop_box == full_box:
            return path.read_bytes()
        buffer = io.BytesIO()
        image.crop(crop_box).save(buffer, format="PNG")
        return buffer.getvalue()


def image_content(
    path: Path, crop_box: tuple[int, int, int, int]
) -> dict[str, Any]:
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(cropped_png(path, crop_box)).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{encoded}"},
    }


def netlist_topology_view(path: Path) -> str:
    """Derive terminals from canonical decks without comments or assumptions."""
    kept: list[str] = []
    in_control = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue
        lower = line.lower()
        if lower.startswith(".control"):
            in_control = True
            continue
        if in_control:
            if lower.startswith(".endc"):
                in_control = False
            continue
        if line.startswith("+"):
            continue
        if line.startswith("."):
            directive = lower.split(maxsplit=1)[0]
            if directive in {".subckt", ".ends"}:
                tokens = line.split()
                if directive == ".subckt":
                    tokens = [
                        token
                        for token in tokens
                        if token.lower() != "params:" and "=" not in token
                    ]
                kept.append(" ".join(tokens))
            continue
        tokens = line.split()
        prefix = tokens[0][0].upper()
        if prefix == "X":
            tokens = [token for token in tokens if "=" not in token]
        elif prefix in TOPOLOGY_TOKEN_COUNTS:
            tokens = tokens[: TOPOLOGY_TOKEN_COUNTS[prefix]]
        else:
            tokens = [token for token in tokens if "=" not in token]
        kept.append(" ".join(tokens))
        keep_continuation = True
    if not kept:
        raise ValueError(f"no circuit statements found in executable netlist: {path}")
    return "\n".join(kept)


def response_text(body: dict[str, Any]) -> tuple[str, str]:
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


def redact_secret(value: Any, secret: str) -> Any:
    """Remove a request credential even if an endpoint unexpectedly echoes it."""
    if isinstance(value, str):
        return value.replace(secret, "<redacted>") if secret else value
    if isinstance(value, list):
        return [redact_secret(item, secret) for item in value]
    if isinstance(value, dict):
        return {key: redact_secret(item, secret) for key, item in value.items()}
    return value


def post_json(
    url: str, api_key: str, payload: dict[str, Any], timeout: int
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise ApiError(exc.code, detail) from exc
    if not isinstance(result, dict):
        raise ValueError("API response must be a JSON object")
    return result


def transient_error(exc: Exception) -> bool:
    if isinstance(exc, ApiError):
        return exc.status in {408, 409, 425, 429} or 500 <= exc.status <= 599
    return isinstance(exc, (TimeoutError, urllib.error.URLError))


def fact_block(row: dict[str, Any], facts_language: str) -> str:
    annotation_en = str(row["visual_annotation_en"]).strip()
    annotation_zh = str(row["visual_annotation_zh"]).strip()
    heading = f"### {row['figure_label']} [{row['visual_unit_id']}]"
    topology_sources: dict[str, list[str]] = {}
    for raw_path in row["netlist_paths"]:
        relative_path = str(raw_path)
        topology = netlist_topology_view(REPO_ROOT / relative_path)
        topology_sources.setdefault(topology, []).append(relative_path)
    netlists = []
    for topology, source_paths in topology_sources.items():
        sources = "\n".join(f"- `{path}`" for path in source_paths)
        netlists.append(
            f"#### Source executable netlist(s)\n\n{sources}\n\n"
            f"```spice\n{topology}\n```"
        )
    topology_block = "\n\n".join(netlists)
    if facts_language == "en":
        annotation = annotation_en or "(No additional visual-only annotation.)"
        visual_block = f"Visual-only annotation:\n\n{annotation}"
    elif facts_language == "zh":
        annotation = annotation_zh or "（无额外纯视觉注释。）"
        visual_block = f"纯视觉注释：\n\n{annotation}"
    else:
        annotation_en = annotation_en or "(No additional visual-only annotation.)"
        annotation_zh = annotation_zh or "（无额外纯视觉注释。）"
        visual_block = (
            f"Visual-only annotation (English):\n\n{annotation_en}\n\n"
            f"纯视觉注释（中文）：\n\n{annotation_zh}"
        )
    return (
        f"{heading}\n\n"
        "Existing executable netlist topology (comments, values, parameters, and "
        "analysis commands omitted):"
        f"\n\n{topology_block}\n\n{visual_block}"
    )


def reasoning_input(
    instruction: str, rows: list[dict[str, Any]], facts_language: str
) -> str:
    question = FIGURES_SECTION.sub("", instruction).rstrip()
    if not rows:
        return question
    facts = "\n\n".join(fact_block(row, facts_language) for row in rows)
    return (
        f"{question}\n\n"
        "## Existing netlist topology and reviewed visual-only annotations\n\n"
        f"{facts}"
    )


def build_jobs(
    mode: str,
    rows: list[dict[str, Any]],
    rollouts: list[int],
    facts_language: str = "en",
) -> list[Job]:
    jobs: list[Job] = []
    if mode == TRACK_VISUAL:
        for rollout in rollouts:
            for row in rows:
                source_figure_path = REPO_ROOT / str(row["source_figure_path"])
                if not source_figure_path.is_file():
                    raise SystemExit(f"missing source figure: {source_figure_path}")
                crop_box = tuple(int(value) for value in row["crop_box"])
                if len(crop_box) != 4:
                    raise SystemExit(
                        f"invalid crop_box for {row['visual_unit_id']}: {crop_box}"
                    )
                jobs.append(
                    Job(
                        rollout=rollout,
                        item_id=str(row["visual_unit_id"]),
                        input_text=VISUAL_EXTRACTION_PROMPT,
                        source_figure_path=source_figure_path,
                        source_figure_sha256=str(row["source_figure_sha256"]),
                        crop_box=crop_box,
                        task_path=None,
                        visual_unit_ids=(str(row["visual_unit_id"]),),
                        netlist_paths=tuple(str(path) for path in row["netlist_paths"]),
                        input_type="single-visual-unit-image",
                    )
                )
        return jobs

    rows_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for mapping in row["task_mappings"]:
            rows_by_task[str(mapping["task_path"])].append(row)
    task_dirs = sorted(path for path in (REPO_ROOT / "tasks").iterdir() if path.is_dir())
    if len(task_dirs) != 50:
        raise SystemExit(f"expected 50 tasks, found {len(task_dirs)}")
    for task_dir in task_dirs:
        task_path = task_dir.relative_to(REPO_ROOT).as_posix()
        mapped_rows = sorted(
            rows_by_task.get(task_path, []), key=lambda row: str(row["visual_unit_id"])
        )
        has_figure = any(task_dir.glob("*.png"))
        if has_figure != bool(mapped_rows):
            raise SystemExit(
                f"reviewed-fact mapping mismatch for {task_path}: "
                f"has_figure={has_figure} mapped_units={len(mapped_rows)}"
            )
        instruction = (task_dir / "instruction.md").read_text(encoding="utf-8")
        input_text = reasoning_input(instruction, mapped_rows, facts_language)
        netlist_paths = tuple(
            sorted(
                {
                    str(path)
                    for row in mapped_rows
                    for path in row["netlist_paths"]
                }
            )
        )
        for rollout in rollouts:
            jobs.append(
                Job(
                    rollout=rollout,
                    item_id=task_dir.name,
                    input_text=input_text,
                    source_figure_path=None,
                    source_figure_sha256=None,
                    crop_box=None,
                    task_path=task_path,
                    visual_unit_ids=tuple(
                        str(row["visual_unit_id"]) for row in mapped_rows
                    ),
                    netlist_paths=netlist_paths,
                    input_type=(
                        "existing-netlist-topology-with-visual-annotations"
                        if mapped_rows
                        else "text-only-control"
                    ),
                )
            )
    return jobs


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned or "model"


def load_completed(
    paths: list[Path], track: str, model: str, facts_language: str | None
) -> set[tuple[int, str]]:
    completed: set[tuple[int, str]] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                expected = {
                    "track": track,
                    "provider_model": model,
                    "facts_language": facts_language,
                }
                mismatches = {
                    key: (row.get(key), value)
                    for key, value in expected.items()
                    if row.get(key) != value
                }
                if mismatches:
                    raise SystemExit(
                        f"resume configuration mismatch in {path}: {mismatches}"
                    )
                if str(row.get("answer") or "").strip():
                    completed.add((int(row["rollout"]), str(row["item_id"])))
    return completed


def canonicalize_jsonl(path: Path) -> None:
    if not path.exists():
        return
    rows_by_item: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                row = json.loads(line)
                rows_by_item[str(row["item_id"])] = row
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for item_id in sorted(rows_by_item):
            file.write(
                json.dumps(rows_by_item[item_id], ensure_ascii=False, sort_keys=True)
                + "\n"
            )


def payload_for(job: Job, args: argparse.Namespace) -> dict[str, Any]:
    if job.source_figure_path is None or job.crop_box is None:
        content: str | list[dict[str, Any]] = job.input_text
    else:
        content = [
            image_content(job.source_figure_path, job.crop_box),
            {"type": "text", "text": job.input_text},
        ]
    return {
        "model": args.model,
        "messages": [{"role": "user", "content": content}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "stream": False,
    }


async def main_async(args: argparse.Namespace) -> int:
    mode = TRACK_VISUAL if args.mode == "visual-extraction" else TRACK_REASONING
    rollouts = sorted(set(args.rollout or [1]))
    if any(rollout < 1 for rollout in rollouts):
        raise SystemExit("rollout numbers must be positive")
    if min(args.concurrency, args.attempts, args.timeout, args.max_tokens) < 1:
        raise SystemExit("concurrency, attempts, timeout, and max-tokens must be positive")

    rows = load_visual_facts()
    jobs = build_jobs(mode, rows, rollouts, args.facts_language)
    items_per_rollout = len(jobs) // len(rollouts)
    figure_jobs = sum(
        job.input_type == "existing-netlist-topology-with-visual-annotations"
        for job in jobs
    )
    text_jobs = sum(job.input_type == "text-only-control" for job in jobs)
    print(
        f"track={mode} rollouts={rollouts} items_per_rollout={items_per_rollout} "
        f"total={len(jobs)} figure_inputs={figure_jobs} text_controls={text_jobs} "
        f"facts_language={args.facts_language if mode == TRACK_REASONING else 'n/a'}",
        flush=True,
    )
    if args.dry_run:
        sample = next(
            (job for job in jobs if job.input_type != "text-only-control"), jobs[0]
        )
        payload_for(sample, args)
        print(
            f"DRY-RUN sample={sample.item_id} input_type={sample.input_type} "
            f"images={int(sample.source_figure_path is not None)} "
            f"visual_units={len(sample.visual_unit_ids)} input_chars={len(sample.input_text)}",
            flush=True,
        )
        return 0

    if not args.base_url:
        raise SystemExit("--base-url is required unless --dry-run is used")
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        raise SystemExit(f"missing API key environment variable: {args.api_key_env}")

    run_variant = (
        mode if mode == TRACK_VISUAL else f"{mode}-{args.facts_language}"
    )
    output_dir = args.output_dir.resolve() if args.output_dir else (
        REPO_ROOT
        / "WORK"
        / "visual-ablation"
        / f"{run_variant}-{safe_name(args.model)}"
    )
    raw_dir = args.raw_dir.resolve() if args.raw_dir else output_dir / "raw"
    prefix = args.output_prefix or f"{run_variant}-{safe_name(args.model)}"
    output_paths = {
        rollout: output_dir / f"{prefix}-rollout-{rollout}.jsonl"
        for rollout in rollouts
    }
    metadata_path = output_dir / f"{prefix}.metadata.json"
    failures_path = output_dir / f"{prefix}.failures.jsonl"
    if not args.resume:
        existing = [
            path
            for path in [*output_paths.values(), metadata_path, failures_path]
            if path.exists()
        ]
        if existing:
            joined = ", ".join(str(path) for path in existing)
            raise SystemExit(f"output already exists; use --resume or a new path: {joined}")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    completed = (
        load_completed(
            list(output_paths.values()),
            mode,
            args.model,
            args.facts_language if mode == TRACK_REASONING else None,
        )
        if args.resume
        else set()
    )
    pending = [job for job in jobs if (job.rollout, job.item_id) not in completed]
    print(
        f"model={args.model} completed={len(completed)} pending={len(pending)} "
        f"concurrency={args.concurrency}",
        flush=True,
    )

    semaphore = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    counters = {"completed": len(completed), "failed": 0}
    api_url = args.base_url.rstrip("/") + "/chat/completions"
    commit = git_commit()

    async def run_one(job: Job) -> None:
        payload = payload_for(job, args)
        final_error = ""
        for attempt in range(1, args.attempts + 1):
            started = time.monotonic()
            try:
                async with semaphore:
                    body = await asyncio.to_thread(
                        post_json, api_url, api_key, payload, args.timeout
                    )
                body = redact_secret(body, api_key)
                elapsed = round(time.monotonic() - started, 3)
                answer, finish_reason = response_text(body)
                if not answer.strip():
                    raise ValueError("empty model response")

                raw_path = raw_dir / f"rollout-{job.rollout}" / f"{job.item_id}.json"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_record = {
                    "attempt": attempt,
                    "elapsed_seconds": elapsed,
                    "facts_language": (
                        args.facts_language if mode == TRACK_REASONING else None
                    ),
                    "input_type": job.input_type,
                    "item_id": job.item_id,
                    "model": args.model,
                    "response": body,
                    "rollout": job.rollout,
                    "track": mode,
                    "visual_unit_ids": list(job.visual_unit_ids),
                    "netlist_paths": list(job.netlist_paths),
                }
                raw_path.write_text(
                    json.dumps(raw_record, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )

                record: dict[str, Any] = {
                    "answer": answer,
                    "benchmark": "razavi-bench",
                    "experiment": args.experiment or mode,
                    "facts_language": (
                        args.facts_language if mode == TRACK_REASONING else None
                    ),
                    "finish_reason": finish_reason,
                    "input": job.input_text,
                    "input_type": job.input_type,
                    "item_id": job.item_id,
                    "model_call_attempts": attempt,
                    "model_family": args.model_family or args.model,
                    "model_name": args.model_name or args.model,
                    "provider_model": args.model,
                    "release": commit,
                    "rollout": job.rollout,
                    "run_date": args.run_date,
                    "task_path": job.task_path,
                    "track": mode,
                    "visual_unit_ids": list(job.visual_unit_ids),
                    "netlist_paths": list(job.netlist_paths),
                }
                if job.source_figure_path is not None and job.crop_box is not None:
                    record["source_figure"] = {
                        "path": job.source_figure_path.relative_to(REPO_ROOT).as_posix(),
                        "sha256": job.source_figure_sha256,
                        "crop_box": list(job.crop_box),
                    }
                async with write_lock:
                    with output_paths[job.rollout].open(
                        "a", encoding="utf-8", newline="\n"
                    ) as file:
                        file.write(
                            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                        )
                    counters["completed"] += 1
                    print(
                        f"OK {counters['completed']}/{len(jobs)} r{job.rollout} "
                        f"{job.item_id} chars={len(answer)} finish={finish_reason} "
                        f"elapsed={elapsed}s attempts={attempt}",
                        flush=True,
                    )
                return
            except Exception as exc:
                elapsed = round(time.monotonic() - started, 3)
                final_error = str(
                    redact_secret(f"{type(exc).__name__}: {exc}", api_key)
                )
                can_retry = transient_error(exc) and attempt < args.attempts
                print(
                    f"{'RETRY' if can_retry else 'ERROR'} r{job.rollout} {job.item_id} "
                    f"attempt={attempt} elapsed={elapsed}s error={final_error[:300]}",
                    flush=True,
                )
                if can_retry:
                    await asyncio.sleep(min(60, 2**attempt + random.random() * 2))
                    continue
                break

        failure = {
            "error": final_error,
            "input_type": job.input_type,
            "item_id": job.item_id,
            "rollout": job.rollout,
            "track": mode,
        }
        async with write_lock:
            with failures_path.open("a", encoding="utf-8", newline="\n") as file:
                file.write(json.dumps(failure, ensure_ascii=False, sort_keys=True) + "\n")
            counters["failed"] += 1

    await asyncio.gather(*(run_one(job) for job in pending))
    for path in output_paths.values():
        canonicalize_jsonl(path)

    metadata = {
        "api_format": "openai_chat_completions",
        "benchmark": "razavi-bench",
        "completed_answers": counters["completed"],
        "concurrency": args.concurrency,
        "expected_answers": len(jobs),
        "experiment": args.experiment or mode,
        "failed_answers": counters["failed"],
        "facts_language": args.facts_language if mode == TRACK_REASONING else None,
        "input_contract": (
            "one_visual_unit_image_without_question_or_reference_facts"
            if mode == TRACK_VISUAL
            else (
                "canonical_netlist_topology_views_plus_visual_only_annotations_"
                "without_images_or_golden_solutions"
            )
        ),
        "max_tokens": args.max_tokens,
        "model_name": args.model_name or args.model,
        "provider_model": args.model,
        "raw_responses_retained_locally": True,
        "visual_facts_sha256": sha256_file(VISUAL_FACTS_PATH),
        "repo_commit": commit,
        "rollouts": rollouts,
        "run_date": args.run_date,
        "temperature": args.temperature,
        "track": mode,
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(metadata, ensure_ascii=False), flush=True)
    return 0 if counters["completed"] == len(jobs) and not counters["failed"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=["visual-extraction", "circuit-reasoning"]
    )
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env", default="RAZAVI_VISUAL_ABLATION_API_KEY")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-name")
    parser.add_argument("--model-family")
    parser.add_argument("--experiment")
    parser.add_argument("--run-date", default=dt.date.today().isoformat())
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--output-prefix")
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--rollout", type=int, action="append")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-tokens", type=int, default=65536)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument(
        "--facts-language", choices=["en", "zh", "bilingual"], default="en"
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
