#!/usr/bin/env python3
"""Batch 7: Claude Opus 5.5, Claude Opus 4.8, GPT-6 Astra, Muse Wonder Full 1.0 and Gemini 3.1 Pro.

Runs run.py's main() with these entries added to its ENTRIES (run.py itself is not edited, as it is
shared with the other batches), writing to batch7/. Every entry uses the highest reasoning effort
its OpenRouter listing supports (max; Gemini 3.1 Pro lists high, medium and low) and max_tokens equal
to its OpenRouter max_completion_tokens; temperature is left to the provider where the listing does
not support it, and Gemini 3.1 Pro keeps its published 0. The published runs used the same efforts.
Muse Wonder Full 1.0 was published through the local Muse Code CLI, whose system prompt this rerun
does not send; here it goes through OpenRouter (meta/muse-wonder, canonical slug
meta/muse-wonder-20261012), like every other API entry: one user message, question text and figure.

Usage: python3 run_batch7.py [run.py options other than --output-dir and --only]
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)

BATCH7 = {  # display name -> (OpenRouter model, effort, temperature, max_tokens)
    "Claude Opus 5.5": ("anthropic/claude-opus-5.5", "max", None, 128000),
    "Claude Opus 4.8": ("anthropic/claude-opus-4.8", "max", None, 128000),
    "GPT-6 Astra": ("openai/gpt-6-astra", "max", None, 128000),
    "Muse Wonder Full 1.0": ("meta/muse-wonder", "max", None, 943718),
    "Gemini 3.1 Pro": ("google/gemini-3.1-pro-preview", "high", 0.0, 65536),
}


def main() -> int:
    for name, entry in BATCH7.items():
        assert run.ENTRIES.get(name, entry) == entry, (name, run.ENTRIES[name])
        run.ENTRIES[name] = entry
        run.MODEL_OPTIONS[name] = {"provider": {"require_parameters": True}}
    sys.argv = [str(HERE / "run.py"), "--output-dir", str(HERE / "batch7"), "--export-selected",
                *[arg for name in BATCH7 for arg in ("--only", name)], *sys.argv[1:]]
    return run.main()


if __name__ == "__main__":
    raise SystemExit(main())
