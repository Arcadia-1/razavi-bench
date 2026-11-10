#!/usr/bin/env python3
"""Batch 8: Claude Fable 5.2, a new entry (released 2026-11-09), run as every other API entry.

Runs run.py's main() (not edited, as it is shared with the other batches) with the entry added to
ENTRIES, writing to batch8/. Fable 5.2 has no published entry, so its key, claude_fable_52, is
added to the leaderboard index run.py reads, in memory only. Settings: OpenRouter
anthropic/claude-fable-5.2 (canonical slug anthropic/claude-fable-5.2-20261109), reasoning effort
max (the highest it lists), max_tokens 128,000 (its max_completion_tokens), provider-default
temperature (the listing has none); one user message with the question text and figure.

Usage: python3 run_batch8.py [run.py options other than --output-dir and --only]
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)

NAME, KEY = "Claude Fable 5.2", "claude_fable_52"
ENTRY = ("anthropic/claude-fable-5.2", "max", None, 128000)


class _JsonWithNewEntry:
    """json for run.py, whose only json.loads call reads the leaderboard index: add the new entry to it."""

    def __getattr__(self, name):
        return getattr(json, name)

    def loads(self, text, *args, **kwargs):
        data = json.loads(text, *args, **kwargs)
        if isinstance(data, dict) and isinstance(data.get("models"), list):
            assert all(m.get("display_name") != NAME for m in data["models"])
            data["models"].append({"display_name": NAME, "model_key": KEY})
        return data


def main() -> int:
    run.ENTRIES[NAME] = ENTRY
    run.MODEL_OPTIONS[NAME] = {"provider": {"require_parameters": True}}
    run.json = _JsonWithNewEntry()
    sys.argv = [str(HERE / "run.py"), "--output-dir", str(HERE / "batch8"), "--export-selected", "--only", NAME, *sys.argv[1:]]
    return run.main()


if __name__ == "__main__":
    raise SystemExit(main())
