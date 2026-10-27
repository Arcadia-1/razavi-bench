#!/usr/bin/env python3
"""Agentic Razavi-Bench runner on mini-swe-agent, set up like Artificial Analysis's Terminal-Bench 4.0.

Every rollout of every task runs mini-swe-agent's DefaultAgent with its `mini` config and prompts,
the native bash tool and the full transcript (no compaction), capped at 500 steps, in a fresh
Docker container without network. A bash-only agent cannot look at a PNG, so the task's figures
are attached to the first user message as images through mini-swe-agent's multimodal tags; the
same files are also in /app. Only /app/answer.md is kept as the answer.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import functools
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from direct_qa_openrouter import check_effort
from direct_qa_openrouter_common import (
    DEFAULT_SMOKE_TASKS,
    PROVIDERS,
    REPO_ROOT,
    append_jsonl,
    canonicalize,
    completed,
    endpoint,
    load_tasks,
    payload,
    read_jsonl,
    redact,
    write_json,
    write_jsonl,
)

MINI_SWE_AGENT_VERSION = "2.4.6"
# Each mode's image: its Dockerfile and the only repository paths its build context holds.
MODES: dict[str, dict[str, Any]] = {
    "multimodal": {"dockerfile": "agentic/harness/miniswe-agentic-multimodal.Dockerfile", "context": []},
    "ngspice-sky130": {
        "dockerfile": "agentic/harness/miniswe-ngspice-sky130.Dockerfile",
        "context": ["simulator/ngspice-sky130", "agentic/skills/ngspice-sky130"],
    },
}
ENVIRONMENT = {
    "multimodal": "The task files are in /app: instruction.md and the figure PNGs. There is no internet access.",
    "ngspice-sky130": (
        "The task files are in /app: instruction.md and the figure PNGs. ngspice is installed with a Sky130 1.8 V "
        "primitive model bundle: the models are in /tools/ngspice-sky130/models (include "
        "/tools/ngspice-sky130/models/sky130.lib.spice) and example decks are in /tools/ngspice-sky130/examples. "
        "Before deciding whether to simulate, read the skill at /app/.claude/skills/ngspice-sky130/SKILL.md and "
        "follow it: simulation is optional supporting evidence, and the answer must rest on circuit reasoning. "
        "There is no internet access."
    ),
}
DELIVERABLE = (
    "Write your final answer to /app/answer.md. Only /app/answer.md is graded; scratch files, decks and logs "
    "are ignored. After writing it, finish with `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`."
)
SKIP_PARTS = {".DS_Store", "__pycache__"}
DATA_URL_RE = re.compile(r"data:image/[\w.+-]+;base64,[A-Za-z0-9+/=]+")
# ngspice as a command, not inside a path such as /tools/ngspice-sky130, or the skill's runners.
SIMULATION_RE = re.compile(r"(?<![\w/.-])ngspice(?![\w/.-])|run_op_probe|run_examples")


def figure_tag(path: Path) -> str:
    """mini-swe-agent expands this tag in a message into an image_url content part."""
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"<MSWEA_MULTIMODAL_CONTENT><CONTENT_TYPE>image_url</CONTENT_TYPE>data:{media_type};base64,{encoded}</MSWEA_MULTIMODAL_CONTENT>"


def task_text(root: Path, task: dict[str, Any], mode: str, attach_figures: bool = True) -> str:
    """The {{task}} of mini-swe-agent's instance template: question, figures as images, environment, deliverable.

    Without attach_figures it is the text-only instruction of the exported Harbor tasks, whose
    agent (agentic/harbor/mini_with_figures.py) adds the same figure section inside the container.
    """
    parts = [task["instruction"].strip()]
    figures = task.get("figures") or []
    if figures and attach_figures:
        parts.append("## Attached Figures\n\nThe figures are shown below; the same PNG files are in /app.")
        parts.extend(f"{Path(relative).name}:\n{figure_tag(root / relative)}" for relative in figures)
    parts.append(f"## Environment\n\n{ENVIRONMENT[mode]}")
    parts.append(f"## Deliverable\n\n{DELIVERABLE}")
    return "\n\n".join(parts)


def strip_images(value: Any) -> Any:
    """Drop inline base64 images so saved trajectories stay small; the figures are in the task directory."""
    if isinstance(value, str):
        return DATA_URL_RE.sub("<image omitted>", value)
    if isinstance(value, list):
        return [strip_images(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_images(item) for key, item in value.items()}
    return value


def usage_totals(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum OpenRouter usage over every billed model call, including calls that ended in a format error."""
    totals: dict[str, Any] = {"model_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cached_tokens": 0, "reasoning_tokens": 0, "cost": 0.0}
    for message in messages:
        response = (message.get("extra") or {}).get("response")
        if not isinstance(response, dict):
            continue
        usage = response.get("usage") or {}
        totals["model_calls"] += 1
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            totals[key] += int(usage.get(key) or 0)
        # DeepSeek reports cache hits as prompt_cache_hit_tokens.
        totals["cached_tokens"] += int((usage.get("prompt_tokens_details") or {}).get("cached_tokens") or usage.get("prompt_cache_hit_tokens") or 0)
        totals["reasoning_tokens"] += int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
        totals["cost"] += float(usage.get("cost") or 0)
    return totals


