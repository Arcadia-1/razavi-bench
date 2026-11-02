from __future__ import annotations

import unittest
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parents[1] / "agentic/harness"
# Repository paths an agent's image may hold. tasks/ only in a stage named "tasks" that
# deletes everything but each task's instruction and figures before the final stage copies it.
PUBLIC_SOURCES = {"tasks", "simulator/ngspice-sky130", "agentic/skills/ngspice-sky130"}
TASK_FILTER = "RUN find /benchmark/tasks -type f ! -name instruction.md ! -name 'figure-*.png' -delete"


class AgenticHarnessTests(unittest.TestCase):
    def test_images_copy_only_public_files(self) -> None:
        dockerfiles = sorted(HARNESS_DIR.glob("*.Dockerfile"))
        self.assertGreaterEqual(len(dockerfiles), 4)
        for dockerfile in dockerfiles:
            stage = ""
            text = dockerfile.read_text(encoding="utf-8")
            for line in text.splitlines():
                words = line.split()
                if words[:1] == ["FROM"]:
                    stage = words[3] if len(words) > 3 and words[2].upper() == "AS" else ""
                if words[:1] != ["COPY"] or any(word.startswith("--from=") for word in words):
                    continue
                for source in [word for word in words[1:-1] if not word.startswith("--")]:
                    self.assertIn(source, PUBLIC_SOURCES, f"{dockerfile.name}: {line}")
                    if source == "tasks":
                        self.assertEqual(stage, "tasks", f"{dockerfile.name}: {line}")
                        self.assertIn(TASK_FILTER, text, dockerfile.name)


if __name__ == "__main__":
    unittest.main()
