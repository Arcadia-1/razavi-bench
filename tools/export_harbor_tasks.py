#!/usr/bin/env python3
"""Export the Razavi-Bench tasks as Harbor tasks, one directory per task.

<output-dir>/<task_slug>/
  task.toml        /app/answer.md is the artifact; the verifier runs in its own container
  instruction.md   the question (the task's prompt: no title or figure numbers) with the mode's
                   environment notes and deliverable
  environment/     the mode's image (agentic/harness/harbor-<mode>.Dockerfile and its public
                   files), any --preinstall agents, and in /app the question (instruction.md) and
                   the figure, named figure-1.png rather than by the article's figure number
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

from direct_qa_openrouter_common import REPO_ROOT, load_tasks, prompt_text

HARBOR_DIR = REPO_ROOT / "agentic/harbor"
# Each mode's image: its Dockerfile and the only repository paths the task environment holds.
MODES: dict[str, dict[str, Any]] = {
    "multimodal": {"dockerfile": "agentic/harness/harbor-multimodal.Dockerfile", "context": []},
    "ngspice-sky130": {
        "dockerfile": "agentic/harness/harbor-ngspice-sky130.Dockerfile",
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
# Harbor's mini-swe-agent setup downloads uv with curl.
CURL_LAYER = """
RUN apt-get update \\
    && apt-get install -y --no-install-recommends curl \\
    && rm -rf /var/lib/apt/lists/*
"""
# Node for the agents --preinstall builds in. Harbor's own installs fetch nvm from GitHub and
# Node from nodejs.org on every run; here Node is fetched once, with retries. The checksums are
# nodejs.org's SHASUMS256.txt entries for the tarballs.
NODE_LAYER = """
ARG NODE_VERSION=22.23.4
ARG NODE_SHA256_X64=b8492284c76a54baf58d61668dd0e41ee0fc98adabf9503d30f05d08f55b4406
ARG NODE_SHA256_ARM64=f7a1e486dbc8b286847815b477d4fb5e9fb963ed4489c3e1588853d685f589f9

RUN set -eux; \\
    case "$(dpkg --print-architecture)" in \\
        amd64) arch=x64; sha256="${NODE_SHA256_X64}" ;; \\
        arm64) arch=arm64; sha256="${NODE_SHA256_ARM64}" ;; \\
        *) echo "unsupported architecture" >&2; exit 1 ;; \\
    esac; \\
    tarball="node-v${NODE_VERSION}-linux-${arch}.tar.gz"; \\
    curl -fsSL --retry 10 --retry-all-errors --retry-delay 3 -o "/tmp/${tarball}" "https://nodejs.org/dist/v${NODE_VERSION}/${tarball}"; \\
    echo "${sha256}  /tmp/${tarball}" | sha256sum -c -; \\
    tar -xzf "/tmp/${tarball}" -C /usr/local --strip-components=1 --no-same-owner; \\
    rm "/tmp/${tarball}"; \\
    node --version
"""
NPM_INSTALL = "npm install -g --fetch-retries=10 --fetch-retry-mintimeout=5000 --fetch-retry-maxtimeout=60000"
# Agents that --preinstall builds into the image, so a run downloads nothing. They come before
# the task files, so every task shares them once built; the npm-based ones follow NODE_LAYER.
NODE_AGENTS = {"claude-code", "codex", "gemini-cli"}
PREINSTALL_LAYERS = {
    # Harbor's claude-code agent skips its own install when `claude` is at the requested
    # version, so pass --agent-kwarg=version=2.1.198. procps is among the tools that install adds.
    "claude-code": f"""
ARG CLAUDE_CODE_VERSION=2.1.198
RUN apt-get update \\
    && apt-get install -y --no-install-recommends procps \\
    && rm -rf /var/lib/apt/lists/* \\
    && {NPM_INSTALL} "@anthropic-ai/claude-code@${{CLAUDE_CODE_VERSION}}" \\
    && claude --version
""",
    # Run with agentic/harbor/razavi_mini_swe_agent.py, which skips Harbor's install when this
    # toolchain is present. It is that install (uv, Python 3.12, mini-swe-agent with litellm,
    # orjson and fastapi) with litellm pinned, plus mcp, which litellm's tool-calling path imports.
    "mini-swe-agent": """
ARG UV_VERSION=0.13.6
ARG MINI_SWE_AGENT_VERSION=2.4.6
ARG LITELLM_VERSION=1.106.4
ARG ORJSON_VERSION=3.13.0
ARG FASTAPI_VERSION=0.162.0
ARG MCP_VERSION=2.3.0

RUN set -eux; \\
    export UV_HTTP_RETRIES=10; \\
    pip install --no-cache-dir --retries=10 "uv==${UV_VERSION}"; \\
    for attempt in 1 2 3 4 5 6; do uv python install 3.12 && break; sleep 5; done; \\
    uv tool install --python 3.12 "mini-swe-agent==${MINI_SWE_AGENT_VERSION}" \\
        --with "litellm==${LITELLM_VERSION}" --with "orjson==${ORJSON_VERSION}" \\
        --with "fastapi==${FASTAPI_VERSION}" --with "mcp==${MCP_VERSION}"; \\
    "$(uv tool dir)/mini-swe-agent/bin/python" -c "import minisweagent, mcp; print(minisweagent.__version__)"
""",
    # Run with agentic/harbor/razavi_gemini_cli.py, which skips Harbor's install when gemini exists.
    "gemini-cli": f"""
ARG GEMINI_CLI_VERSION=0.65.0
RUN {NPM_INSTALL} "@google/gemini-cli@${{GEMINI_CLI_VERSION}}" && gemini --version
""",
    # Harbor's codex agent skips its own install when codex is already on PATH. ripgrep is
    # among the tools that install would otherwise add.
    "codex": f"""
ARG CODEX_VERSION=0.165.0
RUN apt-get update \\
    && apt-get install -y --no-install-recommends ripgrep \\
    && rm -rf /var/lib/apt/lists/* \\
    && {NPM_INSTALL} "@openai/codex@${{CODEX_VERSION}}" \\
    && codex --version
""",
}
# The agent works in /app.
TASK_LAYER = """
COPY task/ /app/
"""
# The verifier inherits the task's workdir (/app), where Harbor also places the answer artifact.
VERIFIER_DOCKERFILE = """FROM python:3.11-slim-bookworm

WORKDIR /app
COPY . /tests/
"""
# With --network public the agent's container can reach the internet, so the instruction asks
# instead of stating; everything else is the same.
NO_INTERNET = "There is no internet access."
NO_INTERNET_REQUEST = "Do not use the internet; work only with the files and tools in this container."
TEST_SH = """#!/bin/bash
# Grade /app/answer.md with the Razavi-Bench judge; see grade.py.
exec python3 /tests/grade.py
"""


def question_md(task: dict[str, Any]) -> str:
    """The question as the agent sees it: the task's prompt, the text the direct runs send, with no
    title, figure numbers or subfigure labels."""
    return f"## Question\n\n{prompt_text(task)}"


def figure_names(task: dict[str, Any]) -> list[str]:
    """Each figure's name in /app: figure-<n>.png in order, not the article's figure number."""
    return [f"figure-{n}.png" for n in range(1, len(task.get("figures") or []) + 1)]


def task_text(task: dict[str, Any], mode: str) -> str:
    """The agent's instruction: the question, the mode's environment notes and the deliverable.

    agentic/harbor/mini_with_figures.py adds the figures as images before "## Environment".
    """
    return "\n\n".join([question_md(task), f"## Environment\n\n{ENVIRONMENT[mode]}", f"## Deliverable\n\n{DELIVERABLE}"])


def context_files(root: Path, mode: str) -> list[str]:
    """The mode's Dockerfile, then every public file its image copies from the repository."""
    spec = MODES[mode]
    files = [spec["dockerfile"]]
    for relative in spec["context"]:
        for path in sorted((root / relative).rglob("*")):
            if path.is_file() and not SKIP_PARTS & set(path.relative_to(root).parts):
                files.append(path.relative_to(root).as_posix())
    return files


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

    environment = target / "environment"
    for relative in context_files(root, args.mode):
        destination = environment / ("Dockerfile" if relative == MODES[args.mode]["dockerfile"] else relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, destination)
    with (environment / "Dockerfile").open("a", encoding="utf-8") as dockerfile:
        agents = sorted(set(args.preinstall))
        node = [NODE_LAYER] if NODE_AGENTS.intersection(agents) else []
        dockerfile.write("".join([CURL_LAYER, *node, *(PREINSTALL_LAYERS[agent] for agent in agents), TASK_LAYER]))
    (environment / "task").mkdir(parents=True)
    (environment / "task/instruction.md").write_text(question_md(task) + "\n", encoding="utf-8")
    for relative, name in zip(task.get("figures") or [], figure_names(task)):
        shutil.copy2(root / relative, environment / "task" / name)

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

    instruction = task_text(task, args.mode)
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
    parser.add_argument(
        "--preinstall",
        action="append",
        choices=sorted(PREINSTALL_LAYERS),
        default=[],
        help="build an agent into the task image so runs download nothing; repeatable (mini-swe-agent and "
        "gemini-cli: run with agentic/harbor/razavi_*.py; codex, claude-code: Harbor's own agents)",
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
