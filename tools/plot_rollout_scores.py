#!/usr/bin/env python3
"""Plot every model's Overall / Part 1 / Part 2 active score with its rollouts.

Reads docs/data/direct_qa/index.json and writes two figures:
docs/assets/direct_qa_rollout_mean_all_metrics.png (the README figure), where
each model gets three bars, Overall (solid), Part 1 (lighter) and Part 2
(hatched), and docs/assets/direct_qa_rollout_mean_overall.png, with only the
Overall bar. Every bar has one dot per rollout and a black line across the
rollout range. Models follow index order, which is sorted by the overall
active score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "docs/data/direct_qa/index.json"
DEFAULT_OUTPUT = ROOT / "docs/assets/direct_qa_rollout_mean_all_metrics.png"
DEFAULT_OVERALL_OUTPUT = ROOT / "docs/assets/direct_qa_rollout_mean_overall.png"

# Shades per provider; models from the same provider take the next shade in rank order.
PROVIDER_SHADES = {
    "anthropic": ["#E08A2E", "#C0501F", "#D96B2B", "#B8662A", "#E9A15B", "#A9441E", "#F0B36F"],
    "openai": ["#1E8449", "#2E9E6B", "#127A5B", "#3FA86E", "#0F6E4E", "#56B98A", "#2B7F9E"],
    "google": ["#2D5FD3", "#3F7FE0", "#1F4FB8", "#5C95E8", "#2B6CC4", "#7AA9EE"],
    "qwen": ["#138C83", "#1FA89B", "#0E766E", "#3BBFAE", "#5ED6C6"],
    "alibaba": ["#138C83", "#1FA89B", "#0E766E", "#3BBFAE", "#5ED6C6"],
    "xai": ["#1F2937", "#4B5563"],
    "moonshot": ["#6D48C8", "#8B6BD6"],
    "thinkingmachines": ["#C21E56", "#D94A7A"],
    "stepfun": ["#8B3FE0"],
    "minimax": ["#D04F5F"],
    "meta": ["#8B1E1E"],
    "bytedance": ["#D97706"],
}
FALLBACK = "#64748B"

W = 1600
BAR_X1 = 1437
HEADER_H = 58
PART_LABELS = {"overall": "Overall", "part1": "Part 1", "part2": "Part 2"}
INK, MUTED, FAINT, LINE = "#0B1220", "#475467", "#667085", "#E4E7EC"


def lighten(color: str, amount: float) -> tuple[float, float, float]:
    r, g, b = to_rgb(color)
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


def rollout_values(summary: dict, part: str) -> list[float]:
    rows = summary["by_rollout"] if part == "overall" else summary.get("by_rollout_part", {}).get(part, {})
    return [rows[k]["score_percent"] for k in sorted(rows, key=int)]


def plot(index: dict, output: Path, parts: tuple[str, ...]) -> None:
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
    models = index["models"]
    judge = index["benchmark"]["active_score_policy"]
    judge_name = {"deepseek_v4_pro": "DeepSeek V4 Pro", "minimax_m3": "MiniMax M3"}.get(judge, judge)
    # Three labelled bars per model, or one unlabelled Overall bar per model.
    stacked = len(parts) > 1
    bar_x0, block_h, panel_top = (500, 138, 247) if stacked else (437, 66, 222)
    body_top = panel_top + HEADER_H
    body_bottom = body_top + block_h * len(models)
    panel_bottom = body_bottom + 62
    height = panel_bottom + 120

    fig = plt.figure(figsize=(W / 100, height / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W)
    ax.set_ylim(height, 0)
    ax.axis("off")
    x_of = lambda pct: bar_x0 + (BAR_X1 - bar_x0) * max(0.0, min(pct, 100.0)) / 100

    ax.text(55, 62, "Razavi-Bench: Multimodal QA", fontsize=44, fontweight="bold", color=INK, va="center")
    if stacked:
        ax.text(55, 125, "Overall / Part 1 / Part 2", fontsize=21, fontweight="bold", color=INK, va="center")
        lines = ("Overall is solid, Part 1 is lighter, and Part 2 is hatched. Black lines show rollout min-to-max.",
                 f"Dots show three rollouts. Scores come from the {judge_name} judge; models are sorted by Overall.")
    else:
        lines = ("Solid bars show three-rollout means; black lines show min-to-max; dots show the three rollouts.",
                 f"Scores come from the {judge_name} judge; models are sorted by Overall.")
    for j, line in enumerate(lines):
        ax.text(55, panel_top - 75 + j * 34, line, fontsize=14, color=MUTED, va="center")

    ax.add_patch(Rectangle((40, panel_top), 1520, panel_bottom - panel_top, fill=False, edgecolor="#D0D5DD", lw=1.2))
    ax.text(73, panel_top + 36, "MODEL", fontsize=11, fontweight="bold", color=FAINT, va="center")
    ax.text(bar_x0, panel_top + 36, "SCORE", fontsize=11, fontweight="bold", color=FAINT, va="center")
    ax.plot([40, 1560], [body_top, body_top], color="#D0D5DD", lw=1)
    for pct in (25, 50, 75, 100):
        ax.plot([x_of(pct)] * 2, [body_top, body_bottom + 8], color=LINE, lw=1, zorder=0)

    used: dict[str, int] = {}
    for i, model in enumerate(models):
        top = body_top + i * block_h
        if i:
            ax.plot([40, 1560], [top, top], color=LINE, lw=1)
        provider = (model.get("provider") or "").lower()
        shades = PROVIDER_SHADES.get(provider, [FALLBACK])
        color = shades[used.get(provider, 0) % len(shades)]
        used[provider] = used.get(provider, 0) + 1

        effort = model.get("thinking_effort") or "default"
        name_y = top + 58 if stacked else top + 23
        ax.text(73, name_y, model["display_name"], fontsize=17, fontweight="bold", color=INK, va="center")
        ax.text(73, name_y + 30, f"Thinking effort: {effort}", fontsize=11.5, color=FAINT, va="center")

        summary = model["summary"]
        for row, part in enumerate(parts):
            y = top + 38 + row * 32 if stacked else top + 33
            half = 10 if stacked else 11.5
            mean = summary["scores"][part]["active"]["score_percent"]
            if stacked:
                ax.text(bar_x0 - 24, y, PART_LABELS[part], fontsize=12.5, color=MUTED, ha="right", va="center")
            width = x_of(mean) - bar_x0
            if part == "overall":
                ax.add_patch(Rectangle((bar_x0, y - half), width, 2 * half, facecolor=color, edgecolor="none"))
            elif part == "part1":
                ax.add_patch(Rectangle((bar_x0, y - half), width, 2 * half, facecolor=lighten(color, 0.45), edgecolor="none"))
            else:
                ax.add_patch(Rectangle((bar_x0, y - half), width, 2 * half, facecolor="white", edgecolor=color, lw=1.2, hatch="////"))
            rolls = rollout_values(summary, part)
            if len(rolls) > 1:
                ax.plot([x_of(min(rolls)), x_of(max(rolls))], [y, y], color=INK, lw=2, zorder=3, solid_capstyle="butt")
            ax.scatter([x_of(v) for v in rolls], [y] * len(rolls), s=60, color=color, edgecolors="white", linewidths=1.2, zorder=4)
            ax.text(1463, y, f"{mean:.1f}%", fontsize=14, fontweight="bold", color=INK, va="center")

    ax.plot([bar_x0, BAR_X1], [body_bottom + 8, body_bottom + 8], color="#98A2B3", lw=1)
    for pct in (0, 25, 50, 75, 100):
        ax.text(x_of(pct), body_bottom + 40, f"{pct}%", fontsize=12, color=FAINT, ha="center", va="center")

    notes = [
        f"Scores are per-rollout means of the {judge_name} judge's 0-4 scores.",
        '[1] B. Razavi, "Analog Design Experiments With AI--Part 1," IEEE Solid-State Circuits Magazine, Fall 2025.',
        '[2] B. Razavi, "Analog Design Experiments With AI--Part 2," IEEE Solid-State Circuits Magazine, Spring 2026.',
    ]
    for j, note in enumerate(notes):
        ax.text(60, panel_bottom + 26 + j * 28 + (6 if j else 0), note, fontsize=11 if j == 0 else 10, color=FAINT, va="center")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=100, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Overall / Part 1 / Part 2 figure")
    parser.add_argument("--overall-output", type=Path, default=DEFAULT_OVERALL_OUTPUT, help="Overall-only figure")
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    for output, parts in ((args.output, tuple(PART_LABELS)), (args.overall_output, ("overall",))):
        plot(index, output, parts)
        print(f"Wrote {output.resolve().relative_to(ROOT)}")


if __name__ == "__main__":
    main()
