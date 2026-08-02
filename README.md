---
license: other
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
| `agentic/` | Public agentic evaluation modes, harness examples, and skill assets |
| `netlists/` | Curated executable SPICE representations of the 38 unique schematic figures |
| `simulator/` | Reproducible ngspice and minimal Sky130 assets used by the netlists and agentic treatment |
| `experiments/` | Cleaned model outputs and per-experiment metadata |
| `tools/` | Current reusable evaluation utilities |
| `LICENSE` | License, source, and permission terms |

## Dataset Viewer Configs

This Hugging Face dataset exposes the benchmark task set as its structured
viewer config:

| Config | Rows | Description |
|---|---:|---|
| `tasks` | 50 | Benchmark prompts, golden solutions, part/question numbers, and local figure paths. |

Model rollout outputs and judge scores are kept under `experiments/` as
reproducibility artifacts, but they are not exposed as primary dataset configs.

## Task Format

Each `instruction.md` contains only the benchmark prompt and any local figure
reference. It intentionally excludes source metadata, original model answers,
scores, and explanatory commentary.

Each `golden_solution.md` contains the expected reasoning and final answer for
evaluation. The golden answers were reviewed against the source articles,
figures, and circuit analysis.

## Evaluation Tools

Use `tools/run_direct_qa.py` to collect direct multimodal answers from an
OpenAI-compatible endpoint, then use `tools/evaluate_answers.py` for scoring.
The evaluator accepts an answer JSONL, reads each task's `instruction.md` and
`golden_solution.md`, reads the repository-level `evaluation_rubric.md`, calls
a configured judge API, and writes score JSONL plus a metadata manifest.

The evaluator is intentionally separate from answer generation. Direct,
agentic, and simulator-assisted runs should first save final answers, then use
the same evaluator configuration for a comparable score pass.

## Experiments

`experiments/` contains cleaned model outputs and per-experiment metadata. The
`2026-06-26-direct-qa` experiment includes GPT, Gemini, and Claude
question-answer pairs from the direct-mm-v4-newgolden benchmark release. The
public files exclude system prompts, process
instructions, hidden reasoning, Vela session IDs, provider metadata, token/cost
data, and internal record IDs.

Automated judge scores, when present, are experiment metadata for transparency
and re-grading. They are not a substitute for independent expert review.
Historical experiment-specific scoring scripts live with the experiment that
produced the scores. New experiments should prefer the reusable evaluator in
`tools/` and store the generated judge metadata with the experiment outputs.

## Citation

If you use Razavi-Bench, please cite this repository:

```bibtex
@misc{zhang2026razavibench,
  title        = {Razavi-Bench: An Expert-Curated Benchmark for Analog-Design Reasoning},
  author       = {Zhishuai Zhang and Behzad Razavi},
  year         = {2026},
  howpublished = {\url{https://github.com/Arcadia-1/razavi-bench}},
  url          = {https://razavi-bench.tokenzhang.com/},
  note         = {Benchmark repository}
}
```

## Agentic Evaluation

`agentic/` defines public file-based evaluation modes for Razavi-bench:
direct multimodal QA, agentic multimodal QA, and an experimental
agentic-ngspice-sky130 mode. Shared simulator assets live under `simulator/`,
while independently curated schematic netlists live under `netlists/`. The
ngspice mode includes a skill guide so simulator use is reproducible and
constrained to supporting analog reasoning. All modes score the final answer,
not simulator logs or scratch files.

The 38 reference-assisted schematic groups under `netlists/` are independent
curation artifacts and must not be mounted into official benchmark runs. Each
deck documents its own topology, assumptions, analysis, and measured quantity.
Run all 59 decks without leaving generated files in the repository with:

```bash
python3 netlists/verify.py
```

## License

Razavi-Bench uses mixed license terms. See `LICENSE` for the full terms.

The benchmark includes or adapts source questions and figures from Behzad
Razavi's *Analog Design Experiments With AI* articles with permission from
Behzad Razavi. Original article, question, and figure copyrights remain with
their respective rights holders, including Behzad Razavi and/or IEEE, as
applicable. This permission does not grant third parties the right to
redistribute, rehost, repackage, or incorporate the benchmark materials into
other benchmark or dataset releases.

