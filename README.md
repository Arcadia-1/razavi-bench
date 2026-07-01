---
license: cc-by-4.0
pretty_name: Razavi Bench
language:
  - en
task_categories:
  - question-answering
  - visual-question-answering
tags:
  - analog-design
  - circuit-design
  - benchmark
  - multimodal
  - llm-evaluation
  - electronic-design-automation
size_categories:
  - n<1K
configs:
  - config_name: tasks
    data_files:
      - split: train
        path: data/tasks.jsonl
  - config_name: model_answers_2026_06_26
    data_files:
      - split: train
        path: data/model_answers_2026-06-26-direct-qa.jsonl
  - config_name: judge_scores_deepseek_v4_pro_20260630_123714
    data_files:
      - split: train
        path: data/judge_scores_deepseek-v4-pro-20260630-123714.jsonl
---

<h1 align="center">Razavi-bench</h1>

<p align="center">
  <strong>An expert-curated benchmark for analog-design reasoning.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/tasks-50-blue?style=flat-square" alt="50 tasks"/>
  <img src="https://img.shields.io/badge/domain-analog%20design-8a63d2?style=flat-square" alt="Analog design"/>
  <img src="https://img.shields.io/badge/format-markdown-lightgrey?style=flat-square" alt="Markdown format"/>
</p>

Razavi-bench packages the question-answer assessments from Behzad Razavi's
*Analog Design Experiments With AI* Part 1 and Part 2 into a clean
one-task-per-directory benchmark. The tasks probe whether a model can reason
about MOS devices, small-signal circuits, feedback, oscillators, comparators,
dividers, LNAs, TIAs, and LC oscillators.

Each task directory keeps only the benchmark prompt, figure, and curated golden
answer. Cleaned public AI model outputs are stored separately under
`experiments/` so the task definitions remain independent from any model run.

## At a Glance

| Item | Count / Status |
|---|---:|
| Total tasks | 50 |
| Part 1 | 30 questions, Q1-Q30 |
| Part 2 | 20 questions, Q1-Q20 |
| `task.toml` files | 0 |
| Source PDFs | Included under `docs/papers/` with permission |

## Repository Layout

```text
tasks/<part>-<number>-<semantic-slug>/
  instruction.md
  golden_solution.md
  figure-xx.png  # only when the question has a figure
```

Top-level files:

| Path | Purpose |
|---|---|
| `data/` | Hugging Face Dataset Viewer friendly JSONL exports |
| `evaluation_rubric.md` | 0-4 evaluation guide used by judge scripts |
| `experiments/` | Cleaned model outputs and per-experiment metadata |
| `LICENSE` | License, source, and permission terms |

## Dataset Viewer Configs

This Hugging Face dataset exposes three structured configs:

| Config | Rows | Description |
|---|---:|---|
| `tasks` | 50 | Benchmark prompts, golden solutions, part/question numbers, and local figure paths. |
| `model_answers_2026_06_26` | 450 | Three independent rollouts for Claude, Gemini, and GPT on all 50 tasks. |
| `judge_scores_deepseek_v4_pro_20260630_123714` | 450 | DeepSeek-V4-Pro scores and rationales for the June 26, 2026 experiment. |

## Task Format

Each `instruction.md` contains only the benchmark prompt and any local figure
reference. It intentionally excludes source metadata, original model answers,
scores, and explanatory commentary.

Each `golden_solution.md` contains the expected reasoning and final answer for
evaluation. The golden answers were reviewed against the source articles,
figures, and circuit analysis.

## Experiments

`experiments/` contains cleaned model outputs and per-experiment metadata. The
`2026-06-26-direct-qa` experiment includes GPT, Gemini, and Claude
question-answer pairs from the direct-mm-v4-newgolden benchmark release. The
public files exclude system prompts, process
instructions, hidden reasoning, Vela session IDs, provider metadata, token/cost
data, and internal record IDs.

Automated judge scores, when present, are experiment metadata for transparency
and re-grading. They are not a substitute for independent expert review.
Experiment-specific scoring scripts live with the experiment that produced the
scores.

## License

The benchmark includes or adapts source questions and figures from Behzad
Razavi's *Analog Design Experiments With AI* articles with permission from
Behzad Razavi. Original article, question, and figure copyrights remain with
their respective rights holders, including Behzad Razavi and/or IEEE, as
applicable.

Dataset curation, cleaned transcripts, score tables, metadata, and documentation
are licensed under CC BY 4.0 as described in `LICENSE`. Code is licensed under
the MIT License in `LICENSE`.

## Notes

The user request originally mentioned 40 questions for Part 1, but the available
Part 1 article contains Q1 through Q30. No synthetic questions were added.

## References

- B. Razavi, "Analog Design Experiments With AI—Part 1 [The Analog Mind]," in
  IEEE Solid-State Circuits Magazine, vol. 17, no. 4, pp. 11-15, Fall 2025.
- B. Razavi, "Analog Design Experiments With AI—Part 2 [The Analog Mind]," in
  IEEE Solid-State Circuits Magazine, vol. 18, no. 2, pp. 8-13, Spring 2026.

## Test Results From June 26, 2026

<p align="center">
  <img src="docs/assets/razavi_3rollout_model_rows.png" alt="Razavi-bench 2026-06-26 test results" width="86%"/>
</p>
