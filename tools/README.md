# Evaluation Tools

This directory contains the current reusable Razavi-Bench evaluation utilities.

## `export_tasks.py`

`export_tasks.py` rebuilds `data/tasks.jsonl` and `docs/data/tasks.jsonl` from
`tasks/`. Each row's `prompt` is exactly the text a model is sent, the "## Question"
section of `instruction.md`; its `figures` follow it in the same message. Every
runner here builds its request from these two fields. Re-run it after editing a task.

## `run_direct_qa.py`

`run_direct_qa.py` runs direct multimodal QA against an OpenAI-compatible
chat-completions endpoint. For every selected rollout, it sends the "## Question"
section of each task's `instruction.md` followed by the task's figures, the message
described in the top-level README, and saves only the final visible answer in the
public output JSONL. Full provider responses
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

The request leaves the sampling temperature to the provider unless
`--temperature` is given; pass `--temperature 0` to repeat an earlier
temperature-0 run of a non-reasoning model under the same settings.

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

The same runner calls other OpenAI-format APIs with `--provider`. With
`--provider deepseek` it uses `https://api.deepseek.com` and `DEEPSEEK_API_KEY`,
sends effort as `reasoning_effort` with thinking enabled, and accepts only
`max`, `high` and `low` (`top` is `max`), because DeepSeek silently maps other
efforts, e.g. `xhigh` to `high`.

With `--provider moonshot` it calls the Kimi API (`https://api.moonshot.ai/v1`,
`MOONSHOT_API_KEY`) and sends `reasoning_effort`; thinking cannot be turned off,
and Kimi silently treats an unknown effort as the default, so only `max`, `high`
and `low` are accepted (`top` is `max`).

With `--provider minimax` it calls MiniMax's mainland platform
(`https://api.minimaxi.com/v1`, `MINIMAX_API_KEY`; Token Plan keys work there)
and sends `reasoning_effort` (`max`, `xhigh`, `high`, `medium`, `low`; `top` is
`max`). Thinking is always on and MiniMax rejects unknown efforts.

With `--provider nvidia` it calls NVIDIA's API catalog
(`https://integrate.api.nvidia.com/v1`, `NVIDIA_API_KEY`). Nemotron models switch
reasoning through the chat template, so the efforts are `high` (full thinking,
`top`), `medium` (`medium_effort`) and `none`, and requests use the model card's
reasoning sampling (temperature 1.0, top_p 0.95).

Raw logs, API responses, credentials, and local output directories should stay
out of version control. The public repository contains only code and selected
metadata; it does not contain local run artifacts.

## Muse Code Direct-QA runner

`direct_qa_muse_code.py` runs Meta models through the local Muse Code CLI
(`muse exec`) on a Muse Code subscription and writes the same files as the
OpenRouter runner, so judging and publishing are unchanged. Because Muse Code is
a coding agent, each answer is locked down to one direct model call: shell,
file writes, web tools and reminder agents are disabled and runs are capped at
one model step. An attempt counts only if it completes with a non-empty answer
from exactly one model call; otherwise (typically when the model tries to call a
tool) it is re-sampled up to `--max-retries` times. The runner stops if Muse
Code downgrades the requested effort. Each call also sets `endpoint_transport`
to null for that run only (`-c endpoint_transport=null`), so an override in
`~/.config/muse/settings.json`, such as one written by a local model gateway,
cannot redirect requests away from Meta's API; the file itself is not changed.
Token usage is read from Muse Code's session logs under
`~/.local/share/muse/sessions`.

```bash
python3 tools/direct_qa_muse_code.py run \
  --output-dir experiments/my-muse-run \
  --output-prefix muse-code-my-model-max \
  --model muse-wonder-full-1.0 \
  --model-name "My Model" \
  --experiment 2026-01-01-direct-qa \
  --run-date 2026-01-01 \
  --effort max \
  --rollout 1 --rollout 2 --rollout 3 \
  --concurrency 6 \
  --resume
```

Pass `--route muse_code_exec` to `build_model_json.py` for these runs.

## Agentic runs on Harbor

The agentic modes in [`agentic/README.md`](../agentic/README.md) run on
[Harbor](https://github.com/harbor-framework/harbor) 0.25 with Docker.
`export_harbor_tasks.py` writes the 50 tasks as Harbor tasks, one directory
each under `output/harbor/<mode>/` (not committed):

- `instruction.md`: the question (the task's `prompt`, with no title or figure
  numbers), the mode's environment notes and the deliverable, `/app/answer.md`;
- `environment/`: the mode's image (`agentic/harness/harbor-<mode>.Dockerfile`;
  for `ngspice-sky130`, ngspice 47 built from source, the Sky130 bundle and the
  skill) plus, in `/app`, the question as `instruction.md` and the figure as
  `figure-1.png`, not named by the article's figure number;