Benchmark materials, including tasks, prompts, figures, source PDFs, golden
solutions, evaluation rubrics, judge prompts, model outputs, score tables,
metadata, derived datasets, dashboard-embedded benchmark data, and benchmark
documentation, are made available for public viewing, citation, non-commercial
research reference, and local evaluation from this repository only. They may not
be redistributed, sublicensed, mirrored, republished, used for model training or
fine-tuning, or incorporated into third-party benchmarks, datasets,
leaderboards, training sets, or evaluation suites without prior written
permission.

Software code in this repository is licensed under the Apache License, Version
2.0. The Apache License applies only to software code and not to benchmark
materials or third-party copyrighted content.

## Notes

The user request originally mentioned 40 questions for Part 1, but the available
Part 1 article contains Q1 through Q30. No synthetic questions were added.

## References

- B. Razavi, "Analog Design Experiments With AI—Part 1 [The Analog Mind]," in
  IEEE Solid-State Circuits Magazine, vol. 17, no. 4, pp. 11-15, Fall 2025.
- B. Razavi, "Analog Design Experiments With AI—Part 2 [The Analog Mind]," in
  IEEE Solid-State Circuits Magazine, vol. 18, no. 2, pp. 8-13, Spring 2026.

## Multimodal QA Results

The `2026-06-26-direct-qa` baseline and later multimodal QA follow-ups each
evaluate answer models over three rollouts of all 50 Razavi-bench tasks. Every
answer is scored by MiniMax M3 and DeepSeek V4 Pro. The table below reports the
judge-specific June 26 baseline with the `2026-07-19-part1-q15-score-correction`
overlay applied to Part 1 Q15; all non-Q15 task scores are unchanged.

| Answer Model | Judge Model | Overall | Part 1 First 30 | Part 2 Last 20 |
|---|---|---:|---:|---:|
| Claude | MiniMax-M3 | 87.00% | 92.50% | 78.75% |
| Claude | DeepSeek-V4-Pro | 88.50% | 92.50% | 82.50% |
| GPT | MiniMax-M3 | 79.50% | 85.83% | 70.00% |
| GPT | DeepSeek-V4-Pro | 80.17% | 84.17% | 74.17% |
| Gemini | MiniMax-M3 | 79.67% | 88.89% | 65.83% |
| Gemini | DeepSeek-V4-Pro | 81.83% | 91.11% | 67.92% |

The current active aggregate below is the August 2 snapshot. Each value is the
mean of DeepSeek V4 Pro and MiniMax M3 scores over three rollouts, with the Q15
hard-rule correction applied consistently.

| Rank | Answer Model | Thinking Effort | Overall | Part 1 | Part 2 |
|---:|---|---|---:|---:|---:|
| 1 | Claude Opus 5 | high | 94.00% | 98.33% | 87.50% |
| 2 | Claude Opus 5 | xhigh | 93.25% | 95.42% | 90.00% |
| 3 | Claude Fable 5 | max | 92.25% | 95.83% | 86.88% |
| 4 | Claude Opus 5 | max | 92.17% | 95.00% | 87.92% |
| 5 | Claude Opus 5 | medium | 88.83% | 92.78% | 82.92% |
| 6 | Claude Opus 4.8 | max | 87.75% | 92.50% | 80.62% |
| 7 | Qwen 3.8 Max Preview | default | 87.42% | 97.92% | 71.67% |
| 8 | Gemini 3.5 Flash | default | 87.42% | 95.69% | 75.00% |
| 9 | GPT 5.6 Sol | max | 85.92% | 91.81% | 77.08% |
| 10 | Gemini 3.6 Flash | default | 85.92% | 92.92% | 75.42% |

<p align="center">
  <img src="docs/assets/direct_qa_rollout_mean_all_metrics.png?v=20260802-gemma-4-31b-it" alt="2026-08-02 Razavi-Bench Multimodal QA snapshot" title="2026-08-02 Razavi-Bench Multimodal QA snapshot" width="92%"/>
</p>

The release-date view uses vendor announcements where available and explicitly
marks preview or first-public-availability dates in the
[model release-date table](docs/data/direct_qa/model_release_dates.csv).

<p align="center">
  <img src="docs/assets/direct_qa_score_vs_release_date.png?v=20260802-large-type" alt="Razavi-Bench score versus model release date" title="Razavi-Bench score versus model release date" width="96%"/>
</p>