def add_usage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = usage_totals([])
    for row in rows:
        for key, value in row.items():
            totals[key] += value
    return totals


def commands(messages: list[dict[str, Any]]) -> list[str]:
    return [action.get("command", "") for message in messages for action in (message.get("extra") or {}).get("actions") or []]


def context_files(root: Path, mode: str) -> list[str]:
    spec = MODES[mode]
    files = [spec["dockerfile"]]
    for relative in spec["context"]:
        for path in sorted((root / relative).rglob("*")):
            if path.is_file() and not SKIP_PARTS & set(path.relative_to(root).parts):
                files.append(path.relative_to(root).as_posix())
    return files


def docker(*args: str, check: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, check=check, **kwargs)


def ensure_image(root: Path, mode: str) -> str:
    """Build the mode's image from a context of only its public files, tagged with their content hash."""
    files = context_files(root, mode)
    digest = hashlib.sha256()
    for relative in files:
        data = (root / relative).read_bytes()
        digest.update(f"{relative}\0{len(data)}\0".encode() + data)
    tag = f"razavi-bench/miniswe-{mode}:{digest.hexdigest()[:12]}"
    if docker("image", "inspect", tag, check=False).returncode == 0:
        return tag
    with tempfile.TemporaryDirectory() as context:
        for relative in files:
            (Path(context) / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, Path(context) / relative)
        subprocess.run(["docker", "build", "-t", tag, "-f", str(Path(context) / MODES[mode]["dockerfile"]), context], check=True)
    return tag


