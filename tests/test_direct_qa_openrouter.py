from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import direct_qa_openrouter as DIRECT
import direct_qa_openrouter_common as COMMON

MODULE_PATH = TOOLS_DIR / "direct_qa_openrouter.py"


class DirectQaOpenRouterTests(unittest.TestCase):
    def test_endpoint_and_payload_are_public(self) -> None:
        self.assertEqual(DIRECT.endpoint_for("https://openrouter.ai/api"), "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(DIRECT.endpoint_for("https://example.test/v1"), "https://example.test/v1/chat/completions")
        payload = DIRECT.build_payload(
            "google/example",
            [{"type": "text", "text": "hello"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}],
            "high",
            128,
        )
        self.assertEqual(payload["reasoning"], {"effort": "high"})
        self.assertFalse(payload["stream"])
        self.assertNotIn("vela", json.dumps(payload).lower())

    def test_call_model_accepts_chat_completion(self) -> None:
        body = {
            "model": "google/example",
            "choices": [{"message": {"content": "answer"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
        }
        with mock.patch.object(COMMON, "post_json", return_value=body) as post:
            result = DIRECT.call_model(
                "https://example.test/v1/chat/completions",
                "not-a-real-key",
                {"model": "google/example"},
                5,
                2,
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["answer"], "answer")
        self.assertEqual(result["usage"]["total_tokens"], 5)
        self.assertEqual(len(result["attempts"]), 1)
        post.assert_called_once()

    def test_canonicalize_creates_empty_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested" / "answers.jsonl"
            DIRECT.canonicalize(path)
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_text(encoding="utf-8"), "")

    def test_audit_passes_complete_records(self) -> None:
        task_slugs = list(DIRECT.DEFAULT_SMOKE_TASKS)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            args = argparse.Namespace(
                repo_root=DIRECT.REPO_ROOT,
                output_dir=output,
                output_prefix="test-model",
                effort="high",
                task_slug=task_slugs,
                rollout=[1],
            )
            tasks = DIRECT.load_tasks(DIRECT.REPO_ROOT, task_slugs)
            answer_path = output / "model_outputs" / "test-model-rollout-1.jsonl"
            raw_path = output / "raw_logs.jsonl"
            for index, task in enumerate(tasks):
                answer = f"answer-{index}"
                figures = list(task.get("figures") or [])
                DIRECT.append_jsonl(answer_path, {
                    "task_slug": task["task_slug"],
                    "rollout": 1,
                    "answer": answer,
                    "figures": figures,
                    "reasoning_effort": "high",
                })
                if index == 0:
                    DIRECT.append_jsonl(raw_path, {
                        "task_slug": task["task_slug"],
                        "rollout": 1,
                        "ok": False,
                        "answer": "",
                        "finish_reason": "",
                        "error": "transient failure",
                    })
                DIRECT.append_jsonl(raw_path, {
                    "task_slug": task["task_slug"],
                    "rollout": 1,
                    "ok": True,
                    "answer": answer,
                    "finish_reason": "stop",
                    "response_model": "google/example",
                    "request_summary": {"reasoning": {"effort": "high"}},
                    "images": [{"path": path} for path in figures],
                    "usage": {"total_tokens": 5},
                })
            report = DIRECT.audit(args)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["answer_records"], 2)

    def test_audit_detects_missing_raw_log(self) -> None:
        task_slugs = list(DIRECT.DEFAULT_SMOKE_TASKS)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            args = argparse.Namespace(
                repo_root=DIRECT.REPO_ROOT,
                output_dir=output,
                output_prefix="test-model",
                effort="high",
                task_slug=task_slugs,
                rollout=[1],
            )
            tasks = DIRECT.load_tasks(DIRECT.REPO_ROOT, task_slugs)
            answer_path = output / "model_outputs" / "test-model-rollout-1.jsonl"
            raw_path = output / "raw_logs.jsonl"
            for index, task in enumerate(tasks):
                answer = {"answer": f"answer-{index}", "figures": task.get("figures") or []}
                DIRECT.append_jsonl(answer_path, {
                    "task_slug": task["task_slug"],
                    "rollout": 1,
                    "answer": answer["answer"],
                    "figures": answer["figures"],
                    "reasoning_effort": "high",
                })
                if index == 0:
                    DIRECT.append_jsonl(raw_path, {
                        "task_slug": task["task_slug"],
                        "rollout": 1,
                        "ok": True,
                        "answer": answer["answer"],
                        "finish_reason": "stop",
                        "usage": {"total_tokens": 5},
                    })
            report = DIRECT.audit(args)
            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(item["reason"] == "invalid_raw_log" for item in report["failures"]))

    def test_source_has_no_internal_dependencies(self) -> None:
        paths = [MODULE_PATH, MODULE_PATH.with_name("direct_qa_openrouter_common.py"), MODULE_PATH.with_name("run_deepseek_v4_pro.py")]
        for path in paths:
            source = path.read_text(encoding="utf-8")
            for forbidden in ("minimax_vela_sdk", "VELA_TOKEN", "/home/", "vela_model_id"):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
