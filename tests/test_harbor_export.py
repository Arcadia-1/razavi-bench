from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import export_harbor_tasks as EXPORT
import run_agentic_miniswe as AGENTIC
from direct_qa_openrouter_common import REPO_ROOT, load_tasks


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WRAPPER = load(ROOT / "agentic/harbor/mini_with_figures.py")
GRADE = load(ROOT / "agentic/harbor/grade.py")


def export_args(output_dir: Path, mode: str = "ngspice-sky130", network: str = "allowlist") -> argparse.Namespace:
    return argparse.Namespace(
        mode=mode, network=network, output_dir=output_dir, agent_timeout=3600, verifier_timeout=2400,
        judge_api_url="https://openrouter.ai/api/v1/chat/completions", judge_model="openai/gpt-6-luna",
        judge_key_env="OPENROUTER_API_KEY", judge_effort="max", judge_max_tokens=128000, judge_timeout=1800,
    )


class HarborExportTests(unittest.TestCase):
    def test_wrapper_gives_the_agent_the_runner_task(self) -> None:
        """Inside the container the figures land where the direct runner puts them."""
        for slug in ("part1-008-source-follower", "part1-001-double-length-and-width-mosfet-its-intrinsic"):
            task = load_tasks(REPO_ROOT, [slug])[0]
            with tempfile.TemporaryDirectory() as app:
                for relative in task["figures"]:
                    shutil.copy2(REPO_ROOT / relative, Path(app) / Path(relative).name)
                instruction = AGENTIC.task_text(REPO_ROOT, task, "ngspice-sky130", attach_figures=False)
                self.assertEqual(WRAPPER.with_figures(instruction, Path(app)), AGENTIC.task_text(REPO_ROOT, task, "ngspice-sky130"))

    def test_export_keeps_answers_in_the_verifier(self) -> None:
        task = load_tasks(REPO_ROOT, ["part1-008-source-follower"])[0]
        with tempfile.TemporaryDirectory() as tmp:
            target = EXPORT.export_task(REPO_ROOT, task, export_args(Path(tmp)))
            golden = (REPO_ROOT / task["task_path"] / "golden_solution.md").read_text(encoding="utf-8")
            agent_side = [path for path in (target / "environment").rglob("*") if path.is_file()] + [target / "instruction.md"]
            for path in agent_side:
                self.assertNotIn(path.name, ("golden_solution.md", "evaluation_rubric.md", "judge.json"), path)
                if path.suffix in (".md", ".py", ".json", ""):
                    self.assertNotIn(golden.strip(), path.read_text(encoding="utf-8", errors="ignore"), path)
            self.assertEqual((target / "tests/repo" / task["task_path"] / "golden_solution.md").read_text(encoding="utf-8"), golden)
            self.assertNotIn("<MSWEA_MULTIMODAL_CONTENT>", (target / "instruction.md").read_text(encoding="utf-8"))
            self.assertEqual(sorted(path.name for path in (target / "environment/task").iterdir()), ["figure-05.png", "instruction.md"])
            dockerfile = (target / "environment/Dockerfile").read_text(encoding="utf-8")
            self.assertTrue(dockerfile.startswith((REPO_ROOT / AGENTIC.MODES["ngspice-sky130"]["dockerfile"]).read_text(encoding="utf-8")))
            self.assertTrue(dockerfile.rstrip().endswith("COPY task/ /app/"))
            # Harbor runs the verifier in the task's workdir, so its image must have /app.
            self.assertIn("WORKDIR /app", (target / "tests/Dockerfile").read_text(encoding="utf-8"))

    def test_task_toml_isolates_the_agent_and_the_verifier(self) -> None:
        task = load_tasks(REPO_ROOT, ["part1-008-source-follower"])[0]
        with tempfile.TemporaryDirectory() as tmp:
            target = EXPORT.export_task(REPO_ROOT, task, export_args(Path(tmp)))
            config = tomllib.loads((target / "task.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["artifacts"], ["/app/answer.md"])
        self.assertEqual(config["verifier"]["environment_mode"], "separate")
        self.assertEqual(config["verifier"]["allowed_hosts"], ["openrouter.ai"])
        self.assertEqual(config["verifier"]["env"], {"OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"})
        self.assertEqual((config["agent"]["network_mode"], config["agent"]["allowed_hosts"]), ("allowlist", []))
        self.assertEqual(config["metadata"]["figures"], task["figures"])

    def test_public_export_asks_the_agent_not_to_use_the_internet(self) -> None:
        task = load_tasks(REPO_ROOT, ["part1-008-source-follower"])[0]
        with tempfile.TemporaryDirectory() as tmp:
            target = EXPORT.export_task(REPO_ROOT, task, export_args(Path(tmp), network="public"))
            config = tomllib.loads((target / "task.toml").read_text(encoding="utf-8"))
            instruction = (target / "instruction.md").read_text(encoding="utf-8")
        self.assertEqual((config["agent"]["network_mode"], config["verifier"]["network_mode"]), ("public", "public"))
        self.assertNotIn(EXPORT.NO_INTERNET, instruction)
        self.assertIn(EXPORT.NO_INTERNET_REQUEST, instruction)

    def test_grader_scores_a_missing_answer_zero_without_the_judge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tests, verifier = Path(tmp) / "tests", Path(tmp) / "logs/verifier"
            tests.mkdir()
            (tests / "judge.json").write_text(json.dumps({"task_path": "tasks/x"}), encoding="utf-8")
            with mock.patch.multiple(GRADE, TESTS=tests, ANSWER=Path(tmp) / "app/answer.md", VERIFIER=verifier), mock.patch.object(GRADE.subprocess, "run") as run:
                self.assertEqual(GRADE.main(), 0)
            run.assert_not_called()
            self.assertEqual(json.loads((verifier / "reward.json").read_text()), {"reward": 0, "score_0_to_4": 0})


if __name__ == "__main__":
    unittest.main()
