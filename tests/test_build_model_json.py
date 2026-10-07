from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/2026-10-01-direct-qa"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


class BuildModelJsonTests(unittest.TestCase):
    def test_reproduces_the_gpt_6_1_sol_snapshot_build(self) -> None:
        """The generic builder must match the experiment-specific script it replaces."""
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "snapshot.json"
            generic = Path(tmp) / "generic.json"
            result = run(str(EXPERIMENT / "tools/build_model_json.py"), "--output", str(snapshot))
            self.assertEqual(result.returncode, 0, result.stderr)
            note = json.loads(snapshot.read_text(encoding="utf-8"))["configuration_note"]
            outputs = EXPERIMENT / "model_outputs"
            answers = []
            for rollout in (1, 2, 3):
                answers += ["--answers", str(outputs / f"openrouter-gpt-6-1-sol-reasoning-max-rollout-{rollout}.jsonl")]
            result = run(
                "tools/build_model_json.py",
                "--model-key", "gpt_6_1_sol",
                "--display-name", "GPT-6.1 Sol",
                "--provider", "openai",
                "--effort", "max",
                "--api-model", "openai/gpt-6.1-sol",
                "--source-experiment", "2026-10-01-direct-qa-openrouter-gpt-6-1-sol-reasoning-max",
                "--configuration-note", note,
                *answers,
                "--scores", str(EXPERIMENT / "judge_outputs/openrouter-deepseek-v4-pro-no-thinking-20261001/openrouter-gpt-6-1-sol.scores.jsonl"),
                "--tokens", str(outputs / "openrouter-gpt-6-1-sol-tokens.json"),
                "--output", str(generic),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(generic.read_bytes(), snapshot.read_bytes())

    def test_usage_record_reads_openrouter_usage(self) -> None:
        spec = importlib.util.spec_from_file_location("build_model_json", ROOT / "tools/build_model_json.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        record = module.usage_record(
            {
                "prompt_tokens": 100,
                "completion_tokens": 40,
                "total_tokens": 140,
                "prompt_tokens_details": {"cached_tokens": 60},
                "completion_tokens_details": {"reasoning_tokens": 30},
            }
        )
        self.assertEqual(record["cached_input_tokens"], 60)
        self.assertEqual(record["reasoning_output_tokens"], 30)
        self.assertTrue(record["complete"])
        self.assertFalse(module.usage_record({"prompt_tokens": 1})["complete"])


if __name__ == "__main__":
    unittest.main()
