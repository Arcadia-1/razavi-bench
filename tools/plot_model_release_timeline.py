#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "docs/data/direct_qa/index.json"
DEFAULT_DATES = ROOT / "docs/data/direct_qa/model_release_dates.csv"
DEFAULT_OUTPUT = ROOT / "docs/assets/direct_qa_score_vs_release_date.png"

PROVIDER_STYLE = {
    "anthropic": ("Anthropic", "#C8611A"),
    "openai": ("OpenAI", "#2F9B60"),
    "google": ("Google", "#2F7ED8"),
    "alibaba": ("Qwen", "#148C83"),
    "qwen": ("Qwen", "#148C83"),
    "xai": ("xAI", "#374151"),
    "bytedance": ("ByteDance", "#D97706"),
    "moonshot": ("Moonshot", "#7C5CC4"),
    "thinkingmachines": ("Thinking Machines", "#D63384"),
    "stepfun": ("StepFun", "#9333EA"),
    "minimax": ("MiniMax", "#D04F5F"),
    "meta": ("Meta", "#8B1E1E"),
}

LABEL_OFFSETS = {
    "claude_opus_48": (9, -13),
    "gemini_35_flash": (-8, 13),
    "doubao_seed_21_pro": (8, -8),
    "llama_4_maverick": (-8, 0),
}

RECENT_LABEL_Y = {
    "claude_opus_5_high": 96.2,
    "claude_opus_5_xhigh": 93.9,
    "claude_opus_5": 91.6,
    "claude_opus_5_medium": 89.3,
    "qwen_38": 87.4,
    "gemini_36_flash": 85.7,
    "gpt_56": 84.0,
    "gpt_56_terra": 82.3,
    "grok_45": 80.6,
    "gpt_56_luna": 78.9,
    "qwen_37_flash": 77.2,
    "kimi_k3": 75.5,
    "inkling_small": 73.8,
    "inkling": 65.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot active Direct QA score against model release date."
    )
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--dates", type=Path, default=DEFAULT_DATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_rows(index_path: Path, dates_path: Path) -> list[dict[str, object]]:
    index = json.loads(index_path.read_text())
    models = {model["model_key"]: model for model in index["models"]}
    with dates_path.open(newline="") as handle:
        date_rows = list(csv.DictReader(handle))

    date_keys = [row["model_key"] for row in date_rows]
    if len(date_keys) != len(set(date_keys)):
        duplicates = sorted(key for key, count in Counter(date_keys).items() if count > 1)
        raise ValueError(f"Duplicate model keys in release-date table: {duplicates}")
    if set(date_keys) != set(models):
        raise ValueError(
            "Release-date coverage mismatch: "
            f"missing={sorted(set(models) - set(date_keys))}, "
            f"extra={sorted(set(date_keys) - set(models))}"
        )

    rows: list[dict[str, object]] = []
    name_counts = Counter(model["display_name"] for model in models.values())
    for release in date_rows:
        model = models[release["model_key"]]
        if release["display_name"] != model["display_name"]:
            raise ValueError(
                f"Display-name mismatch for {release['model_key']}: "
                f"{release['display_name']!r} != {model['display_name']!r}"
            )
        label = model["display_name"]
        if name_counts[label] > 1:
            label = f"{label}\nEffort: {model['thinking_effort']}"
        rows.append(
            {
                **release,
                "release_date": datetime.strptime(release["release_date"], "%Y-%m-%d").date(),
                "score": float(model["summary"]["scores"]["overall"]["active"]["score_percent"]),
                "label": label,
            }
        )
    return rows


