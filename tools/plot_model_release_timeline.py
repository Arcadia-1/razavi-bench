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
    "claude_sonnet_46": (-8, 8),
    "claude_fable_5": (-8, 8),
    "claude_opus_48": (-8, -13),
    "gemini_31": (-8, 10),
    "gemini_35_flash": (-8, 13),
    "gemma_4_31b_it": (-8, -12),
    "doubao_seed_21_pro": (-8, -8),
    "gpt_54_mini": (8, -10),
    "gpt_55": (-8, 8),
    "llama_4_maverick": (-8, 0),
    "minimax_m3": (8, 12),
    "qwen_37_plus": (-8, 20),
}

RECENT_LABEL_Y = {
    "claude_opus_5_high": 96.4,
    "claude_opus_5_xhigh": 93.6,
    "claude_opus_5": 90.8,
    "claude_opus_5_medium": 88.0,
    "qwen_38": 85.5,
    "gemini_36_flash": 83.3,
    "gpt_56": 81.1,
    "gpt_56_terra": 78.9,
    "grok_45": 76.7,
    "gpt_56_luna": 74.5,
    "qwen_37_flash": 72.3,
    "kimi_k3": 70.1,
    "inkling_small": 67.9,
    "inkling": 64.8,
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
            fontsize=11.5,
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
        fontsize=11.5,
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
    ax.tick_params(colors="#6B7280", labelsize=13)
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
    figure, ax = plt.subplots(
        figsize=(20, 15),
        dpi=180,
    )
    ax.set_xlim(date(2024, 4, 15), date(2026, 8, 10))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[2, 5, 8, 11]))
    style_axis(ax)

    for row in rows:
        _, color = PROVIDER_STYLE[str(row["provider"])]
        ax.scatter(
            row["release_date"],
            row["score"],
            s=72,
            color=color,
            edgecolor="white",
            linewidth=1.4,
            zorder=5,
        )
        annotate(ax, row)

    ax.set_ylabel("Active Overall Score (%)", fontsize=17, fontweight="bold", color="#111827")
    figure.supxlabel("Model Release Date", y=0.105, fontsize=17, fontweight="bold", color="#111827")
    figure.suptitle(
        "Razavi-Bench: Multimodal QA — Overall Score vs. Model Release Date",
        x=0.055,
        y=0.972,
        ha="left",
        fontsize=27,
        fontweight="bold",
        color="#0B1220",
    )
    figure.text(
        0.056,
        0.925,
        "32 Direct QA configurations · 3 rollouts · active score is the mean of MiniMax M3 and DeepSeek V4 Pro judges",
        fontsize=14,
        color="#4B5563",
    )

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
    ax.legend(
        handles=providers,
        loc="lower center",
        bbox_to_anchor=(0.60, 0.012),
        ncol=6,
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=0.90,
        fontsize=12,
        handletextpad=0.4,
        columnspacing=1.3,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.subplots_adjust(left=0.06, right=0.76, top=0.88, bottom=0.18)
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
