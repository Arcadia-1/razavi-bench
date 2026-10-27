from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import run_agentic_miniswe as AGENTIC
from direct_qa_openrouter_common import REPO_ROOT, load_tasks


class AgenticMiniSweTests(unittest.TestCase):
    def test_task_text_attaches_every_figure_and_no_solution(self) -> None:
        for task in load_tasks(REPO_ROOT):
            text = AGENTIC.task_text(REPO_ROOT, task, "ngspice-sky130")
            self.assertEqual(text.count("<MSWEA_MULTIMODAL_CONTENT>"), len(task["figures"]), task["task_slug"])
            self.assertIn("/app/answer.md", text)
            self.assertIn("/app/.claude/skills/ngspice-sky130/SKILL.md", text)
            self.assertNotIn(task["golden_solution"].strip()[-80:], text)

    def test_multimodal_mode_does_not_mention_the_simulator(self) -> None:
        task = load_tasks(REPO_ROOT, ["part1-008-source-follower"])[0]
        text = AGENTIC.task_text(REPO_ROOT, task, "multimodal")
        self.assertNotIn("ngspice", text)
        self.assertIn("data:image/png;base64,", text)

    def test_build_context_holds_only_public_files(self) -> None:
        for mode in AGENTIC.MODES:
            files = AGENTIC.context_files(REPO_ROOT, mode)
            self.assertEqual(files[0], AGENTIC.MODES[mode]["dockerfile"])
            for relative in files:
                self.assertFalse(relative.startswith(("tasks/", "netlists/", "data/", "experiments/")), relative)
                self.assertNotIn("golden", relative)

    def test_strip_images_removes_inline_figures(self) -> None:
        url = "data:image/png;base64,iVBORw0KGgo="
        value = {"content": [{"type": "image_url", "image_url": {"url": url}}, {"type": "text", "text": f"see {url} here"}]}
        stripped = AGENTIC.strip_images(value)
        self.assertEqual(stripped["content"][0]["image_url"]["url"], "<image omitted>")
        self.assertEqual(stripped["content"][1]["text"], "see <image omitted> here")

    def test_usage_totals_counts_every_billed_call(self) -> None:
        messages = [
            {"role": "user", "content": "task"},
            {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "prompt_cache_hit_tokens": 4, "completion_tokens_details": {"reasoning_tokens": 3}}}}},
            {"role": "user", "extra": {"response": {"usage": {"prompt_tokens": 20, "completion_tokens": 1, "total_tokens": 21, "cost": 0.5, "prompt_tokens_details": {"cached_tokens": 8}}}}},
            {"role": "tool", "extra": {"raw_output": "ok"}},
        ]
        totals = AGENTIC.usage_totals(messages)
        self.assertEqual(totals["model_calls"], 2)
        self.assertEqual(totals["total_tokens"], 36)
        self.assertEqual(totals["cached_tokens"], 12)
        self.assertEqual(totals["reasoning_tokens"], 3)
        self.assertEqual(totals["cost"], 0.5)

    def test_only_simulator_runs_count_as_ngspice_commands(self) -> None:
        runs = ["ngspice -b /app/sf.cir > /app/sf.log 2>&1", "cd /app && ngspice --version", "python3 /app/.claude/skills/ngspice-sky130/assets/run_op_probe.py --template nfet_op", "python3 -c \"subprocess.run(['ngspice', '-b', 'x.cir'])\""]
        reads = ["cat /app/.claude/skills/ngspice-sky130/SKILL.md", "ls /tools/ngspice-sky130/models", "cat /app/sf.ngspice.log"]
        for command in runs:
            self.assertTrue(AGENTIC.SIMULATION_RE.search(command), command)
        for command in reads:
            self.assertFalse(AGENTIC.SIMULATION_RE.search(command), command)

    def test_model_kwargs_follow_each_provider_format(self) -> None:
        openrouter = argparse.Namespace(model="google/example", effort="high", max_tokens=None, provider="openrouter")
        self.assertEqual(AGENTIC.model_kwargs(openrouter), {"reasoning": {"effort": "high"}})
        deepseek = argparse.Namespace(model="deepseek-flash", effort="max", max_tokens=1024, provider="deepseek")
        self.assertEqual(AGENTIC.model_kwargs(deepseek), {"thinking": {"type": "enabled"}, "reasoning_effort": "max", "max_tokens": 1024})


if __name__ == "__main__":
    unittest.main()
