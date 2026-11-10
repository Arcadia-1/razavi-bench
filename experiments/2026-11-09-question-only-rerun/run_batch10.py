#!/usr/bin/env python3
"""Batch 10: Claude Fable 5.1, run at the user's request after batch 9.

Runs run.py's main() with the entry added to its ENTRIES (run.py itself is not edited, as it is
shared with the other batches), writing to batch10/. Settings: OpenRouter anthropic/claude-fable-5.1,
reasoning effort max (the highest it lists, as published), max_tokens 128,000 (its
max_completion_tokens), provider-default temperature (the listing has none); one user message with
the question text and figure.

Usage: python3 run_batch10.py [run.py options other than --output-dir and --only]
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)

BATCH10 = {  # display name -> (OpenRouter model, effort, temperature, max_tokens)
    "Claude Fable 5.1": ("anthropic/claude-fable-5.1", "max", None, 128000),
}


def main() -> int:
    for name, entry in BATCH10.items():
        assert run.ENTRIES.get(name, entry) == entry, (name, run.ENTRIES[name])
        run.ENTRIES[name] = entry
        run.MODEL_OPTIONS[name] = {"provider": {"require_parameters": True}}
    sys.argv = [str(HERE / "run.py"), "--output-dir", str(HERE / "batch10"), "--export-selected",
                *[arg for name in BATCH10 for arg in ("--only", name)], *sys.argv[1:]]
    return run.main()


if __name__ == "__main__":
    raise SystemExit(main())