- `tests/`: a separate verifier container with the golden solution, the rubric
  and `evaluate_answers.py`. It grades `/app/answer.md`, the task's only
  artifact, with GPT-6 Luna at max effort and writes the score divided by 4 as
  the reward (a missing answer scores 0 with no judge call).

Golden solutions never enter the agent's container. With the default
`--network allowlist`, the agent reaches only the model API while it runs and
the verifier only the judge API. That needs a sandbox that can switch network
policy after start; Docker Desktop cannot (its kernel lacks nftables FIB
support), so on a Mac export with `--network public`, which leaves the network
open and asks the agent in the instruction not to use the internet.

The reference agent is `agentic/harbor/razavi_mini_swe_agent.py`: Harbor's
mini-swe-agent set up the way Artificial Analysis runs Terminal-Bench 4.0
(mini-swe-agent 2.4.6 with its `mini` config and prompts, the native bash tool,
the full transcript with no compaction, at most 500 steps), with the figures
attached as images. A bash-only agent cannot look at a PNG, and Harbor passes
the task as one command-line argument, too small for a figure's base64, so the
agent uploads `mini_with_figures.py` and starts mini-swe-agent through it; the
script adds each figure in `/app` as a mini-swe-agent multimodal tag before
the instruction's Environment section. It also adds the `mcp` package after
Harbor's install: Harbor 0.25 installs LiteLLM without its proxy extra, but
LiteLLM's tool-calling path imports the MCP client, so every model call fails
without it. DeepSeek V4.1 Flash 1017 scored the same with this agent as with
the standalone runner it replaced (87.83% against 87.50%; see
`experiments/2026-10-27-agentic-ngspice-sky130`).

Harbor installs every agent inside the container on every run, which fails on
an unreliable connection. `--preinstall <agent>` (repeatable) builds the agent
into the task image once instead, in layers before the task files so all tasks
share them, and the run downloads nothing. For mini-swe-agent that is Harbor's
own toolchain (uv 0.13.6, Python 3.12) with mini-swe-agent 2.4.6, LiteLLM
1.106.4 and `mcp` pinned; the agent class then skips Harbor's install.

```bash
python3 tools/export_harbor_tasks.py --network public \
  --preinstall mini-swe-agent --preinstall claude-code --preinstall codex --preinstall gemini-cli
PYTHONPATH=agentic/harbor harbor run -y \
  -p output/harbor/ngspice-sky130-public \
  --agent razavi_mini_swe_agent:RazaviMiniSweAgent \
  -m deepseek/deepseek-flash \
  --ak 'config={"model": {"model_kwargs": {"thinking": {"type": "enabled"}, "extra_body": {"reasoning_effort": "max"}, "max_tokens": 131072}}}' \
  -o output/harbor-jobs -n 4 -k 3
```

`DEEPSEEK_API_KEY` and `OPENROUTER_API_KEY` (for the judge) must be set.
LiteLLM, which mini-swe-agent uses here, turns a top-level `reasoning_effort`
into "thinking on" for DeepSeek, so the effort level goes in `extra_body`.
`harbor trial regrade <trial dir> -p <task dir>` re-runs only the verifier on
a recorded trial; it also needs `PYTHONPATH=agentic/harbor`.

Gemini runs through Harbor's own `gemini-cli` agent, which reads the figures
from `/app` itself. Harbor installs Gemini CLI on every run by fetching nvm
from GitHub, Node from nodejs.org and the CLI from npm, which fails on an
unreliable connection. Export with `--preinstall gemini-cli` to build Node
22.23.4 (checksum-pinned) and Gemini CLI 0.65.0 into the task image once, with
retries, and run `agentic/harbor/razavi_gemini_cli.py`, which skips Harbor's
install when `gemini` is already there. `GEMINI_FORCE_OAUTH=1` uses the Mac's
"Login with Google" credentials (`~/.gemini/oauth_creds.json`); Harbor copies
them into the container for the run and deletes them afterwards. Gemini CLI
cannot log in non-interactively, so the local login must be current: run
`gemini` once in a terminal if it has lapsed. Google refuses Gemini CLI for
free "Gemini Code Assist for individuals" accounts (`IneligibleTierError`,
pointing to Antigravity), so those need a `GEMINI_API_KEY` instead.

```bash
GEMINI_FORCE_OAUTH=1 PYTHONPATH=agentic/harbor harbor run -y \
  -p output/harbor/ngspice-sky130-public \
  --agent razavi_gemini_cli:RazaviGeminiCli -m gemini/gemini-3.1-pro-preview \
  -o output/harbor-jobs -n 4 -k 3 --max-retries 2
```

