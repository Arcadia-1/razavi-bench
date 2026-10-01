#!/usr/bin/env python3
"""Run the repository's public evaluator with DeepSeek V4 Pro defaults.

This launcher only sets public defaults and delegates to tools/evaluate_answers.py.
It does not import any private SDK or internal service, and it never handles an
API key itself; the evaluator reads the key from an environment variable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

EVALUATOR = Path(__file__).with_name("evaluate_answers.py")
DEFAULT_ARGS = (
    ("--api-url", "https://api.deepseek.com/chat/completions"),
    ("--api-format", "chat-completions"),
    ("--model", "deepseek-v4-pro"),
    ("--api-key-env", "DEEPSEEK_API_KEY"),
    ("--thinking-mode", "disabled"),
)


def has_option(argv: list[str], option: str) -> bool:
    return any(arg == option or arg.startswith(option + "=") for arg in argv)


def main() -> int:
    argv = sys.argv[1:]
    for option, value in DEFAULT_ARGS:
        if not has_option(argv, option):
            argv.extend((option, value))
    if not has_option(argv, "--json-mode"):
        argv.append("--json-mode")
    os.execv(sys.executable, [sys.executable, str(EVALUATOR), *argv])


if __name__ == "__main__":
    raise SystemExit(main())