@functools.cache
def mini() -> SimpleNamespace:
    """Import mini-swe-agent on first use, so the helpers above work without it."""
    os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
    import minisweagent
    import requests
    import yaml
    from minisweagent.agents.default import DefaultAgent
    from minisweagent.config import builtin_config_dir
    from minisweagent.environments.docker import DockerEnvironment
    from minisweagent.models.openrouter_model import OpenRouterAPIError, OpenRouterAuthenticationError, OpenRouterModel, OpenRouterRateLimitError
    from minisweagent.models.utils.actions_toolcall import BASH_TOOL
    from minisweagent.models.utils.openai_multimodal import DEFAULT_MULTIMODAL_REGEX

    if minisweagent.__version__ != MINI_SWE_AGENT_VERSION:
        raise RuntimeError(f"mini-swe-agent {MINI_SWE_AGENT_VERSION} is required, found {minisweagent.__version__}")

    class Agent(DefaultAgent):
        def serialize(self, *extra_dicts: dict) -> dict:
            return strip_images(super().serialize(*extra_dicts))

    class Model(OpenRouterModel):
        """mini-swe-agent's OpenRouter model, pointed at any OpenAI-format provider, with a set HTTP timeout
        (its fixed 60 s cuts off long reasoning steps)."""

        def __init__(self, *, provider: str, base_url: str, request_timeout: int, **kwargs: Any):
            # Only OpenRouter reports each call's cost; elsewhere tokens are recorded and the cost limit is inactive.
            super().__init__(cost_tracking="default" if provider == "openrouter" else "ignore_errors", **kwargs)
            self.provider = provider
            self._api_url = endpoint(base_url)
            self._api_key = os.environ[PROVIDERS[provider]["key_env"]]
            self.request_timeout = request_timeout

        def _query(self, messages: list[dict], **kwargs: Any) -> dict:
            headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json", "HTTP-Referer": "https://razavi-bench.tokenzhang.com", "X-Title": "Razavi-Bench Agentic"}
            body = {"model": self.config.model_name, "messages": messages, "tools": [BASH_TOOL], **(self.config.model_kwargs | kwargs)}
            if self.provider == "openrouter":
                body["usage"] = {"include": True}
            try:
                response = requests.post(self._api_url, headers=headers, data=json.dumps(body), timeout=self.request_timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as exc:
                if response.status_code == 401:
                    raise OpenRouterAuthenticationError("Authentication failed") from exc
                if response.status_code == 429:
                    raise OpenRouterRateLimitError("Rate limit exceeded") from exc
                raise OpenRouterAPIError(f"HTTP {response.status_code}: {response.text}") from exc
            except requests.exceptions.RequestException as exc:
                raise OpenRouterAPIError(f"Request failed: {exc}") from exc

    config = yaml.safe_load((builtin_config_dir / "mini.yaml").read_text())
    return SimpleNamespace(Agent=Agent, Model=Model, DockerEnvironment=DockerEnvironment, config=config, multimodal_regex=DEFAULT_MULTIMODAL_REGEX, version=minisweagent.__version__)


def model_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    """Effort and sampling fields in each provider's format, as the Direct-QA runner sends them."""
    body = payload(args.model, [], args.effort, args.max_tokens or 0, args.provider)
    kwargs = {key: value for key, value in body.items() if key not in ("model", "messages", "max_tokens", "stream")}
    if args.max_tokens:
        kwargs["max_tokens"] = args.max_tokens
    return kwargs


def run_once(args: argparse.Namespace, root: Path, task: dict[str, Any], rollout: int, attempt: int, image: str) -> dict[str, Any]:
    """One agent run in a fresh container; returns its answer and what it cost."""
    m = mini()
    started = time.time()
    trajectory = args.output_dir / "raw-responses" / "trajectories" / f"{args.output_prefix}-rollout-{rollout}" / f"{task['task_slug']}.attempt-{attempt}.traj.json"
    env = m.DockerEnvironment(
        image=image,
        cwd="/app",
        env=m.config["environment"]["env"],
        timeout=args.command_timeout,
        run_args=["--rm", "--network", "none", f"--cpus={args.cpus}", f"--memory={args.memory}"],
        container_timeout=f"{args.wall_time + 600}s",
    )
    try:
        task_files = ["instruction.md", *(Path(relative).name for relative in task.get("figures") or [])]
        for name in task_files:
            docker("cp", str(root / task["task_path"] / name), f"{env.container_id}:/app/{name}")
        # mini's prompt describes the machine from these; report the container, not the host running Docker.
        uname = {key: docker("exec", env.container_id, "uname", flag, text=True).stdout.strip() for key, flag in (("system", "-s"), ("release", "-r"), ("version", "-v"), ("machine", "-m"))}
        model = m.Model(
            provider=args.provider,
            base_url=args.base_url,
            model_name=args.model,
            model_kwargs=model_kwargs(args),
            multimodal_regex=m.multimodal_regex,
            observation_template=m.config["model"]["observation_template"],
            format_error_template=m.config["model"]["format_error_template"],
            request_timeout=args.timeout,
        )
        agent_config = {key: value for key, value in m.config["agent"].items() if key != "mode"}
        agent_config.update(step_limit=args.step_limit, cost_limit=args.cost_limit, wall_time_limit_seconds=args.wall_time, output_path=trajectory)
        agent = m.Agent(model, env, **agent_config)
        error = None
        try:
            agent.run(task_text(root, task, args.mode), **uname)
        except Exception as exc:  # the agent has already recorded it as its exit message
            error = redact(exc)
        answer = docker("exec", env.container_id, "cat", "/app/answer.md", check=False, text=True).stdout
        found = docker("exec", env.container_id, "find", "/app", "-path", "/app/.claude", "-prune", "-o", "-type", "f", "-print", check=False, text=True).stdout.split()
    finally:
        env.cleanup()
    responses = [message["extra"]["response"] for message in agent.messages if isinstance((message.get("extra") or {}).get("response"), dict)]
    return {
        "attempt": attempt,
        "ok": bool(answer.strip()),
        "answer": answer,
        "exit_status": (agent.messages[-1].get("extra") or {}).get("exit_status", "") if agent.messages else "",
        "error": error,
        "steps": agent.n_calls,
        "usage": usage_totals(agent.messages),
        "response_model": responses[-1].get("model", "") if responses else "",
        "providers": sorted({str(response.get("provider")) for response in responses if response.get("provider")}),
        "ngspice_commands": sum(bool(SIMULATION_RE.search(command)) for command in commands(agent.messages)),
        "files": sorted(set(found) - {f"/app/{name}" for name in task_files}),
        "trajectory": trajectory.relative_to(args.output_dir).as_posix(),
        "wall_seconds": round(time.time() - started, 1),
    }


def public_record(task: dict[str, Any], rollout: int, result: dict[str, Any], attempts: int, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "benchmark": "razavi-bench",
        "experiment": args.experiment,
        "run_date": args.run_date,
        "task_slug": task["task_slug"],
        "task_path": task["task_path"],
        "part": task["part"],
        "question_number": task["question_number"],
        "question": task["instruction"].split("## Question\n\n", 1)[-1].strip(),
        "figures": task.get("figures") or [],
        "rollout": rollout,
        "answer": result["answer"],
        "mode": "agentic_" + args.mode.replace("-", "_"),
        "harness": f"mini-swe-agent {MINI_SWE_AGENT_VERSION}",
        "provider_model": args.model,
        "model_name": args.model_name,
        "model_family": args.model_family,
        "reasoning_effort": args.effort,
        "agent_attempts": attempts,
        "agent_steps": result["steps"],
        "agent_exit_status": result["exit_status"],
        "ngspice_commands": result["ngspice_commands"],
        "internet_or_tool_evidence": True,
    }


def execute(args: argparse.Namespace, smoke: bool = False) -> dict[str, Any]:
    provider = PROVIDERS[args.provider]
    args.base_url = args.base_url or provider["base_url"]
    if not os.environ.get(provider["key_env"]):
        raise ValueError(f"missing {provider['key_env']}")
    if min(args.concurrency, args.timeout, args.step_limit, args.wall_time, args.command_timeout, args.max_retries) < 1:
        raise ValueError("numeric arguments must be positive")
    effort_check = check_effort(args)

    root = args.repo_root.resolve()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(root, args.task_slug or (list(DEFAULT_SMOKE_TASKS) if smoke else None))
    rollouts = sorted(set(args.rollout or [1]))
    paths = {rollout: args.output_dir / "model_outputs" / f"{args.output_prefix}-rollout-{rollout}.jsonl" for rollout in rollouts}
    done = completed(list(paths.values())) if args.resume else set()
    jobs = [(rollout, task) for rollout in rollouts for task in tasks if (rollout, task["task_slug"]) not in done]
    image = ensure_image(root, args.mode)
    version = mini().version
    raw_path = args.output_dir / "raw_logs.jsonl"
    failures = []
    print(f"model={args.model} mode={args.mode} image={image} expected={len(tasks) * len(rollouts)} completed={len(done)} pending={len(jobs)}", flush=True)

    def one(job: tuple[int, dict[str, Any]]) -> tuple[int, dict[str, Any], list[dict[str, Any]]]:
        rollout, task = job
        attempts = []
        # An empty answer (no answer.md, a crashed run) is a property of this sample, not the task, so draw a fresh one.
        for attempt in range(1, args.max_retries + 1):
            try:
                result = run_once(args, root, task, rollout, attempt, image)
            except Exception as exc:  # the container or the copy failed before the agent ran
                result = {"attempt": attempt, "ok": False, "answer": "", "error": redact(exc), "usage": usage_totals([])}
            attempts.append(result)
            if result["ok"]:
                break
        return rollout, task, attempts

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            rollout, task, attempts = future.result()
            final = attempts[-1]
            append_jsonl(raw_path, {
                "experiment": args.experiment,
                "task_slug": task["task_slug"],
                "rollout": rollout,
                "figures": task.get("figures") or [],
                "ok": final["ok"],
                "answer": final["answer"],
                "usage": add_usage([attempt["usage"] for attempt in attempts]),
                "attempts": attempts,
            })
            print(f"{'ok  ' if final['ok'] else 'FAIL'} r{rollout} {task['task_slug']} steps={final.get('steps')} exit={final.get('exit_status') or final.get('error')} ngspice={final.get('ngspice_commands')}", flush=True)
            if final["ok"]:
                append_jsonl(paths[rollout], public_record(task, rollout, final, len(attempts), args))
            else:
                failures.append({"task_slug": task["task_slug"], "rollout": rollout, "error": final.get("error") or final.get("exit_status") or "no /app/answer.md"})

    for path in paths.values():
        canonicalize(path)
    rows = sorted((row for path in paths.values() for row in read_jsonl(path)), key=lambda row: (row["task_slug"], row["rollout"]))
    judge_input = args.output_dir / "judge_input.jsonl"
    write_jsonl(judge_input, rows)
    raws = [row for row in read_jsonl(raw_path) if any(row["task_slug"] == task["task_slug"] for task in tasks)]
    report = {
        "status": "pass" if not failures and len(rows) == len(tasks) * len(rollouts) else "fail",
        "experiment": args.experiment,
        "model": args.model,
        "provider": args.provider,
        "base_url": args.base_url,
        "effort": args.effort,
        "max_tokens": args.max_tokens,
        "mode": args.mode,
        "harness": {
            "mini_swe_agent": version,
            "agent": "DefaultAgent with the mini config and prompts (minisweagent/config/mini.yaml), native bash tool, full transcript",
            "model_class": f"OpenRouterModel on {endpoint(args.base_url)}, HTTP timeout {args.timeout} s",
            "step_limit": args.step_limit,
            "cost_limit": args.cost_limit if args.provider == "openrouter" else None,
            "wall_time_limit_seconds": args.wall_time,
            "command_timeout_seconds": args.command_timeout,
            "figures": "attached to the first user message as images (multimodal_regex), and copied into /app",
        },
        "environment": {"image": image, "network": "none", "cpus": args.cpus, "memory": args.memory},
        "expected_answers": len(tasks) * len(rollouts),
        "valid_answers": len(rows),
        "image_answers": sum(bool(row["figures"]) for row in rows),
        "answers_with_ngspice": sum(row["ngspice_commands"] > 0 for row in rows),
        "mean_agent_steps": round(sum(row["agent_steps"] for row in rows) / len(rows), 2) if rows else None,
        "usage": add_usage([row["usage"] for row in raws]),
        "effort_check": effort_check,
        "failures": failures,
        "judge_input": str(judge_input),
    }
    write_json(args.output_dir / "validation_report.json", report)
    return report


def add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--model", required=True, help="the provider's model id")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-family", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-date", required=True)
    parser.add_argument("--task-slug", action="append", default=[])
    parser.add_argument("--rollout", action="append", type=int, default=[])
    parser.add_argument("--mode", choices=sorted(MODES), default="ngspice-sky130")
    # The agent's model calls are not streamed, so providers that need streaming are left out.
    parser.add_argument("--provider", choices=sorted(name for name, spec in PROVIDERS.items() if not spec.get("stream")), default="openrouter")
    parser.add_argument("--base-url", default=None, help="override the provider's base URL")
    parser.add_argument("--effort", default="top", help='reasoning effort: "top" (the highest the model lists), "default", or a listed effort')
    parser.add_argument("--skip-effort-check", action="store_true")
    parser.add_argument("--max-tokens", type=int, default=None, help="per model call; not sent when omitted")
    parser.add_argument("--timeout", type=int, default=1800, help="HTTP timeout of one model call, in seconds")
    parser.add_argument("--step-limit", type=int, default=500, help="Artificial Analysis's Terminal-Bench 4.0 cap")
    parser.add_argument("--cost-limit", type=float, default=3.0, help="USD per run; mini-swe-agent's mini default (OpenRouter only)")
    parser.add_argument("--wall-time", type=int, default=3600, help="seconds per run")
    parser.add_argument("--command-timeout", type=int, default=30, help="seconds per bash command; mini-swe-agent's Docker default")
    parser.add_argument("--cpus", default="2")
    parser.add_argument("--memory", default="4g")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-retries", type=int, default=2, help="runs per slot until one leaves a non-empty /app/answer.md")
    parser.add_argument("--resume", action="store_true")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "probe"):
        add_run_args(subcommands.add_parser(name))
    args = parser.parse_args()
    report = execute(args, args.command == "probe")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
