# Evaluation Tools

This directory contains the current reusable Razavi-Bench evaluation utilities.

## `validate_visual_facts.py`

`validate_visual_facts.py` validates the 41 human-reviewed visual units in
`data/visual_facts.jsonl`. It checks task coverage, original image hashes, crop
bounds, translation integrity, and references to executable `.cir` files under
`netlists/`. It also rejects copied-image fields, stored topology
transcriptions, and the former natural-language connectivity fields.

```bash
python3 tools/validate_visual_facts.py
```

## `run_visual_ablation.py`

`run_visual_ablation.py` runs two independent ablations against an
OpenAI-compatible chat-completions endpoint. Neither mode reads golden
solutions or judge data.

In `visual-extraction` mode, every request contains one visual unit and a fixed
extraction prompt, without the benchmark question or reviewed facts. The tool
reads the original `tasks/` image and applies `crop_box` in memory, so the
repository does not store a second image copy. This mode requires Pillow:

```bash
python3 -m pip install Pillow
python3 tools/run_visual_ablation.py visual-extraction \
  --model PROVIDER_MODEL \
  --dry-run
```

In `circuit-reasoning` mode, the tool removes the Markdown image section from
each figure-bearing question, reads the mapped executable `.cir` files, and
derives their terminal-level topology together with the mapped visual-only
annotations. It omits explanatory comments, element values, parameter
assignments, simulator control blocks, and analysis directives, so neither
answer-oriented commentary nor simulation assumptions enter the prompt. Model
and subcircuit identifiers are retained where they identify a device type. The
topology view is generated at runtime from the repository's canonical
executable netlists; no second topology text is stored. The four text-only tasks
remain unchanged controls. English annotations are used by default;
`--facts-language zh` selects the reviewed Chinese source, and
`--facts-language bilingual` includes both languages.

```bash
python3 tools/run_visual_ablation.py circuit-reasoning \
  --model PROVIDER_MODEL \
  --facts-language en \
  --dry-run
```

Results from this mode must remain labeled as a netlist-based reasoning ablation
rather than a pure visual-facts or native-vision score.

For a real run, provide the endpoint and the name of an environment variable
containing its API key. The tool supports bounded concurrency, transient-failure
retries, separate raw responses, and answer-based resume:

```bash
export RAZAVI_VISUAL_ABLATION_API_KEY=...

python3 tools/run_visual_ablation.py circuit-reasoning \
  --base-url https://provider.example/v1 \
  --api-key-env RAZAVI_VISUAL_ABLATION_API_KEY \
  --model PROVIDER_MODEL \
  --rollout 1 --rollout 2 --rollout 3 \
  --output-dir WORK/visual-ablation/example \
  --resume
```

Outputs use `track=visual-extraction` or
`track=netlist-and-visual-annotations-circuit-reasoning`. They must not be
merged into official Direct or Agentic scores.

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

## `evaluate_answers.py`

`evaluate_answers.py` scores saved answer JSONL files after model generation.
It does not run models, agents, simulators, or Vela tasks.

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

Historical scripts under `experiments/<experiment>/tools/` are snapshots of the
code used for those experiments. Keep them with their experiment artifacts for
auditability, but use this directory for new scoring runs.
