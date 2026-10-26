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

    def test_call_model_retries_a_truncated_answer(self) -> None:
        truncated = {
            "model": "google/example",
            "choices": [{"message": {"content": ""}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 128, "total_tokens": 130},
        }
        complete = {
            "model": "google/example",
            "choices": [{"message": {"content": "answer"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
        }
        with mock.patch.object(COMMON, "post_json", side_effect=[truncated, complete]), mock.patch.object(COMMON.time, "sleep"):
            result = DIRECT.call_model("https://example.test/v1/chat/completions", "not-a-real-key", {}, 5, 3)
        self.assertTrue(result["ok"])
        self.assertEqual(result["answer"], "answer")
        self.assertEqual([a["finish_reason"] for a in result["attempts"]], ["length", "stop"])
        with mock.patch.object(COMMON, "post_json", return_value=truncated) as post, mock.patch.object(COMMON.time, "sleep"):
            result = DIRECT.call_model("https://example.test/v1/chat/completions", "not-a-real-key", {}, 5, 2)
        self.assertFalse(result["ok"])
        self.assertEqual(post.call_count, 2)

    def test_resolve_effort_checks_the_listed_efforts(self) -> None:
        muse = {"supported_efforts": ["max", "xhigh", "high", "medium", "low", "minimal"]}
        mistral = {"supported_efforts": ["high", "none"]}
        self.assertEqual(COMMON.resolve_effort("top", muse), ("max", None))
        self.assertEqual(COMMON.resolve_effort("max", muse), ("max", None))
        effort, notice = COMMON.resolve_effort("xhigh", muse)
        self.assertEqual(effort, "xhigh")
        self.assertIn("below", notice)
        with self.assertRaisesRegex(ValueError, "not supported"):
            COMMON.resolve_effort("max", mistral)
        self.assertEqual(COMMON.resolve_effort("top", mistral), ("high", None))
        with self.assertRaisesRegex(ValueError, "does not expose"):
            COMMON.resolve_effort("high", None)
        self.assertEqual(COMMON.resolve_effort("default", None)[0], "default")
        self.assertEqual(COMMON.resolve_effort("high", {"supported_efforts": None}), ("high", None))

    def test_check_effort_rewrites_top_before_any_call(self) -> None:
        args = argparse.Namespace(skip_effort_check=False, provider="openrouter", base_url="https://openrouter.ai/api", model="meta/example", effort="top")
        with mock.patch.object(DIRECT, "model_reasoning", return_value={"supported_efforts": ["max", "high"]}):
            report = DIRECT.check_effort(args)
        self.assertEqual(args.effort, "max")
        self.assertEqual(report["supported_efforts"], ["max", "high"])
        skipped = argparse.Namespace(skip_effort_check=True, effort="high")
        self.assertFalse(DIRECT.check_effort(skipped)["checked"])

    def test_deepseek_sends_its_own_effort_fields(self) -> None:
        body = COMMON.payload("deepseek-flash", [{"type": "text", "text": "q"}], "max", 128, "deepseek")
        self.assertEqual(body["thinking"], {"type": "enabled"})
        self.assertEqual(body["reasoning_effort"], "max")
        self.assertNotIn("reasoning", body)
        args = argparse.Namespace(skip_effort_check=False, provider="deepseek", base_url="https://api.deepseek.com", model="deepseek-flash", effort="top")
        self.assertEqual(DIRECT.check_effort(args)["effort"], "max")
        bad = argparse.Namespace(skip_effort_check=False, provider="deepseek", base_url="https://api.deepseek.com", model="deepseek-flash", effort="xhigh")
        with self.assertRaisesRegex(ValueError, "not supported"):
            DIRECT.check_effort(bad)

    def test_nvidia_switches_nemotron_thinking_through_the_chat_template(self) -> None:
        body = COMMON.payload("nvidia/nemotron", [{"type": "text", "text": "q"}], "high", 128, "nvidia")
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": True})
        self.assertEqual((body["temperature"], body["top_p"]), (1.0, 0.95))
        medium = COMMON.payload("nvidia/nemotron", [], "medium", 128, "nvidia")
        self.assertTrue(medium["chat_template_kwargs"]["medium_effort"])
        args = argparse.Namespace(skip_effort_check=False, provider="nvidia", base_url=None, model="nvidia/nemotron", effort="top")
        self.assertEqual(DIRECT.check_effort(args)["effort"], "high")

    def test_moonshot_sends_reasoning_effort_only(self) -> None:
        body = COMMON.payload("kimi-model", [{"type": "text", "text": "q"}], "max", 128, "moonshot")
        self.assertEqual(body["reasoning_effort"], "max")
        self.assertNotIn("thinking", body)
        self.assertNotIn("reasoning", body)
        self.assertEqual(COMMON.payload("MiniMax-M", [], "max", 128, "minimax")["reasoning_effort"], "max")
        top = argparse.Namespace(skip_effort_check=False, provider="minimax", base_url=None, model="MiniMax-M", effort="top")
        self.assertEqual(DIRECT.check_effort(top)["effort"], "max")
        bad = argparse.Namespace(skip_effort_check=False, provider="moonshot", base_url=None, model="kimi-model", effort="ultra")
        with self.assertRaisesRegex(ValueError, "not supported"):
            DIRECT.check_effort(bad)

    def test_minimax_streams_and_reassembles_the_answer(self) -> None:
        body = COMMON.payload("MiniMax-M", [], "max", 128, "minimax")
        self.assertTrue(body["stream"])
        self.assertEqual(body["stream_options"], {"include_usage": True})
        self.assertFalse(COMMON.payload("deepseek-flash", [], "max", 128, "deepseek")["stream"])
        events = [
            b'data: {"model":"MiniMax-M","choices":[{"delta":{"reasoning_content":"thinking"}}]}\n',
            b'data: {"model":"MiniMax-M","choices":[{"delta":{"content":"ans"}}]}\n',
            b'data: {"model":"MiniMax-M","choices":[{"delta":{"content":"wer"},"finish_reason":"stop"}]}\n',
            b'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":7,"total_tokens":12}}\n',
            b'data: [DONE]\n',
        ]
        response = mock.MagicMock()
        response.__enter__.return_value = iter(events)
        with mock.patch.object(COMMON.urllib.request, "urlopen", return_value=response):
            result = DIRECT.call_model("https://api.minimaxi.com/v1/chat/completions", "not-a-real-key", body, 5, 1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["answer"], "answer")
        self.assertEqual(result["usage"]["total_tokens"], 12)

    def test_deepseek_cache_hits_become_cached_input_tokens(self) -> None:
        body = {
            "model": "deepseek-flash",
            "choices": [{"message": {"content": "answer"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 3, "total_tokens": 103, "prompt_cache_hit_tokens": 64},
        }
        with mock.patch.object(COMMON, "post_json", return_value=body):
            result = DIRECT.call_model("https://api.deepseek.com/v1/chat/completions", "not-a-real-key", {}, 5, 1)
        self.assertEqual(result["usage"]["prompt_tokens_details"]["cached_tokens"], 64)

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
