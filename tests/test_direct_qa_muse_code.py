from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import direct_qa_muse_code as MUSE


class MuseCodeRunnerTests(unittest.TestCase):
    def test_usage_is_read_from_the_session_log(self) -> None:
        call = {"payload": {"event": {"usage_family": "provider", "usage": {
            "input_tokens": 23000, "output_tokens": 13276, "cached_tokens": 0,
            "cache_read_tokens": 0, "reasoning_tokens": 12581}}}}
        tool = {"payload": {"usage_family": "tool", "usage": {"rss_self_bytes": 1}}}
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "2026/10/14/sid-1/session.jsonl"
            log.parent.mkdir(parents=True)
            log.write_text(json.dumps(tool) + "\n" + json.dumps(call) + "\n", encoding="utf-8")
            with mock.patch.object(MUSE, "SESSIONS", Path(tmp)):
                usages = MUSE.session_usages("sid-1")
        self.assertEqual(len(usages), 1)
        record = MUSE.openai_usage(usages[0])
        self.assertEqual(record["total_tokens"], 36276)
        self.assertEqual(record["completion_tokens_details"]["reasoning_tokens"], 12581)

    def test_lockdown_allows_one_model_step_and_no_tools(self) -> None:
        for flag in ("--disable-shell", "--disable-write", "--disable-web-tools", "--disable-reminders"):
            self.assertIn(flag, MUSE.LOCKDOWN)
        self.assertEqual(MUSE.LOCKDOWN[MUSE.LOCKDOWN.index("--max-model-steps") + 1], "1")


if __name__ == "__main__":
    unittest.main()