Codex runs through Harbor's own `codex` agent, which views the figures with
its `view_image` tool. `--preinstall codex` builds Codex CLI 0.165.0 and
ripgrep into the image (sharing the Node layer with `gemini-cli`), and Harbor
then skips its own install. `CODEX_FORCE_AUTH_JSON=1` uses the Mac's ChatGPT
login (`~/.codex/auth.json`). Harbor copies it into the container and never
writes it back, so if Codex refreshes the login there, the Mac's copy may stop
working and need `codex login`.

```bash
CODEX_FORCE_AUTH_JSON=1 harbor run -y \
  -p output/harbor/ngspice-sky130-public \
  -a codex -m openai/gpt-6-astra --ak reasoning_effort=max \
  -o output/harbor-jobs -n 4 -k 3 --max-retries 2
```

Claude Code runs through Harbor's own `claude-code` agent, which reads the
figures with its Read tool. `--preinstall claude-code` builds Claude Code
2.1.198 into the image, and Harbor skips its install when the requested
`version` matches. Pointed at Moonshot's Anthropic-compatible endpoint, it runs
Kimi:

```bash
harbor run -y \
  --path=output/harbor/ngspice-sky130-public \
  --agent=claude-code \
  --model='kimi-31-pro-nuvora[1m]' \
  --agent-kwarg=version=2.1.198 \
  --agent-kwarg=disallowed_tools=EnterPlanMode,EnterWorktree,ExitPlanMode,ExitWorktree,AskUserQuestion \
  --agent-env=ANTHROPIC_MODEL='kimi-31-pro-nuvora[1m]' \
  --agent-env=ANTHROPIC_DEFAULT_FABLE_MODEL='kimi-31-pro-nuvora[1m]' \
  --agent-env=ANTHROPIC_DEFAULT_OPUS_MODEL='kimi-31-pro-nuvora[1m]' \
  --agent-env=ANTHROPIC_DEFAULT_SONNET_MODEL='kimi-31-pro-nuvora[1m]' \
  --agent-env=ANTHROPIC_DEFAULT_HAIKU_MODEL='kimi-31-pro-nuvora[1m]' \
  --agent-env=CLAUDE_CODE_SUBAGENT_MODEL='kimi-31-pro-nuvora[1m]' \
  --agent-env=CLAUDE_CODE_AUTO_COMPACT_WINDOW='1048576' \
  --agent-env=CLAUDE_CODE_EFFORT_LEVEL='max' \
  --agent-env=FORCE_AUTO_BACKGROUND_TASKS='1' \
  --agent-env=ENABLE_BACKGROUND_TASKS='1' \
  --agent-env=ENABLE_TOOL_SEARCH='false' \
  --agent-env=IS_SANDBOX='1' \
  --agent-env=API_TIMEOUT_MS='12000000' \
  --agent-env=BUN_CONFIG_HTTP_IDLE_TIMEOUT='2000' \
  --agent-env=CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1' \
  --agent-env=ANTHROPIC_BASE_URL='https://api.moonshot.ai/anthropic' \
  --agent-env=ANTHROPIC_API_KEY="$MOONSHOT_API_KEY" \
  -o output/harbor-jobs -n 4 -k 3 --max-retries 2
```

Pass keys from the environment, as above, rather than literally: Harbor redacts
them in the job's saved config, but a literal key stays in the shell history.

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

The standard Razavi-Bench judge is GPT-6 Luna at maximum reasoning effort,
called through OpenRouter, so one `OPENROUTER_API_KEY` covers both generation
and grading. Every published answer was re-graded with it on 2026-10-27; at
about $0.0012 per answer, a 150-answer run costs roughly $0.20 to grade:

```bash
python3 tools/evaluate_answers.py \
  --input experiments/my-openrouter-full/judge_input.jsonl \
  --output experiments/my-openrouter-full/judge_outputs/gpt-6-luna-max.scores.jsonl \
  --api-url https://openrouter.ai/api/v1/chat/completions \
  --model openai/gpt-6-luna \
  --api-key-env OPENROUTER_API_KEY \
  --json-mode --reasoning-effort max \
  --max-tokens 128000 --timeout 1800 --concurrency 15 --resume
```

Earlier entries were graded by DeepSeek V4 Pro with reasoning disabled
(`tools/run_deepseek_v4_pro.py`, or `--model deepseek/deepseek-v4-pro
--thinking-mode disabled --openrouter-reasoning` through OpenRouter); those
scores stay in the model files under `deepseek_v4_pro` for audit.

To add a judge's scores for already-published models, write one score file per
model and import them, then make that judge active:

```bash
python3 tools/add_judge_scores.py --judge-key gpt_6_luna_max \
  --judge-model openai/gpt-6-luna --scores-dir path/to/scores --suffix .scores.jsonl
python3 tools/apply_active_judge.py --judge gpt_6_luna_max
node tools/aggregate_questions.js
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
  --scores experiments/my-openrouter-full/judge_outputs/gpt-6-luna-max.scores.jsonl \
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
QA data (default: `gpt_6_luna_max`). It sets every answer's `active_score` from
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