def annotate(ax: plt.Axes, row: dict[str, object]) -> None:
    key = str(row["model_key"])
    if key in RECENT_LABEL_Y:
        ax.annotate(
            str(row["label"]),
            (row["release_date"], row["score"]),
            xytext=(1.018, RECENT_LABEL_Y[key]),
            textcoords=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=7.2,
            color="#111827",
            linespacing=1.05,
            arrowprops={"arrowstyle": "-", "color": "#9CA3AF", "lw": 0.6},
            bbox={"boxstyle": "square,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.9},
            annotation_clip=False,
            clip_on=False,
            zorder=4,
        )
        return
    dx, dy = LABEL_OFFSETS.get(key, (7, 5))
    horizontal_alignment = "right" if dx < 0 else "left"
    ax.annotate(
        str(row["label"]),
        (row["release_date"], row["score"]),
        xytext=(dx, dy),
        textcoords="offset points",
        ha=horizontal_alignment,
        va="center",
        fontsize=7.2,
        color="#111827",
        linespacing=1.05,
        arrowprops={"arrowstyle": "-", "color": "#9CA3AF", "lw": 0.55},
        bbox={"boxstyle": "square,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.88},
        annotation_clip=False,
        clip_on=False,
        zorder=4,
    )


def style_axis(ax: plt.Axes) -> None:
    ax.set_ylim(38, 97)
    ax.set_yticks(range(40, 101, 10))
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.grid(axis="x", color="#F0F2F5", linewidth=0.7)
    ax.tick_params(colors="#6B7280", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))


def plot(rows: list[dict[str, object]], output: Path) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.titleweight": "bold",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })
    figure, (old_ax, recent_ax) = plt.subplots(
        1,
        2,
        figsize=(20, 11),
        dpi=180,
        sharey=True,
        gridspec_kw={"width_ratios": [1.25, 4.75], "wspace": 0.035},
    )
    old_ax.set_xlim(date(2024, 4, 1), date(2025, 6, 1))
    recent_ax.set_xlim(date(2025, 11, 15), date(2026, 8, 10))
    old_ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    recent_ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    style_axis(old_ax)
    style_axis(recent_ax)
    recent_ax.spines["left"].set_visible(False)
    recent_ax.tick_params(axis="y", left=False, labelleft=False)

    for row in rows:
        axis = old_ax if row["release_date"] < date(2025, 6, 1) else recent_ax
        _, color = PROVIDER_STYLE[str(row["provider"])]
        axis.scatter(
            row["release_date"],
            row["score"],
            s=72,
            color=color,
            edgecolor="white",
            linewidth=1.4,
            zorder=5,
        )
        annotate(axis, row)

    old_ax.set_ylabel("Active Overall Score (%)", fontsize=11, fontweight="bold", color="#111827")
    figure.supxlabel("Model Release Date", y=0.075, fontsize=11, fontweight="bold", color="#111827")
    figure.suptitle(
        "Razavi-Bench: Multimodal QA",
        x=0.055,
        y=0.97,
        ha="left",
        fontsize=25,
        fontweight="bold",
        color="#0B1220",
    )
    figure.text(
        0.056,
        0.927,
        "Overall Score vs. Model Release Date",
        fontsize=14,
        fontweight="bold",
        color="#111827",
    )
    figure.text(
        0.056,
        0.899,
        "32 Direct QA configurations · 3 rollouts · active score is the mean of MiniMax M3 and DeepSeek V4 Pro judges",
        fontsize=9.5,
        color="#4B5563",
    )

    diagonal = 0.012
    kwargs = {"color": "#6B7280", "clip_on": False, "linewidth": 1.1}
    old_ax.plot((1 - diagonal, 1 + diagonal), (-diagonal, +diagonal), transform=old_ax.transAxes, **kwargs)
    recent_ax.plot((-diagonal, +diagonal), (-diagonal, +diagonal), transform=recent_ax.transAxes, **kwargs)

    providers = []
    seen = set()
    for row in rows:
        legend_name, color = PROVIDER_STYLE[str(row["provider"])]
        if legend_name in seen:
            continue
        seen.add(legend_name)
        providers.append(
            Line2D([0], [0], marker="o", color="none", markerfacecolor=color,
                   markeredgecolor="white", markersize=7, label=legend_name)
        )
    figure.legend(
        handles=providers,
        loc="lower center",
        bbox_to_anchor=(0.53, 0.015),
        ncol=6,
        frameon=False,
        fontsize=8,
        handletextpad=0.4,
        columnspacing=1.3,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.subplots_adjust(left=0.055, right=0.80, top=0.86, bottom=0.13)
    figure.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    rows = load_rows(args.index, args.dates)
    if len(rows) != 32:
        raise ValueError(f"Expected 32 active configurations, got {len(rows)}")
    plot(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} points)")


if __name__ == "__main__":
    main()
