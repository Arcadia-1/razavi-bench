#!/usr/bin/env python3
"""Harbor verifier: grade /app/answer.md and write the reward.

tools/export_harbor_tasks.py copies this into each task's tests/, together with
tools/evaluate_answers.py, the rubric and the task's golden solution under
/tests/repo, and the judge settings in /tests/judge.json. The verifier runs in
its own container, so the golden solution never reaches the agent's.

The reward is the judge's score_0_to_4 divided by 4. A missing or empty answer
scores 0 without a judge call; a judge that returns no score fails the
verifier rather than recording a wrong reward.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TESTS = Path("/tests")
ANSWER = Path("/app/answer.md")
VERIFIER = Path("/logs/verifier")


def main() -> int:
    judge = json.loads((TESTS / "judge.json").read_text(encoding="utf-8"))
    VERIFIER.mkdir(parents=True, exist_ok=True)
    answer = ANSWER.read_text(encoding="utf-8") if ANSWER.exists() else ""
    (VERIFIER / "answer.md").write_text(answer, encoding="utf-8")
    if not answer.strip():
        (VERIFIER / "reward.json").write_text(json.dumps({"reward": 0, "score_0_to_4": 0}) + "\n")
        return 0

    answers = VERIFIER / "judge_input.jsonl"
    scores = VERIFIER / "score.jsonl"
    answers.write_text(json.dumps({"task_path": judge["task_path"], "answer": answer}, ensure_ascii=False) + "\n", encoding="utf-8")
    subprocess.run(
        [
            sys.executable, str(TESTS / "evaluate_answers.py"),
            "--repo", str(TESTS / "repo"),
            "--input", str(answers),
            "--output", str(scores),
            "--api-url", judge["api_url"],
            "--model", judge["model"],
            "--api-key-env", judge["api_key_env"],
            "--json-mode",
            "--reasoning-effort", judge["reasoning_effort"],
            "--max-tokens", str(judge["max_tokens"]),
            "--timeout", str(judge["timeout"]),
            "--concurrency", "1",
        ],
        check=True,
    )
    score = json.loads(scores.read_text(encoding="utf-8").splitlines()[0]).get("score_0_to_4")
    if score is None:
        print("the judge returned no score; see score.jsonl", file=sys.stderr)
        return 1
    (VERIFIER / "reward.json").write_text(json.dumps({"reward": score / 4, "score_0_to_4": score}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
