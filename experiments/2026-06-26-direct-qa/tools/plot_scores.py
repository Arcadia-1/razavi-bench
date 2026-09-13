#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import to_rgba
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath


DEFAULT_EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODEL_ORDER = ["claude", "gemini", "gpt"]
MODEL_LABELS = {
    "claude": ("Claude Opus 4.8", "Thinking Max"),
    "gemini": ("Gemini 3.1 Pro", "Thinking High"),
    "gpt": ("GPT-5.5", "Thinking XHigh"),
}
ROLLOUT_ORDER = [1, 2, 3]
PART_ORDER = ["part1_first_30", "part2_last_20", "all"]
PLOT_PART_ORDER = ["all", "part1_first_30", "part2_last_20"]
PART_LABELS = {
    "part1_first_30": "Part 1",
    "part2_last_20": "Part 2",
    "all": "Overall",
}
JUDGE_ORDER = ["minimax", "deepseek"]
JUDGE_LABELS = {
    "minimax": "MiniMax M3",
    "deepseek": "DeepSeek V4 Pro",
}
MODEL_COLORS = {
    "claude": "#C9651A",
    "gemini": "#2B7DD8",
    "gpt": "#2C9558",
}
METRIC_STYLES = {
    "all": {"alpha": 0.95, "hatch": None, "edge_alpha": 0.95},
    "part1_first_30": {"alpha": 0.56, "hatch": None, "edge_alpha": 0.56},
    "part2_last_20": {"alpha": 0.22, "hatch": "////", "edge_alpha": 0.80},
}
SUMMARY_FIELDS = [
    "judge_family",
    "source_judge_runs",
    "answer_model_family",
    "rollout",
    "part",
    "n_answers",
    "n_judgments",
    "avg_score_0_to_4",
    "avg_percent",
    "score_distribution",
]
TITLE_FONT = "Avenir Next"
BODY_FONT = "Helvetica Neue"
FALLBACK_FONT = "DejaVu Sans"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_summary(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise SystemExit(f"No rows found in {path}")
    return rows


def judge_family(row: dict, path: Path) -> str:
    label = f"{row.get('judge_model', '')} {path.name}".lower()
    if "minimax" in label:
        return "minimax"
    if "deepseek" in label:
        return "deepseek"
    raise ValueError(f"Unknown judge model for {path}: {row.get('judge_model')}")


def part_for_task(task_slug: str) -> str:
    if task_slug.startswith("part1-"):
        return "part1_first_30"
    if task_slug.startswith("part2-"):
        return "part2_last_20"
    raise ValueError(f"Unknown task part: {task_slug}")


def build_summary_rows(judge_output_dir: Path) -> list[dict]:
    buckets: dict[tuple[str, str, int, str], list[int]] = defaultdict(list)
    task_sets: dict[tuple[str, str, int, str], set[str]] = defaultdict(set)
    source_runs: dict[str, set[str]] = defaultdict(set)

    paths = sorted(judge_output_dir.glob("*.jsonl"))
    if not paths:
        raise SystemExit(f"No judge output JSONL files found in {judge_output_dir}")

    for path in paths:
        for row in load_jsonl(path):
            score = row.get("score_0_to_4")
            if score is None:
                continue
            judge = judge_family(row, path)
            model = row["answer_model_family"]
            rollout = int(row["rollout"])
            task_slug = row["task_slug"]
            part = part_for_task(task_slug)
            source_runs[judge].add(path.stem)
            for part_key in (part, "all"):
                key = (judge, model, rollout, part_key)
                buckets[key].append(int(score))
                task_sets[key].add(task_slug)

    rows = []
    for judge in JUDGE_ORDER:
        for model in MODEL_ORDER:
            for rollout in ROLLOUT_ORDER:
                for part in PART_ORDER:
                    key = (judge, model, rollout, part)
                    scores = buckets[key]
                    distribution = Counter(scores)
                    avg_score = sum(scores) / len(scores)
                    rows.append(
                        {
                            "judge_family": judge,
                            "source_judge_runs": ";".join(sorted(source_runs[judge])),
                            "answer_model_family": model,
                            "rollout": rollout,
                            "part": part,
                            "n_answers": len(task_sets[key]),
                            "n_judgments": len(scores),
                            "avg_score_0_to_4": round(avg_score, 6),
                            "avg_percent": round(avg_score / 4 * 100, 4),
                            "score_distribution": json.dumps(dict(sorted(distribution.items())), sort_keys=True),
                        }
                    )
    return rows


def write_summary(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def score_lookup(rows: list[dict]) -> dict[tuple[str, str, int, str], float]:
    values = {}
    for row in rows:
        key = (
            row["judge_family"],
            row["answer_model_family"],
            int(row["rollout"]),
            row["part"],
        )
        values[key] = float(row["avg_percent"])
    return values


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def pct(value: float) -> str:
    return f"{value:.1f}%"


def color_with_alpha(hex_color: str, alpha: float) -> tuple[float, float, float, float]:
    rgba = to_rgba(hex_color)
    return (rgba[0], rgba[1], rgba[2], alpha)


def available_font(candidates: list[str]) -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in candidates:
        if candidate in available:
            return candidate
    return FALLBACK_FONT


def text_width_fraction(text: str, font_family: str, size: float, weight: str, fig: plt.Figure) -> float:
    properties = FontProperties(family=font_family, size=size, weight=weight)
    width_points = TextPath((0, 0), text, prop=properties).get_extents().width
    return width_points / (fig.get_figwidth() * 72)


def draw_bullet_parts(
    ax: plt.Axes,
    fig: plt.Figure,
    x: float,
    y: float,
    parts: list[tuple[str, str]],
    font_family: str,
    fontsize: float = 14,
) -> None:
    current_x = x
    for text, weight in parts:
        display_text = text.rstrip()
        ax.text(
            current_x,
            y,
            display_text,
            ha="left",
            va="top",
            fontsize=fontsize,
            fontfamily=font_family,
            fontweight=weight,
            color="#5B6472",
        )
        current_x += text_width_fraction(display_text, font_family, fontsize, weight, fig)
        if display_text != text:
            current_x += 0.006


def source_run_count(rows: list[dict], judge: str) -> int:
    for row in rows:
        if row["judge_family"] == judge:
            runs = [run for run in row["source_judge_runs"].split(";") if run]
            return len(runs)
    return 0


def plot_scores_for_judge(
    rows: list[dict],
    judge: str,
    output_png: Path,
    output_svg: Path,
) -> None:
    scores = score_lookup(rows)
    body_font = available_font([BODY_FONT, TITLE_FONT])
    title_font = available_font([TITLE_FONT, BODY_FONT])

    plt.rcParams.update(
        {
            "font.family": body_font,
            "font.size": 12,
            "axes.unicode_minus": False,
        }
    )
    fig = plt.figure(figsize=(10, 10), dpi=220)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    outer_l, outer_r = 0.025, 0.975
    table_top = 0.680
    table_bottom = 0.155
    row_h = (table_top - table_bottom) / len(MODEL_ORDER)

    model_x = 0.045
    bar_l, bar_r = 0.330, 0.930

    ax.text(
        outer_l,
        0.972,
        "Razavi Bench",
        ha="left",
        va="top",
        fontsize=54,
        fontfamily=title_font,
        fontweight="heavy",
        color="#0B1220",
    )

    run_count = source_run_count(rows, judge)
    bullets: list[str | list[tuple[str, str]]] = [
        [
            ("Judge model: ", "bold"),
            (JUDGE_LABELS[judge], "bold"),
        ],
        "Bars show three-rollout means for Overall, Part 1 (30 questions), and Part 2 (20 questions).",
        "Black lines show rollout min-to-max; colored dots show rollout 1/2/3 on the same metric row.",
    ]
    bullet_y0 = 0.870
    bullet_gap = 0.034
    for i, text in enumerate(bullets):
        y = bullet_y0 - i * bullet_gap
        fontsize = 16 if i == 0 else 14
        ax.text(outer_l, y, "•", ha="left", va="top", fontsize=fontsize, color="#5B6472")
        if isinstance(text, list):
            draw_bullet_parts(ax, fig, outer_l + 0.018, y, text, body_font, fontsize=fontsize)
        else:
            ax.text(outer_l + 0.018, y, text, ha="left", va="top", fontsize=14, color="#5B6472")

    ax.add_patch(
        Rectangle(
            (outer_l, table_bottom - 0.045),
            outer_r - outer_l,
            table_top - table_bottom + 0.110,
            fill=False,
            edgecolor="#E1E3E6",
            linewidth=1.0,
        )
    )
    header_y = 0.715
    ax.text(model_x, header_y, "MODEL", ha="left", va="center", fontsize=12.5, color="#707070", fontweight="medium")
    ax.text(bar_l, header_y, "SCORE", ha="left", va="center", fontsize=12.5, color="#707070", fontweight="medium")
    ax.plot([outer_l, outer_r], [table_top, table_top], color="#E8E8E8", lw=1.0)

    for tick in [0, 0.25, 0.50, 0.75, 1.00]:
        x = bar_l + tick * (bar_r - bar_l)
        ax.plot([x, x], [table_bottom, table_top], color="#EEF1F5", lw=0.9, zorder=0)
        ax.text(x, table_bottom - 0.030, f"{tick:.2f}", ha="center", va="top", fontsize=10.5, color="#747474")

    bar_offsets = [0.050, 0.000, -0.050]
    bar_h = row_h * 0.115
    label_x = bar_l - 0.018

    for idx, model in enumerate(MODEL_ORDER):
        y_top = table_top - idx * row_h
        y_bottom = y_top - row_h
        y = (y_top + y_bottom) / 2
        color = MODEL_COLORS[model]
        model_name, thinking = MODEL_LABELS[model]

        ax.plot([outer_l, outer_r], [y_bottom, y_bottom], color="#EFEFEF", lw=0.9)
        ax.text(model_x, y + 0.014, model_name, ha="left", va="center", fontsize=15.0, color="#111827", fontweight="semibold")
        ax.text(model_x, y - 0.022, thinking, ha="left", va="center", fontsize=11.0, color="#5B6472", fontweight="regular")

        for part, offset in zip(PLOT_PART_ORDER, bar_offsets):
            yb = y + offset
            rollout_values = [scores[(judge, model, rollout, part)] for rollout in ROLLOUT_ORDER]
            value = mean(rollout_values)
            bar_end = bar_l + (value / 100.0) * (bar_r - bar_l)

            ax.text(label_x, yb, PART_LABELS[part], ha="right", va="center", fontsize=10.8, color="#5B6472")
            style = METRIC_STYLES[part]
            ax.add_patch(
                Rectangle(
                    (bar_l, yb - bar_h / 2),
                    bar_end - bar_l,
                    bar_h,
                    facecolor=color_with_alpha(color, style["alpha"]),
                    edgecolor=color_with_alpha(color, style["edge_alpha"]) if style["hatch"] else "none",
                    linewidth=0.55 if style["hatch"] else 0.0,
                    hatch=style["hatch"],
                    zorder=2,
                )
            )
            ax.text(
                bar_end,
                yb + bar_h * 0.72,
                pct(value),
                ha="center",
                va="bottom",
                fontsize=10.2,
                color="#111827",
                fontweight="semibold",
            )

            min_x = bar_l + (min(rollout_values) / 100.0) * (bar_r - bar_l)
            max_x = bar_l + (max(rollout_values) / 100.0) * (bar_r - bar_l)
            ax.plot([min_x, max_x], [yb, yb], color="#111827", lw=0.85, alpha=0.68, zorder=4)
            for rollout, rollout_value in zip(ROLLOUT_ORDER, rollout_values):
                x = bar_l + (rollout_value / 100.0) * (bar_r - bar_l)
                ax.scatter(
                    x,
                    yb,
                    s=58,
                    color=color,
                    edgecolor="white",
                    linewidth=1.45,
                    zorder=5 + rollout,
                )

    ax.text(
        outer_l,
        0.064,
        '[1] B. Razavi, "Analog Design Experiments With AI--Part 1 [The Analog Mind]," IEEE Solid-State Circuits Magazine, vol. 17, no. 4, pp. 11-15, Fall 2025.',
        ha="left",
        va="bottom",
        fontsize=9,
        color="#6B7280",
    )
    ax.text(
        outer_l,
        0.040,
        '[2] B. Razavi, "Analog Design Experiments With AI--Part 2 [The Analog Mind]," IEEE Solid-State Circuits Magazine, vol. 18, no. 2, pp. 8-13, Spring 2026.',
        ha="left",
        va="bottom",
        fontsize=9,
        color="#6B7280",
    )

    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, facecolor="white")
    fig.savefig(output_svg, facecolor="white")
    plt.close(fig)


def plot_scores(rows: list[dict], out_dir: Path) -> list[Path]:
    outputs = []
    for judge in JUDGE_ORDER:
        output_png = out_dir / f"judge_scores_{judge}.png"
        output_svg = out_dir / f"judge_scores_{judge}.svg"
        plot_scores_for_judge(rows, judge, output_png, output_svg)
        outputs.extend([output_png, output_svg])
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR / "judge_scores" / "summary.csv",
        help="Rollout-aware score summary CSV.",
    )
    parser.add_argument(
        "--judge-output-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR / "judge_outputs",
        help="Directory containing per-answer judge output JSONL files.",
    )
    parser.add_argument(
        "--rebuild-summary",
        action="store_true",
        help="Regenerate summary CSV from judge output JSONL before plotting.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR / "figures",
        help="Directory for generated figures.",
    )
    args = parser.parse_args()

    if args.rebuild_summary:
        write_summary(args.summary, build_summary_rows(args.judge_output_dir))
    rows = load_summary(args.summary)
    for output in plot_scores(rows, args.out_dir):
        print(output)


if __name__ == "__main__":
    main()
