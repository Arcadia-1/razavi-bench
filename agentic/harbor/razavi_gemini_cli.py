"""Harbor's gemini-cli for task images that already have Gemini CLI.

Export the tasks with Gemini CLI built in and run them with this class:

    python3 tools/export_harbor_tasks.py --network public --preinstall gemini-cli
    GEMINI_FORCE_OAUTH=1 PYTHONPATH=agentic/harbor harbor run --agent razavi_gemini_cli:RazaviGeminiCli ...

Harbor's own install fetches nvm from GitHub, Node from nodejs.org and Gemini CLI
from npm on every run, which fails on an unreliable connection. When `gemini` is
already on the image's PATH this class skips that and writes only the settings
file Harbor's install writes; otherwise it falls back to Harbor's install.
Harbor's run command sources nvm only if it exists, so it finds the built-in
gemini. Gemini CLI reads the task's figures from /app itself, as images.
"""

from __future__ import annotations

from typing import Any

from harbor.agents.installed.gemini_cli import GeminiCli

# The settings file Harbor's GeminiCli.install writes after installing Gemini CLI.
SETTINGS_COMMAND = (
    "mkdir -p ~/.gemini && "
    "cat > ~/.gemini/settings.json << 'SETTINGS'\n"
    '{\n  "experimental": {\n    "skills": true\n  }\n}\n'
    "SETTINGS"
)


class RazaviGeminiCli(GeminiCli):
    async def install(self, environment: Any) -> None:
        if (await environment.exec("command -v gemini >/dev/null 2>&1")).return_code != 0:
            await super().install(environment)
            return
        await self.exec_as_agent(environment, SETTINGS_COMMAND)
        await self.exec_as_agent(environment, "gemini --version")
