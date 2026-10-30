#!/usr/bin/env python3
"""Start mini-swe-agent with the task's figures attached as images.

Harbor hands mini-swe-agent the task as one command-line argument, and a
figure's base64 is larger than Linux lets one argument be. This script takes
mini-swe-agent's own arguments, adds every /app/figure-*.png to --task as a
mini-swe-agent multimodal tag, and runs mini-swe-agent in this process, so the
images never pass through a command line. The figures go right after the
question, before the task's "## Environment" section.

It runs inside the task container with mini-swe-agent's own Python, so it uses
only the standard library and mini-swe-agent.
"""

from __future__ import annotations

import base64
import mimetypes
import sys
from pathlib import Path

ENVIRONMENT_HEADING = "\n\n## Environment"


def figure_tag(path: Path) -> str:
    """mini-swe-agent expands this tag in a message into an image_url content part."""
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"<MSWEA_MULTIMODAL_CONTENT><CONTENT_TYPE>image_url</CONTENT_TYPE>data:{media_type};base64,{encoded}</MSWEA_MULTIMODAL_CONTENT>"


def with_figures(task: str, app_dir: Path = Path("/app")) -> str:
    figures = sorted(app_dir.glob("figure-*.png"))
    if not figures:
        return task
    section = "\n\n".join(
        ["## Attached Figures\n\nThe figures are shown below; the same PNG files are in /app.", *(f"{path.name}:\n{figure_tag(path)}" for path in figures)]
    )
    head, heading, tail = task.partition(ENVIRONMENT_HEADING)
    return f"{head}\n\n{section}{heading}{tail}" if heading else f"{task}\n\n{section}"


def main(argv: list[str]) -> None:
    args = ["--task=" + with_figures(arg.removeprefix("--task=")) if arg.startswith("--task=") else arg for arg in argv]
    from minisweagent.run.mini import app

    app(args=args, prog_name="mini-swe-agent")


if __name__ == "__main__":
    main(sys.argv[1:])
