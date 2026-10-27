#!/usr/bin/env python3
"""Export the Razavi-Bench tasks as Harbor tasks, one directory per task.

<output-dir>/<task_slug>/
  task.toml        /app/answer.md is the artifact; the verifier runs in its own container
  instruction.md   the question with the mode's environment notes and deliverable, worded as
                   tools/run_agentic_miniswe.py words them, without the inline figures
  environment/     the mode's image (agentic/harness/miniswe-<mode>.Dockerfile and its public
                   files) plus the task's instruction and figures in /app
  tests/           the verifier image: agentic/harbor/grade.py, tools/evaluate_answers.py, the
                   rubric and this task's golden solution

Golden solutions and the rubric only go into tests/, which Harbor builds into a separate
verifier container after the agent finishes. Run the tasks with
agentic/harbor/razavi_mini_swe_agent.py so mini-swe-agent sees the figures as images.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from direct_qa_openrouter_common import REPO_ROOT, load_tasks
from run_agentic_miniswe import MODES, context_files, task_text

HARBOR_DIR = REPO_ROOT / "agentic/harbor"
# Harbor's mini-swe-agent setup downloads uv with curl; the agent works in /app.
ENVIRONMENT_SUFFIX = """
RUN apt-get update \\
    && apt-get install -y --no-install-recommends curl \\
    && rm -rf /var/lib/apt/lists/*

COPY task/ /app/
"""
# The verifier inherits the task's workdir (/app), where Harbor also places the answer artifact.
VERIFIER_DOCKERFILE = """FROM python:3.11-slim-bookworm

WORKDIR /app
COPY . /tests/
"""
# With --network public the agent's container can reach the internet, so the instruction asks
# instead of stating; everything else matches the runner's wording.
NO_INTERNET = "There is no internet access."
NO_INTERNET_REQUEST = "Do not use the internet; work only with the files and tools in this container."
TEST_SH = """#!/bin/bash
# Grade /app/answer.md with the Razavi-Bench judge; see grade.py.
exec python3 /tests/grade.py
"""


def toml_value(value: Any) -> str:
    """TOML basic strings, integers and arrays of them are written like JSON."""
    return json.dumps(value, ensure_ascii=False)


def task_toml(task: dict[str, Any], args: argparse.Namespace) -> str:
    metadata = {"task_slug": task["task_slug"], "part": task["part"], "question_number": task["question_number"], "mode": args.mode, "figures": task.get("figures") or []}
    name = f"razavi-bench/{args.mode}-{task['task_slug']}"
    description = f"Razavi-Bench {task['part']} question {task['question_number']}, agentic {args.mode} mode"
    return "\n".join([
        'schema_version = "1.4"',
        'artifacts = ["/app/answer.md"]',
        "",
        "[task]",
        f"name = {toml_value(name)}",
        'version = "1.0.0"',
        f"description = {toml_value(description)}",
        f"keywords = {toml_value(['analog-design', 'razavi-bench', args.mode])}",
        "",
        "[metadata]",
        *(f"{key} = {toml_value(value)}" for key, value in metadata.items()),
        "",
        "[verifier]",
        f"timeout_sec = {float(args.verifier_timeout)}",
        'environment_mode = "separate"',
        *(["# The verifier reaches only the judge API.", 'network_mode = "allowlist"', f"allowed_hosts = {toml_value([urlsplit(args.judge_api_url).hostname])}"]
          if args.network == "allowlist" else ['network_mode = "public"']),
        "",
        "[verifier.env]",
        f"{args.judge_key_env} = {toml_value('${' + args.judge_key_env + '}')}",
        "",
        "[agent]",
        f"timeout_sec = {float(args.agent_timeout)}",
        *(["# While the agent runs it reaches only the model API: Harbor adds the inference host,", "# or pass it with --allow-agent-host.", 'network_mode = "allowlist"', "allowed_hosts = []"]
          if args.network == "allowlist" else ["# Public: this sandbox cannot restrict egress; the instruction asks the agent not to use the internet.", 'network_mode = "public"']),
        "",
        "[environment]",
        "# Setup is public: Harbor installs mini-swe-agent into the container before the agent runs.",
        'network_mode = "public"',
        "build_timeout_sec = 1800.0",
        "cpus = 2",
        "memory_mb = 4096",
        'workdir = "/app"',
        "",
    ])


def export_task(root: Path, task: dict[str, Any], args: argparse.Namespace) -> Path:
    target = args.output_dir / task["task_slug"]
    if target.exists():
        shutil.rmtree(target)
    task_dir = root / task["task_path"]
    task_files = ["instruction.md", *(Path(relative).name for relative in task.get("figures") or [])]

    environment = target / "environment"
    for relative in context_files(root, args.mode):
        destination = environment / ("Dockerfile" if relative == MODES[args.mode]["dockerfile"] else relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, destination)
    with (environment / "Dockerfile").open("a", encoding="utf-8") as dockerfile:
        dockerfile.write(ENVIRONMENT_SUFFIX)
    (environment / "task").mkdir(parents=True)
    for name in task_files:
        shutil.copy2(task_dir / name, environment / "task" / name)

    tests = target / "tests"
    (tests / "repo" / task["task_path"]).mkdir(parents=True)
    (tests / "Dockerfile").write_text(VERIFIER_DOCKERFILE, encoding="utf-8")
    (tests / "test.sh").write_text(TEST_SH, encoding="utf-8")
    (tests / "test.sh").chmod(0o755)
    shutil.copy2(HARBOR_DIR / "grade.py", tests / "grade.py")
    shutil.copy2(root / "tools/evaluate_answers.py", tests / "evaluate_answers.py")
    shutil.copy2(root / "evaluation_rubric.md", tests / "repo/evaluation_rubric.md")
    for name in ("instruction.md", "golden_solution.md"):
        shutil.copy2(task_dir / name, tests / "repo" / task["task_path"] / name)
    judge = {"task_path": task["task_path"], "api_url": args.judge_api_url, "model": args.judge_model, "api_key_env": args.judge_key_env, "reasoning_effort": args.judge_effort, "max_tokens": args.judge_max_tokens, "timeout": args.judge_timeout}
    (tests / "judge.json").write_text(json.dumps(judge, indent=2) + "\n", encoding="utf-8")

    instruction = task_text(root, task, args.mode, attach_figures=False)
    if args.network == "public":
        instruction = instruction.replace(NO_INTERNET, NO_INTERNET_REQUEST, 1)
    (target / "instruction.md").write_text(instruction + "\n", encoding="utf-8")
    (target / "task.toml").write_text(task_toml(task, args), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--mode", choices=sorted(MODES), default="ngspice-sky130")
    parser.add_argument(
        "--network",
        choices=("allowlist", "public"),
        default="allowlist",
        help="allowlist: the agent reaches only the model API and the verifier only the judge API, which needs a "
        "sandbox that can switch network policy (not Docker Desktop); public: open throughout",
    )
    parser.add_argument("--output-dir", type=Path, default=None, help="default: output/harbor/<mode>, or <mode>-public")
    parser.add_argument("--task-slug", action="append", default=[])
    parser.add_argument("--agent-timeout", type=int, default=3600, help="seconds")
    parser.add_argument("--verifier-timeout", type=int, default=2400, help="seconds, judge call included")
    parser.add_argument("--judge-api-url", default="https://openrouter.ai/api/v1/chat/completions")
    parser.add_argument("--judge-model", default="openai/gpt-6-luna")
    parser.add_argument("--judge-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--judge-effort", default="max")
    parser.add_argument("--judge-max-tokens", type=int, default=128000)
    parser.add_argument("--judge-timeout", type=int, default=1800)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    args.output_dir = (args.output_dir or root / "output/harbor" / (args.mode + ("-public" if args.network == "public" else ""))).resolve()
    tasks = load_tasks(root, args.task_slug or None)
    for task in tasks:
        export_task(root, task, args)
    print(f"exported {len(tasks)} {args.mode} tasks to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
