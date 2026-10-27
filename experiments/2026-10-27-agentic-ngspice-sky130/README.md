# 2026-10-27 Agentic ngspice-sky130

First run of the `ngspice-sky130` agentic mode on mini-swe-agent, generated
with `tools/run_agentic_miniswe.py`. It is a trial of the harness and is not
published on the website.

## Harness

- mini-swe-agent 2.4.6, set up like Artificial Analysis's Terminal-Bench 4.0
  runs: `DefaultAgent` with the `mini` config and prompts, the native bash
  tool, the full transcript with no compaction, at most 500 steps, and
  mini-swe-agent's defaults otherwise (30 s per command)
- One fresh Docker container per run, without network, built from
  `agentic/harness/miniswe-ngspice-sky130.Dockerfile`: ngspice 47 built from
  source, the Sky130 bundle in `/tools/ngspice-sky130`, and the skill in
  `/app/.claude/skills/ngspice-sky130`. Each task's `instruction.md` and
  figures are copied into `/app`; nothing else from the repository is in the
  container
- The figures are also attached to the agent's first message as images
- Only `/app/answer.md` is graded

## DeepSeek V4.1 Flash 1017

- Answer model: `deepseek-flash` through the official DeepSeek API, thinking
  enabled at reasoning effort max; `max_tokens` 131,072 per model call
- Rollouts: 3 × 50 tasks, 8 containers at a time; all 150 runs submitted an
  answer on the first attempt
- Judge: GPT-6 Luna at maximum reasoning effort through OpenRouter

| Mode | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| Agentic ngspice-sky130 (this run) | **87.50%** | **96.39%** | **74.17%** |
| Direct multimodal QA (2026-10-18, same judge) | 82.50% | 88.33% | 73.75% |

Rollout results are 84.50%, 90.50%, and 87.50%. Score distribution over 150
answers: 116 fours, 9 threes, 12 twos, 10 ones, 3 zeros.

The gain is in Part 1 and comes mostly from reading the figures, not from
simulation. In 79 of 150 runs the agent decoded the PNG itself with Python's
`zlib` and printed zoomed crops as text to check device types and connections.
That turned `part1-006` (a diode-connected PMOS) and `part1-015` (two NMOS
devices) from 0/0/0 in Direct QA into 4/4/4. ngspice ran in 81 runs. Those
runs scored 87.04%, against 88.04% for the 69 runs that did not simulate.
Several agents also searched the disk for the task's name. The container holds
nothing to find, so those searches came up empty.

Agents took a median of 17.5 steps (at most 68) and 253 s per run. Usage
across all 2,936 model calls: 107,839,903 input tokens (104,864,768 cached),
5,994,671 output tokens (5,094,836 reasoning). At DeepSeek's price used for
the Direct-QA entry ($0.15 input, $0.003 cached input, $0.60 output per 1M
tokens), the answer-model cost is about $4.36; judge cost is excluded.

## Contents

- `deepseek-v41-flash-1017/model_outputs/`: three 50-answer rollout JSONL
  files, with agent steps, exit status and ngspice command counts per answer
- `deepseek-v41-flash-1017/judge_outputs/gpt-6-luna-max.scores.jsonl`:
  per-answer GPT-6 Luna scores and rationales

Trajectories, raw logs, the judge's local metadata manifest and the validation
report stay local.
