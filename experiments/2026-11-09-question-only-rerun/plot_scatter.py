#!/usr/bin/env python3
"""Scatter of each finished entry's published score against its question-only rerun score.

Reads the published answers in docs/data/direct_qa/models/ and the rerun's GPT-6 Luna
scores (scores-gpt-6-luna-max.jsonl for the OpenRouter entries, scores-selfhosted-*.jsonl
for the self-hosted Qwen models), counting only scores of the current answers given
against the current reference. Writes scatter_published_vs_rerun.png and .csv.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# Entries whose rerun raised the reasoning effort above the published run's; every other
# entry kept its published reasoning setting, so only the prompt changed.
EFFORT_RAISED = {"qwen_37_plus", "qwen_37_flash", "mimo_2_6_pro", "gpt_54_mini", "minimax_m3",
                 "gemma_4_31b_it", "gemini_25_flash_lite", "claude_haiku_45"}
SHORT = {"Qwen3-VL-235B-A22B Instruct": "Qwen3-VL 235B", "Qwen2.5-VL-72B Instruct": "Qwen2.5-VL 72B",
         "GPT-4o (2024-11-20)": "GPT-4o 1120", "GPT-4o (2024-08-06)": "GPT-4o 0806", "GPT-4o Mini": "GPT-4o mini",
         "DeepSeek V4.1 Flash 0910": "DeepSeek V4.1 Flash", "Claude Haiku 4.5": "Haiku 4.5", "Gemma 4 31B IT": "Gemma 4 31B",
         "Nemotron 3.5 Super VL": "Nemotron 3.5 Super VL", "Mistral Large 2512": "Mistral Large 2512"}
# Label offsets in points (dx, dy, horizontal alignment) where the default (right of the dot) collides.
OFFSETS = {"GPT-5.4 Mini": (-7, 0, "right"), "Qwen2.5-VL 72B": (0, 10, "center"), "GPT-4o mini": (7, -4, "left"),
           "Haiku 4.5": (-7, 0, "right"), "GPT-4o 0806": (7, -3, "left"), "GPT-4o 1120": (7, 3, "left"),
           "Nova Pro": (7, -2, "left"), "Qwen 3.8 27B": (7, -3, "left"), "DeepSeek V4.1 Flash": (9, -6, "left"),
           "Qwen 3.7 Plus": (0, 10, "center"), "Gemma 4 31B": (-7, 0, "right"), "Gemini 2.5 Flash-Lite": (7, -4, "left"), "Qwen 3.7 Flash": (7, -4, "left"), "Gemini 3.7 Flash": (-7, 2, "right")}

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#ebeae6"
SAME, RAISED = "#2a78d6", "#eb6834"   # categorical slots 1 and 2, validated all-pairs


def rows() -> list[dict]:
    golden = {p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO / "tasks").glob("*/golden_solution.md")}
    answers = {}
    for name in ("answers.jsonl", "answers_selfhosted.jsonl", "answers_selfhosted_9b.jsonl"):
        for r in map(json.loads, open(HERE / name)):
            answers[(r["model_name"], r["task_slug"], r["rollout"])] = hashlib.sha256(r["answer"].encode()).hexdigest()
    scores = {}
    for name in ("scores-gpt-6-luna-max.jsonl", "scores-selfhosted-gpt-6-luna-max.jsonl", "scores-selfhosted-9b-gpt-6-luna-max.jsonl",
                 "scores-recal4-gpt-6-luna-max.jsonl"):
        for s in map(json.loads, open(HERE / name)):
            key = (s["answer_metadata"]["model_name"], s["task_slug"], s["answer_metadata"]["rollout"])
            if answers.get(key) == s["answer_sha256"] and golden[s["task_slug"]] == s["golden_solution_sha256"]:
                scores.setdefault(key[0], {})[key[1:]] = s["score_0_to_4"]
    index = {m["model_key"]: m for m in json.loads((REPO / "docs/data/direct_qa/index.json").read_text())["models"]}
    out = []
    for key, values in scores.items():
        assert len(values) == 150, (key, len(values))
        published = json.loads((REPO / "docs/data/direct_qa" / index[key]["detail_file"]).read_text())["answers"]
        out.append({"model_key": key, "name": index[key]["display_name"],
                    "published": 25 * st.fmean(a["active_score"]["score_0_to_4"] for a in published),
                    "rerun": 25 * st.fmean(values.values()), "effort_raised": key in EFFORT_RAISED})
    return sorted(out, key=lambda r: -r["published"])


def main() -> None:
    data = rows()
    for path in ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9, 9.4), dpi=200, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    lo, hi = 18, 96
    ax.plot([lo, hi], [lo, hi], color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1, label="虚线：重跑与发布时相同")
    ax.text(hi - 2, lo + 2, "对角线以下：重跑后分数变低", color=INK2, fontsize=9, ha="right")
    for group, color, label in ((False, SAME, "推理设置不变，只改题面"), (True, RAISED, "改题面 + 推理强度调高")):
        pts = [r for r in data if r["effort_raised"] == group]
        mean = st.fmean(r["rerun"] - r["published"] for r in pts)
        ax.scatter([r["published"] for r in pts], [r["rerun"] for r in pts], s=70, color=color, edgecolor=SURFACE,
                   linewidth=1.6, zorder=3, label=f"{label}（{len(pts)} 个，平均 {mean:+.1f} 分）")
    for r in data:
        name = SHORT.get(r["name"], r["name"])
        dx, dy, ha = OFFSETS.get(name, (7, 0, "left"))
        ax.annotate(name, (r["published"], r["rerun"]), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=8.5, color=INK, zorder=4)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel("发布时得分 (%)", color=INK2, fontsize=10.5)
    ax.set_ylabel("只发题目和图的重跑得分 (%)", color=INK2, fontsize=10.5)
    ax.set_xticks(range(20, 100, 10)); ax.set_yticks(range(20, 100, 10))
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(color=GRID, lw=0.8, zorder=0)
    for side in ax.spines.values():
        side.set_visible(False)
    mean_all = st.fmean(r["rerun"] - r["published"] for r in data)
    fig.text(0.07, 0.965, "22 个模型：发布时得分 vs. 只发题目和图的重跑", fontsize=14, color=INK, weight="bold")
    fig.text(0.07, 0.938, f"GPT-6 Luna 评分，每个模型 50 题 × 3 次；全部平均 {mean_all:+.1f} 分", fontsize=10, color=INK2)
    ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK, handletextpad=0.3, borderaxespad=0.6)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.06, top=0.92)
    fig.savefig(HERE / "scatter_published_vs_rerun.png", facecolor=SURFACE)

    with (HERE / "scatter_published_vs_rerun.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["model_key", "name", "published", "rerun", "change", "effort_raised"])
        for r in data:
            writer.writerow([r["model_key"], r["name"], f"{r['published']:.1f}", f"{r['rerun']:.1f}",
                             f"{r['rerun'] - r['published']:+.1f}", r["effort_raised"]])
    print(f"{len(data)} entries; mean change {mean_all:+.2f}")


if __name__ == "__main__":
    main()
