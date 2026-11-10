#!/usr/bin/env python3
"""Published versus question-only rerun scores for every complete entry in rerun_scores.csv.

Writes compare_timeline.png (score against release date: hollow points and a dashed frontier
for the published scores, filled points and a solid frontier for the rerun) and
compare_dumbbell.png (one row per entry, sorted by rerun score). Run collect_scores.py first.
"""

from __future__ import annotations

import csv
import statistics as st
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, patheffects
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
SURFACE, INK, INK2, OLD, LINK, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#d6d5d0", "#ebeae6"
SAME, RAISED = "#2a78d6", "#eb6834"   # categorical slots 1 and 2, validated all-pairs
SHORT = {"Qwen3-VL-235B-A22B Instruct": "Qwen3-VL 235B", "Qwen2.5-VL-72B Instruct": "Qwen2.5-VL 72B",
         "GPT-4o (2024-11-20)": "GPT-4o 1120", "GPT-4o (2024-08-06)": "GPT-4o 0806", "GPT-4o (2024-05-13)": "GPT-4o 0513",
         "GPT-4o Mini": "GPT-4o mini", "Nemotron 3.5 Super VL": "Nemotron 3.5", "Gemma 4 31B IT": "Gemma 4 31B",
         "DeepSeek V4.1 Flash 0910": "DeepSeek 0910", "DeepSeek V4.1 Flash 1017": "DeepSeek 1017"}
OFFSETS = [(6, 0, "left"), (-6, 0, "right"), (0, 8, "center"), (0, -8, "center"), (6, 7, "left"), (6, -7, "left"),
           (-6, 7, "right"), (-6, -7, "right"), (12, 13, "left"), (12, -13, "left"), (-12, 13, "right"), (-12, -13, "right"),
           (0, 16, "center"), (0, -16, "center"), (18, 20, "left"), (18, -20, "left"), (-18, 20, "right"), (-18, -20, "right"),
           (26, 0, "left"), (-26, 0, "right"), (24, 28, "left"), (24, -28, "left"), (-24, 28, "right"), (-24, -28, "right"),
           (0, 28, "center"), (0, -28, "center"), (34, 14, "left"), (34, -14, "left"), (-34, 14, "right"), (-34, -14, "right")]
FIXED: dict = {}  # label -> offset, to pin a label by hand


def setup_font() -> None:
    for path in ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


def load() -> list[dict]:
    rows = []
    for r in csv.DictReader(open(HERE / "rerun_scores.csv")):
        if r["rerun"]:
            rows.append({**r, "published": float(r["published"]) if r["published"] else None, "rerun": float(r["rerun"]),
                         "day": date.fromisoformat(r["release_date"]), "raised": r["effort_raised"] == "True",
                         "short": SHORT.get(r["name"], r["name"])})
    return rows


def frontier(points, end):
    xs, ys, best = [], [], float("-inf")
    for day, score in sorted(points):
        if score > best:
            xs.append(day); ys.append(score); best = score
    return xs + [end], ys + [best]


def place_labels(fig, ax, items, points, lines):
    """Pick one offset per label, minimising overlaps with other labels, points, the frontier lines and the axes edge.

    Every candidate box is measured once; then each label in turn moves to its cheapest offset given the others,
    until a pass changes nothing. Nearer offsets (earlier in OFFSETS) win ties; labels away from their point get a leader line.
    """
    renderer = fig.canvas.get_renderer()
    frame = ax.get_window_extent(renderer)
    pts = np.array([[b.x0, b.y0, b.x1, b.y1] for b in points])
    lns = np.array([[b.x0, b.y0, b.x1, b.y1] for b in lines])

    def hits(box, others):
        return int(np.sum((others[:, 0] < box[2]) & (box[0] < others[:, 2]) & (others[:, 1] < box[3]) & (box[1] < others[:, 3])))

    offsets, boxes, base = [], [], []
    for x, y, text in items:
        opts = [FIXED[text]] if text in FIXED else OFFSETS
        bs, cs = [], []
        for k, (dx, dy, ha) in enumerate(opts):
            t = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=7.5)
            b = t.get_window_extent(renderer).expanded(1.08, 1.35)
            t.remove()
            box = np.array([b.x0, b.y0, b.x1, b.y1])
            inside = frame.x0 <= b.x0 and b.x1 <= frame.x1 and frame.y0 <= b.y0 and b.y1 <= frame.y1
            bs.append(box)
            cs.append(20 * hits(box, pts) + hits(box, lns) + (0 if inside else 1000) + 0.6 * k)
        offsets.append(opts); boxes.append(np.array(bs)); base.append(np.array(cs))
    choice = [int(np.argmin(c)) for c in base]
    for _ in range(30):
        changed = False
        for i in range(len(items)):
            others = np.array([boxes[j][choice[j]] for j in range(len(items)) if j != i])
            b = boxes[i]
            clash = ((others[None, :, 0] < b[:, None, 2]) & (b[:, None, 0] < others[None, :, 2])
                     & (others[None, :, 1] < b[:, None, 3]) & (b[:, None, 1] < others[None, :, 3])).sum(axis=1)
            k = int(np.argmin(base[i] + 100 * clash))
            if k != choice[i]:
                choice[i], changed = k, True
        if not changed:
            break
    for (x, y, text), opts, k in zip(items, offsets, choice):
        dx, dy, ha = opts[k]
        far = abs(dx) >= 12 or abs(dy) >= 13  # beyond the first ring of offsets: draw a leader line to the point
        ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=7.5, color=INK, zorder=6,
                    arrowprops=dict(arrowstyle="-", color=OLD, lw=0.6, shrinkA=1, shrinkB=4) if far else None,
                    path_effects=[patheffects.withStroke(linewidth=2.5, foreground=SURFACE)])


