# Evaluation Tools

This directory contains the current reusable Razavi-Bench evaluation utilities.

## `run_direct_qa.py`

`run_direct_qa.py` runs direct multimodal QA against an OpenAI-compatible
chat-completions endpoint. For every selected rollout, it reads each task's
`instruction.md`, places any PNG figures before the prompt text, and saves only
the final visible answer in the public output JSONL. Full provider responses
are written to a separately selected local directory and should not be
committed.

The runner supports bounded concurrency, retries, and resume from existing
non-empty answers. API keys are read only from an environment variable.

```bash
export RAZAVI_DIRECT_API_KEY=...

python3 tools/run_direct_qa.py \
  --base-url https://example.com/v1 \
  --model example-multimodal-model \
  --model-name "Example Model" \
  --model-family example \
  --experiment 2026-01-01-direct-qa \
  --run-date 2026-01-01 \
  --output-dir experiments/2026-01-01-direct-qa/model_outputs \
  --output-prefix example-model \
  --raw-dir ../razavi-bench-private/example-model/raw-responses \
  --rollout 1 --rollout 2 --rollout 3 \
  --concurrency 4 \
  --resume
```

The public metadata records that raw responses were retained locally, but does
not record their machine-specific path.

## Standalone OpenRouter Direct-QA Suite

`direct_qa_openrouter.py` is a self-contained, standard-library-only runner for
OpenRouter-compatible Chat Completions endpoints. It has no private SDK or
internal-service dependency. The API key is read only from an environment
variable and is never written to output files.

Run the default text-plus-image probe:

```bash
export OPENROUTER_API_KEY=...
python3 tools/direct_qa_openrouter.py probe \
  --output-dir experiments/my-openrouter-smoke \
  --output-prefix my-model \
  --model google/my-model \
  --model-name "My Model" \
  --model-family google \
  --experiment 2026-01-01-openrouter-smoke \
  --run-date 2026-01-01 \
  --effort top \
  --max-tokens 131072
```

Run the full 50-task, three-rollout evaluation:

```bash
python3 tools/direct_qa_openrouter.py run \
  --output-dir experiments/my-openrouter-full \
  --output-prefix my-model \
  --model google/my-model \
  --model-name "My Model" \
  --model-family google \
  --experiment 2026-01-01-openrouter-full \
  --run-date 2026-01-01 \
  --rollout 1 --rollout 2 --rollout 3 \
  --effort top \
  --max-tokens 131072 \
  --concurrency 20 \
  --resume
```

Before any paid call, the runner checks `--effort` against the efforts
OpenRouter lists for the model (`reasoning.supported_efforts` in its public
model list), because OpenRouter silently maps an unsupported effort to the
nearest supported one. `top` (the default) picks the highest listed effort; an
explicit effort must be one the model lists, and one below the highest still
runs (e.g. to compare several efforts) but prints a notice. The resolved effort
and the listed efforts are recorded in `validation_report.json`. Pass
`--skip-effort-check` only for endpoints that are not OpenRouter.

The runner writes public answer JSONL, a redacted raw audit log, and a
validation report under the selected output directory. Audit an existing run
without making network requests:

```bash
python3 tools/direct_qa_openrouter.py audit \
  --output-dir experiments/my-openrouter-full \
  --output-prefix my-model \
  --effort max \
  --rollout 1 --rollout 2 --rollout 3
```

`audit` takes the effort the run resolved to (see `validation_report.json`).

Raw logs, API responses, credentials, and local output directories should stay
out of version control. The public repository contains only code and selected
metadata; it does not contain local run artifacts.

## `evaluate_answers.py`

`evaluate_answers.py` scores saved answer JSONL files after model generation.
It does not run models, agents, simulators, or internal tasks.

Input rows must contain at least:

```json
{"task_path": "tasks/part1-006-device-act-as-current-source", "answer": "..."}
```

The evaluator loads:

- `tasks/<task>/instruction.md`
- `tasks/<task>/golden_solution.md`
- `evaluation_rubric.md`

and sends the question, candidate answer, golden solution, and rubric to a
configured judge API. It writes:

- score JSONL, one row per input answer;
- a metadata JSON manifest beside the score file by default.

The metadata records the repository commit, dirty status, rubric hash, judge
script hash, judge system-prompt hash, API format, judge model, and runtime
parameters. This lets old scores remain interpretable even if the evaluator is
later improved.

Example with an OpenAI-compatible chat-completions endpoint:

```bash
export RAZAVI_JUDGE_API_KEY=...

python3 tools/evaluate_answers.py \
  --input experiments/my-run/model_outputs/answers.jsonl \
  --output experiments/my-run/judge_outputs/my-judge.jsonl \
  --api-url https://example.com/v1/chat/completions \
  --api-format chat-completions \
  --model my-judge-model \
  --json-mode \
  --resume
```

If the judge service uses the Responses API shape, use:

```bash
python3 tools/evaluate_answers.py \
  --input experiments/my-run/model_outputs/answers.jsonl \
  --output experiments/my-run/judge_outputs/my-judge.jsonl \
  --api-url https://example.com/v1/responses \
  --api-format responses \
  --model my-judge-model \
  --resume
```

For the standard Razavi-Bench DeepSeek V4 Pro judge, use the public launcher so
the endpoint, model, key environment variable, JSON mode, and disabled thinking
mode are consistent:

```bash
export DEEPSEEK_API_KEY=...
python3 tools/run_deepseek_v4_pro.py \
  --input experiments/my-openrouter-full/judge_input.jsonl \
  --output experiments/my-openrouter-full/judge_outputs/deepseek-v4-pro.jsonl \
  --concurrency 6 \
  --resume
```

The judge can also run through OpenRouter, so one `OPENROUTER_API_KEY` covers
both generation and grading. Recent runs use DeepSeek V4 Pro there with
reasoning disabled:

```bash
python3 tools/evaluate_answers.py \
  --input experiments/my-openrouter-full/judge_input.jsonl \
  --output experiments/my-openrouter-full/judge_outputs/deepseek-v4-pro.scores.jsonl \
  --api-url https://openrouter.ai/api/v1/chat/completions \
  --model deepseek/deepseek-v4-pro \
  --api-key-env OPENROUTER_API_KEY \
  --json-mode --thinking-mode disabled --openrouter-reasoning \
  --max-tokens 8192 --concurrency 5 --resume
```

## `build_model_json.py`

`build_model_json.py` turns a finished run into the website's model file,
`docs/data/direct_qa/models/<model_key>.json`. It merges the answer JSONL files,
the judge's score JSONL, and token usage, and refuses to write anything unless
every task has an answer, a score, and usage in every rollout and each score's
answer hash matches. Token usage comes from the runner's local `raw_logs.jsonl`
(`--raw-log`) or from a public manifest keyed `"<rollout>:<task_slug>"`
(`--tokens`).

```bash
python3 tools/build_model_json.py \
  --model-key my_model \
  --display-name "My Model" \
  --provider google \
  --effort high \
  --api-model google/my-model \
  --source-experiment 2026-01-01-openrouter-full \
  --configuration-note "My Model answered all 50 tasks in three rollouts through OpenRouter at high reasoning effort. Answers were graded by DeepSeek V4 Pro with reasoning disabled." \
  --answers experiments/my-openrouter-full/model_outputs/my-model-rollout-1.jsonl \
  --answers experiments/my-openrouter-full/model_outputs/my-model-rollout-2.jsonl \
  --answers experiments/my-openrouter-full/model_outputs/my-model-rollout-3.jsonl \
  --scores experiments/my-openrouter-full/judge_outputs/deepseek-v4-pro.scores.jsonl \
  --raw-log experiments/my-openrouter-full/raw_logs.jsonl
```

If a slot still has no answer after re-running it (for example, the model keeps
spending its whole `max_tokens` budget reasoning), pass
`--unanswered <rollout>:<task_slug>` to publish it as unanswered with score 0;
the tokens of its failed attempts in the raw log are still billed.

Then, to publish:

1. add the model's API price to `docs/assets/pricing.js` (keyed by `model_key`);
2. add a release-date row to `docs/data/direct_qa/model_release_dates.csv` and
   run `python3 tools/plot_model_release_timeline.py`;
3. run `python3 tools/apply_active_judge.py` and `node tools/aggregate_questions.js`.

Historical scripts under `experiments/<experiment>/tools/` are snapshots of the
code used for those experiments. Keep them with their experiment artifacts for
auditability, but use this directory for new scoring runs.

## `apply_active_judge.py`

`apply_active_judge.py` makes one judge authoritative for the published Direct
QA data (default: `deepseek_v4_pro`). It sets every answer's `active_score` from
that judge, recomputes each model's summaries, including per-rollout scores for
each part (`summary.by_rollout_part`), rewrites `docs/data/direct_qa/models/` and
`index.json`, and re-ranks the index. New model JSON files are added to the
index automatically. Other judges' scores are kept for audit.
Run it after publishing new results, then refresh the question files:

```bash
python3 tools/apply_active_judge.py
node tools/aggregate_questions.js
```

## `plot_rollout_scores.py`

`plot_rollout_scores.py` draws two figures from `index.json`, each with one dot
per rollout: `docs/assets/direct_qa_rollout_mean_all_metrics.png`
(Overall, Part 1 and Part 2 per model) and
`docs/assets/direct_qa_rollout_mean_overall.png` (Overall only).

## `build_task_thumbnails.py`

`build_task_thumbnails.py` shrinks each task's first figure into
`docs/assets/task-thumbs/` for the homepage task cards and records their sizes in
`docs/data/task_thumbnails.json`. Re-run it after adding or changing figures.
