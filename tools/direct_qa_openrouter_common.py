"""Small shared helpers for the public Direct-QA runner."""

from __future__ import annotations

import base64
import json
import mimetypes
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://openrouter.ai/api"
DEFAULT_SMOKE_TASKS = (
    "part1-001-double-length-and-width-mosfet-its-intrinsic",
    "part1-004-sketch-ix-versus-vx",
)
_SECRET_RE = re.compile(r"(?:sk-[A-Za-z0-9_-]{8,}|Bearer\s+\S+)", re.IGNORECASE)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def redact(value: Any) -> str:
    return _SECRET_RE.sub("<redacted>", str(value or ""))[:500]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def load_tasks(repo_root: Path, slugs: list[str] | None = None) -> list[dict[str, Any]]:
    rows = read_jsonl(repo_root / "data/tasks.jsonl")
    by_slug = {row["task_slug"]: row for row in rows}
    if not slugs:
        return rows
    missing = sorted(set(slugs) - set(by_slug))
    if missing:
        raise ValueError(f"unknown task slug(s): {', '.join(missing)}")
    return [by_slug[slug] for slug in sorted(set(slugs))]


def build_content(repo_root: Path, task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    content = [{"type": "text", "text": task["instruction"]}]
    figures: list[str] = []
    for relative in task.get("figures") or []:
        path = repo_root / relative
        media_type = mimetypes.guess_type(path.name)[0] or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{encoded}"}})
        figures.append(relative)
    return content, figures


def endpoint(base_url: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/chat/completions" if base.endswith("/v1") else f"{base}/v1/chat/completions"


def payload(model: str, content: list[dict[str, Any]], effort: str, max_tokens: int) -> dict[str, Any]:
    value: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "stream": False,
    }
    if effort != "default":
        value["reasoning"] = {"effort": effort}
    return value


def model_reasoning(base_url: str, model: str, timeout: int = 30) -> dict[str, Any] | None:
    """Return the model's `reasoning` object from OpenRouter's public model list.

    None means the model exposes no effort selection. Raises if the model is not listed.
    """
    base = base_url.rstrip("/")
    url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        models = json.loads(response.read().decode())["data"]
    for entry in models:
        if entry.get("id") == model:
            return entry.get("reasoning")
    raise ValueError(f"{model} is not in {url}; check the model id or pass --skip-effort-check")


def resolve_effort(requested: str, reasoning: dict[str, Any] | None) -> tuple[str, str | None]:
    """Check a requested effort against the efforts the model lists, highest first.

    OpenRouter silently maps an unsupported effort to the nearest supported one, so an
    unsupported request is an error here. "top" picks the highest listed effort; a lower
    effort is allowed (some models are evaluated at several) but returns a notice.
    """
    supported = (reasoning or {}).get("supported_efforts")
    if requested == "default":
        return requested, "using the provider's default effort"
    if reasoning is None:
        raise ValueError(f"effort {requested!r} requested, but the model does not expose effort selection; use --effort default")
    if not supported:
        if requested == "top":
            raise ValueError("the model accepts every effort without listing them; pass one explicitly")
        return requested, None
    if requested == "top":
        return supported[0], None
    if requested not in supported:
        raise ValueError(f"effort {requested!r} is not supported; the model lists {', '.join(supported)} (highest first)")
    if requested != supported[0]:
        return requested, f"effort {requested!r} is below the model's highest effort {supported[0]!r}"
    return requested, None


def response_text(body: dict[str, Any]) -> tuple[str, str]:
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content, str(choice.get("finish_reason") or "")
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict)), str(choice.get("finish_reason") or "")
    return "", str(choice.get("finish_reason") or "")


def post_json(url: str, key: str, body: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "HTTP-Referer": "https://razavi-bench.tokenzhang.com", "X-Title": "Razavi-Bench Direct QA"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def call_model(url: str, key: str, body: dict[str, Any], timeout: int, retries: int) -> dict[str, Any]:
    attempts = []
    for attempt in range(1, retries + 1):
        try:
            response = post_json(url, key, body, timeout)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            attempts.append({"attempt": attempt, "error": redact(exc)})
            if attempt == retries:
                return {"ok": False, "answer": "", "finish_reason": "", "response_model": "", "usage": {}, "attempts": attempts, "error": redact(exc)}
            time.sleep(1.5 * attempt)
            continue
        answer, finish_reason = response_text(response)
        usage = response.get("usage") or {}
        model = str(response.get("model") or "")
        total = int(usage.get("total_tokens") or 0)
        valid = bool(answer.strip() and finish_reason == "stop" and model and total > 0)
        attempts.append({"attempt": attempt, "status": 200, "finish_reason": finish_reason, "usage": usage})
        # A truncated or empty answer (e.g. reasoning used the whole max_tokens budget)
        # is a property of this sample, not the task, so draw a fresh one.
        if not valid and attempt < retries:
            time.sleep(1.5 * attempt)
            continue
        return {"ok": valid, "answer": answer, "finish_reason": finish_reason, "response_model": model, "usage": usage, "attempts": attempts, "error": None if valid else "invalid provider response"}
    raise AssertionError("unreachable")


def completed(paths: list[Path]) -> set[tuple[int, str]]:
    return {(int(row["rollout"]), row["task_slug"]) for path in paths for row in read_jsonl(path) if str(row.get("answer") or "").strip()}


def canonicalize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = {row["task_slug"]: row for row in read_jsonl(path)}
    path.write_text("".join(json.dumps(rows[key], ensure_ascii=False, sort_keys=True) + "\n" for key in sorted(rows)), encoding="utf-8")
