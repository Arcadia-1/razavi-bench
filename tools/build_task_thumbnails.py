#!/usr/bin/env python3
"""Build the small figure previews shown on the homepage task cards.

Reads docs/data/tasks.jsonl, shrinks each task's first figure into
docs/assets/task-thumbs/<task_slug>.webp and writes
docs/data/task_thumbnails.json, which maps each slug to its preview and
pixel size so the page can reserve space before the image loads.

Requires Pillow. Re-run after adding or changing task figures.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TASKS = DOCS / "data" / "tasks.jsonl"
THUMB_DIR = DOCS / "assets" / "task-thumbs"
INDEX = DOCS / "data" / "task_thumbnails.json"

# Cards are about 240-330 CSS px wide; 2x that keeps line art sharp on retina screens.
MAX_WIDTH = 600
MAX_HEIGHT = 480
QUALITY = 88


def build() -> dict[str, dict[str, object]]:
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    index: dict[str, dict[str, object]] = {}
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        task = json.loads(line)
        figures = task.get("figures") or []
        if not figures:
            continue
        slug = task["task_slug"]
        with Image.open(DOCS / figures[0]) as source:
            image = source.convert("RGBA")
        # Flatten transparency onto white so previews match the printed figures.
        flat = Image.new("RGB", image.size, "white")
        flat.paste(image, mask=image.getchannel("A"))
        flat.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
        out = THUMB_DIR / f"{slug}.webp"
        flat.save(out, "WEBP", quality=QUALITY, method=6)
        index[slug] = {
            "src": out.relative_to(DOCS).as_posix(),
            "width": flat.width,
            "height": flat.height,
        }
    return dict(sorted(index.items()))


def main() -> None:
    index = build()
    INDEX.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(index)} previews to {THUMB_DIR.relative_to(ROOT)} and {INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
