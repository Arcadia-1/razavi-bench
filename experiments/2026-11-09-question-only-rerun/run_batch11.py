#!/usr/bin/env python3
"""Batch 11: Gemini 4 Carbon, a new entry (released 2026-11-10), run as every other API entry.

Runs run.py's main() (not edited, as it is shared with the other batches) with the entry added to
ENTRIES, writing to batch11/. Gemini 4 Carbon has no published entry, so its key, gemini_4_carbon, is
added to the leaderboard index run.py reads, in memory only. Settings: OpenRouter
google/gemini-4-carbon (canonical slug google/gemini-4-carbon-20261110), reasoning effort
high (the highest it lists), max_tokens 943,718 (its max_completion_tokens), temperature 0
as for Gemini 4 Argon; one user message with the question text and figure.

Usage: python3 run_batch11.py [run.py options other than --output-dir and --only]
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

NAME, KEY = "Gemini 4 Carbon", "gemini_4_carbon"
ENTRY = ("google/gemini-4-carbon", "high", 0.0, 943718)


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
    sys.argv = [str(HERE / "run.py"), "--output-dir", str(HERE / "batch11"), "--export-selected", "--only", NAME, *sys.argv[1:]]
    return run.main()


if __name__ == "__main__":
    raise SystemExit(main())
