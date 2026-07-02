# Experiment: 2026-06-26 direct-qa

This directory contains cleaned AI question-answer pairs from one Razavi-Bench
experiment.

## Experiment

- Run date: 2026-06-26
- Benchmark release: direct-mm-v4-newgolden
- Models: GPT-5.5 Thinking XHigh, Gemini 3.1 Pro CC Thinking High, Claude Opus
  4.8 Thinking Max
- Rollouts: 3 per model
- Records: 450 total, stored as 9 model-output JSONL files

## Files

- `model_outputs/`: cleaned GPT, Gemini, and Claude answer JSONL files, split
  by model family and rollout.
- `judge_outputs/`: per-answer judge model output JSONL files.
- `judge_scores/summary.csv`: rollout-aware aggregate score table for reports
  and plots.
- `tools/`: historical scripts used to generate this experiment's original
  `judge_outputs/*.jsonl`.
- `figures/`: MiniMax and DeepSeek score plots generated from
  `judge_scores/summary.csv`.

Each `model_outputs/*.jsonl` line is one JSON object with the effective
benchmark question, final visible model answer, run date, rollout number,
answer round count, model call count, and internet/tool evidence flag.
There are 9 files: 3 model families times 3 rollouts, with 50 records each.

The model output files exclude system prompts, process instructions, hidden
reasoning, Vela session IDs, provider metadata, token/cost data, and internal
record IDs.

`internet_or_tool_evidence` is `false` for every record in this experiment. The
original audit checked exposed tools/functions, structured tool calls, and
web-search request counters.

Judge outputs are stored separately under `judge_outputs/` because they are tied
to the rubric and golden answers used at judge time. If the rubric or golden
answers change, add a new judge output artifact under this experiment rather
than modifying the cleaned model output files.

`judge_scores/summary.csv` is derived from the judge outputs and keeps
model-family, rollout, judge-family, and Part 1/Part 2/overall aggregates. Use
it as the single summary source for reports and plots; use `judge_outputs/*.jsonl`
when per-answer scores and rationales are needed.

The judge scripts in this directory are kept as a reproducibility snapshot for
this experiment. New judge runs should generally use the repository-level
`tools/evaluate_answers.py` evaluator and store its metadata JSON with the new
judge outputs. The historical scripts read API keys from environment variables
or interactive input. They do not store credentials in the repository.

Examples:

```bash
python3 experiments/2026-06-26-direct-qa/tools/run_minimax_judge.py \
  --output-name minimax-m3-part1-001 \
  --task-slug part1-001-double-length-and-width-mosfet-its-intrinsic

python3 experiments/2026-06-26-direct-qa/tools/run_deepseek_judge.py \
  --output-name deepseek-gpt-r1-part1-001 \
  --task-slug part1-001-double-length-and-width-mosfet-its-intrinsic \
  --model-family gpt \
  --rollout 1
```

Generate the judge-score plots:

```bash
python3 experiments/2026-06-26-direct-qa/tools/plot_scores.py
```

This writes `figures/judge_scores_minimax.*` and
`figures/judge_scores_deepseek.*`. The bars show rollout means, black lines
show rollout min-to-max, and colored dots show the three rollout aggregates.

Regenerate the summary table before plotting:

```bash
python3 experiments/2026-06-26-direct-qa/tools/plot_scores.py --rebuild-summary
```

See `../../LICENSE` for dataset, code, and source-material terms.