def timeline(rows) -> None:
    new = [r for r in rows if r["published"] is None]
    rows = [r for r in rows if r["published"] is not None]
    fig, ax = plt.subplots(figsize=(19, 13.5), dpi=170, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    start, end = date(2024, 4, 1), date(2027, 2, 1)
    for r in rows:
        ax.plot([r["day"], r["day"]], [r["published"], r["rerun"]], color=LINK, lw=1.1, zorder=1)
    fx, fy = frontier([(r["day"], r["published"]) for r in rows], end)
    ax.step(fx, fy, where="post", color=OLD, lw=1.6, ls=(0, (5, 4)), zorder=2)
    fx, fy = frontier([(r["day"], r["rerun"]) for r in rows + new], end)
    ax.step(fx, fy, where="post", color=SAME, lw=2, zorder=2)
    ax.scatter([r["day"] for r in rows], [r["published"] for r in rows], s=46, facecolor=SURFACE, edgecolor=OLD, linewidth=1.4, zorder=3)
    for group, color in ((False, SAME), (True, RAISED)):
        pts = [r for r in rows + new if r["raised"] == group]
        ax.scatter([r["day"] for r in pts], [r["rerun"] for r in pts], s=48, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=4)
    ax.set_xlim(start, end); ax.set_ylim(15, 101)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_xlabel("模型发布日期", color=INK2, fontsize=11); ax.set_ylabel("得分 (%)", color=INK2, fontsize=11)
    ax.tick_params(colors=INK2, labelsize=9.5, length=0)
    ax.grid(color=GRID, lw=0.8, zorder=0)
    for side in ax.spines.values():
        side.set_visible(False)
    fig.subplots_adjust(left=0.05, right=0.985, bottom=0.07, top=0.92)  # final layout before placing labels
    fig.canvas.draw()
    points, lines = [], []
    for r in rows:
        for y in (r["published"], r["rerun"]):
            px, py = ax.transData.transform((mdates.date2num(r["day"]), y))
            points.append(matplotlib.transforms.Bbox([[px - 5, py - 5], [px + 5, py + 5]]))
    for values in ([(r["day"], r["published"]) for r in rows], [(r["day"], r["rerun"]) for r in rows + new]):
        xs, ys = frontier(values, end)  # keep labels off both frontier lines
        path = [(xs[0], ys[0])]
        for x, y0, y1 in zip(xs[1:], ys[:-1], ys[1:]):
            path += [(x, y0), (x, y1)]
        pts = [ax.transData.transform((mdates.date2num(x), y)) for x, y in path]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / 6))
            for k in range(n + 1):
                px, py = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                lines.append(matplotlib.transforms.Bbox([[px - 2, py - 2], [px + 2, py + 2]]))
    for r in new:
        px, py = ax.transData.transform((mdates.date2num(r["day"]), r["rerun"]))
        points.append(matplotlib.transforms.Bbox([[px - 5, py - 5], [px + 5, py + 5]]))
    place_labels(fig, ax, [(r["day"], r["rerun"], r["short"] + (" (新)" if r in new else "")) for r in rows + new], points, lines)
    handles = [
        Line2D([], [], marker="o", ls="none", markersize=7, markerfacecolor=SURFACE, markeredgecolor=OLD, markeredgewidth=1.4, label="发布时得分"),
        Line2D([], [], color=OLD, lw=1.6, ls=(0, (5, 4)), label="发布时最高分（随时间）"),
        Line2D([], [], marker="o", ls="none", markersize=7, color=SAME, label="重跑得分：推理设置不变"),
        Line2D([], [], marker="o", ls="none", markersize=7, color=RAISED, label="重跑得分：推理强度调到最高"),
        Line2D([], [], color=SAME, lw=2, label="重跑最高分（随时间）"),
        Line2D([], [], color=LINK, lw=1.1, label="同一模型的两次得分"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK)
    mean = st.fmean(r["rerun"] - r["published"] for r in rows)
    fig.text(0.05, 0.965, f"{len(rows)} 个模型：发布时得分 vs. 新题面重跑" + (f"（另有 {len(new)} 个新条目）" if new else ""), fontsize=15, color=INK, weight="bold")
    fig.text(0.05, 0.94, f"空心点、虚线 = 发布时；实心点、实线 = 只发题目和图、最高推理强度重跑。GPT-6 Luna 评分，每个模型 50 题 × 3 次；平均变化 {mean:+.1f} 分",
             fontsize=10, color=INK2)
    fig.savefig(HERE / "compare_timeline.png", facecolor=SURFACE)


def dumbbell(rows) -> None:
    rows = sorted(rows, key=lambda r: r["rerun"])
    fig, ax = plt.subplots(figsize=(10, 0.27 * len(rows) + 1.6), dpi=180, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for i, r in enumerate(rows):
        if r["published"] is not None:
            ax.plot([r["published"], r["rerun"]], [i, i], color=LINK, lw=2, zorder=1, solid_capstyle="round")
            ax.scatter(r["published"], i, s=34, facecolor=SURFACE, edgecolor=OLD, linewidth=1.3, zorder=2)
        ax.scatter(r["rerun"], i, s=36, color=RAISED if r["raised"] else SAME, zorder=3)
        d = r["rerun"] - r["published"] if r["published"] is not None else None
        ax.text(101.5, i, f"{r['rerun']:.1f}", va="center", ha="right", fontsize=8, color=INK)
        ax.text(108.5, i, f"{d:+.1f}" if d is not None else "新", va="center", ha="right", fontsize=8, color=INK2)
    ax.set_yticks(range(len(rows)), [r["short"] for r in rows], fontsize=8.5, color=INK)
    ax.set_xlim(15, 109); ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xticks(range(20, 101, 10)); ax.tick_params(axis="x", colors=INK2, labelsize=8.5, length=0)
    ax.tick_params(axis="y", length=0)
    ax.text(101.5, len(rows) - 0.1, "重跑", ha="right", va="bottom", fontsize=8, color=INK2)
    ax.text(108.5, len(rows) - 0.1, "变化", ha="right", va="bottom", fontsize=8, color=INK2)
    ax.grid(axis="x", color=GRID, lw=0.8, zorder=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xlabel("得分 (%)", color=INK2, fontsize=10)
    handles = [
        Line2D([], [], marker="o", ls="none", markersize=6.5, markerfacecolor=SURFACE, markeredgecolor=OLD, markeredgewidth=1.3, label="发布时"),
        Line2D([], [], marker="o", ls="none", markersize=6.5, color=SAME, label="重跑：推理设置不变"),
        Line2D([], [], marker="o", ls="none", markersize=6.5, color=RAISED, label="重跑：推理强度调到最高"),
    ]
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.86, 0.0), frameon=False, fontsize=8.5, labelcolor=INK)
    fig.text(0.02, 0.995, f"{len(rows)} 个模型逐个对比（按重跑得分排序）", fontsize=13, color=INK, weight="bold", va="top")
    fig.subplots_adjust(left=0.2, right=0.985, bottom=0.04, top=1 - 0.75 / (0.27 * len(rows) + 1.6))
    fig.savefig(HERE / "compare_dumbbell.png", facecolor=SURFACE)


def main() -> None:
    setup_font()
    rows = load()
    timeline(rows)
    dumbbell(rows)
    same = [r["rerun"] - r["published"] for r in rows if not r["raised"] and r["published"] is not None]
    up = [r["rerun"] - r["published"] for r in rows if r["raised"] and r["published"] is not None]
    print(f"{len(rows)} entries; mean change {st.fmean(same + up):+.2f} "
          f"(setting unchanged {len(same)}: {st.fmean(same):+.2f}; effort raised {len(up)}: {st.fmean(up):+.2f})")


if __name__ == "__main__":
    main()
