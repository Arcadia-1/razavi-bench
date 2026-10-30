"""Harbor's mini-swe-agent with each task's figures sent to the model as images.

Use it with the tasks from tools/export_harbor_tasks.py:

    PYTHONPATH=agentic/harbor harbor run --agent razavi_mini_swe_agent:RazaviMiniSweAgent ...

Harbor gives mini-swe-agent the task as text on its command line, so a bash-only
agent would never see the figures. Before the agent starts, this class uploads
mini_with_figures.py and launches mini-swe-agent through it; the script adds the
figures to the task inside the container and turns on mini-swe-agent's
multimodal tags. Everything else is Harbor's MiniSweAgent, pinned to
mini-swe-agent 2.4.6 and capped at 500 steps, as Artificial Analysis runs
Terminal-Bench 4.0. A `config` agent kwarg is merged
over these defaults. Tasks exported with `--preinstall mini-swe-agent` already
contain that mini-swe-agent, and then Harbor's install is skipped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harbor.agents.installed.mini_swe_agent import MiniSweAgent

MINI_SWE_AGENT_VERSION = "2.4.6"
MULTIMODAL_REGEX = r"(?s)<MSWEA_MULTIMODAL_CONTENT><CONTENT_TYPE>(.+?)</CONTENT_TYPE>(.+?)</MSWEA_MULTIMODAL_CONTENT>"
DEFAULT_CONFIG: dict[str, Any] = {"agent": {"step_limit": 500}, "model": {"multimodal_regex": MULTIMODAL_REGEX}}
# Prints the version of a mini-swe-agent already installed with uv, failing if it or mcp is missing.
PREINSTALLED_CHECK = (
    'export PATH="$HOME/.local/bin:$PATH" MSWEA_SILENT_STARTUP=1; '
    '"$(uv tool dir)/mini-swe-agent/bin/python" -c "import minisweagent, mcp; print(minisweagent.__version__)"'
)
WRAPPER = Path(__file__).with_name("mini_with_figures.py")
WRAPPER_TARGET = "/tmp/mini_with_figures.py"
LAUNCH = "mini-swe-agent --yolo"


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        merged[key] = merge(merged[key], value) if isinstance(value, dict) and isinstance(merged.get(key), dict) else value
    return merged


class RazaviMiniSweAgent(MiniSweAgent):
    def __init__(self, *args: Any, config: dict[str, Any] | None = None, version: str | None = None, **kwargs: Any):
        super().__init__(*args, config=merge(DEFAULT_CONFIG, config or {}), version=version or MINI_SWE_AGENT_VERSION, **kwargs)

    async def install(self, environment: Any) -> None:
        # tools/export_harbor_tasks.py --preinstall mini-swe-agent builds this toolchain into the
        # image; then nothing is downloaded at run time.
        found = await environment.exec(PREINSTALLED_CHECK)
        if found.return_code == 0 and (found.stdout or "").strip().splitlines()[-1:] == [self._version]:
            return
        await super().install(environment)
        # Harbor 0.25 installs litellm without its proxy extra, but litellm's tool-calling path
        # imports the MCP client, so every model call would fail without it.
        await self.exec_as_agent(
            environment,
            'export PATH="$HOME/.local/bin:$PATH" && uv pip install --python "$(uv tool dir)/mini-swe-agent/bin/python" "mcp>=2.2,<3"',
        )

    async def run(self, instruction: str, environment: Any, context: Any) -> None:
        await environment.upload_file(WRAPPER, WRAPPER_TARGET)
        await super().run(instruction, environment, context)

    async def exec_as_agent(self, environment: Any, command: str, **kwargs: Any) -> Any:
        if LAUNCH in command:
            # Same arguments, but through the wrapper and with mini-swe-agent's own Python.
            command = command.replace(LAUNCH, f'"$(uv tool dir)/mini-swe-agent/bin/python" {WRAPPER_TARGET} --yolo', 1)
        return await super().exec_as_agent(environment, command, **kwargs)
