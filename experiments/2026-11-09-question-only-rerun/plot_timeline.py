#!/usr/bin/env python3
"""Score against release date for the finished entries: published (hollow, dashed frontier)
and question-only rerun (filled, solid frontier), each model's two scores joined by a line.

Reads scatter_published_vs_rerun.csv (written by plot_scatter.py) and the release dates in
docs/data/direct_qa/model_release_dates.csv. The frontiers are the running best score by
release date among these entries only. Writes timeline_published_vs_rerun.png.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

SURFACE, INK, INK2, OLD, LINK, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#d6d5d0", "#ebeae6"
NEW = "#2a78d6"
SHORT = {"Qwen3-VL-235B-A22B Instruct": "Qwen3-VL 235B", "Qwen2.5-VL-72B Instruct": "Qwen2.5-VL 72B",
         "GPT-4o (2024-11-20)": "GPT-4o 1120", "GPT-4o (2024-08-06)": "GPT-4o 0806", "GPT-4o Mini": "GPT-4o mini",
         "DeepSeek V4.1 Flash 0910": "DeepSeek V4.1 Flash", "Claude Haiku 4.5": "Haiku 4.5", "Gemma 4 31B IT": "Gemma 4 31B",
         "Nemotron 3.5 Super VL": "Nemotron 3.5"}
# Label offsets in points from the rerun (filled) dot: (dx, dy, horizontal alignment).
# Dots on a frontier line get their label off the line; the Jul-Sep 2026 cluster is spread by hand.
OFFSETS = {"GPT-4o mini": (4, -10, "left"), "GPT-4o 0806": (4, -10, "left"), "GPT-4o 1120": (4, -10, "left"),
           "Llama 4 Maverick": (4, 9, "left"), "GPT-5.4 Mini": (-8, 0, "right"), "Qwen 3.7 Plus": (-8, 0, "right"),
           "MiniMax M3": (-8, 0, "right"), "Gemini 3.7 Flash": (-8, 0, "right"), "Qwen 3.7 Flash": (0, -11, "center"),
           "Qwen 3.8 27B": (7, -10, "left")}
START, END, AXIS_END = date(2024, 6, 15), date(2026, 11, 15), date(2026, 12, 31)


def frontier(points: list[tuple[date, float]]) -> tuple[list[date], list[float]]:
    xs, ys, best = [], [], float("-inf")
    for day, score in sorted(points):
        if score > best:
            xs.append(day); ys.append(score); best = score
    return xs + [END], ys + [best]


def main() -> None:
    released = {r["model_key"]: date.fromisoformat(r["release_date"])
                for r in csv.DictReader(open(REPO / "docs/data/direct_qa/model_release_dates.csv"))}
    data = [{**r, "day": released[r["model_key"]], "published": float(r["published"]), "rerun": float(r["rerun"])}
            for r in csv.DictReader(open(HERE / "scatter_published_vs_rerun.csv"))]
    for path in ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(13, 8), dpi=200, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for r in data:
        ax.plot([r["day"], r["day"]], [r["published"], r["rerun"]], color=LINK, lw=1.2, zorder=1, solid_capstyle="butt")
    fx, fy = frontier([(r["day"], r["published"]) for r in data])
    ax.step(fx, fy, where="post", color=OLD, lw=1.6, ls=(0, (5, 4)), zorder=2)
    fx, fy = frontier([(r["day"], r["rerun"]) for r in data])
    ax.step(fx, fy, where="post", color=NEW, lw=2, zorder=2)
    ax.scatter([r["day"] for r in data], [r["published"] for r in data], s=62, facecolor=SURFACE, edgecolor=OLD,
               linewidth=1.6, zorder=3)
    ax.scatter([r["day"] for r in data], [r["rerun"] for r in data], s=62, color=NEW, edgecolor=SURFACE,
               linewidth=1.4, zorder=4)
    for r in data:
        name = SHORT.get(r["name"], r["name"])
        dx, dy, ha = OFFSETS.get(name, (7, 0, "left"))
        ax.annotate(name, (r["day"], r["rerun"]), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=8.5, color=INK, zorder=5,
                    path_effects=[patheffects.withStroke(linewidth=3, foreground=SURFACE)])

    ax.set_xlim(START, AXIS_END); ax.set_ylim(15, 100)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_xlabel("模型发布日期", color=INK2, fontsize=10.5)
    ax.set_ylabel("得分 (%)", color=INK2, fontsize=10.5)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(color=GRID, lw=0.8, zorder=0)
    for side in ax.spines.values():
        side.set_visible(False)
    handles = [
        Line2D([], [], marker="o", ls="none", markersize=8, markerfacecolor=SURFACE, markeredgecolor=OLD, markeredgewidth=1.6,
               label="发布时得分"),
        Line2D([], [], color=OLD, lw=1.6, ls=(0, (5, 4)), label="发布时最高分（随时间）"),
        Line2D([], [], marker="o", ls="none", markersize=8, color=NEW, label="重跑得分（只发题目和图）"),
        Line2D([], [], color=NEW, lw=2, label="重跑最高分（随时间）"),
        Line2D([], [], color=LINK, lw=1.2, label="同一模型的两次得分"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK)
    fig.text(0.06, 0.955, "22 个已重跑模型：得分 vs. 发布日期", fontsize=14, color=INK, weight="bold")
    fig.text(0.06, 0.925, "空心点、虚线 = 发布时；实心点、实线 = 新题面重跑。GPT-6 Luna 评分，每个模型 50 题 × 3 次；最高分线只在这 22 个模型里算",
             fontsize=9.5, color=INK2)
    fig.subplots_adjust(left=0.06, right=0.98, bottom=0.08, top=0.9)
    fig.savefig(HERE / "timeline_published_vs_rerun.png", facecolor=SURFACE)
    print("written timeline_published_vs_rerun.png")


if __name__ == "__main__":
    main()
