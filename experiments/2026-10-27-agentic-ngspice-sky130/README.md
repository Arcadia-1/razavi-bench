# 2026-10-27 Agentic ngspice-sky130

First run of the `ngspice-sky130` agentic mode on mini-swe-agent, generated
with `tools/run_agentic_miniswe.py`. It is a trial of the harness and is not
published on the website. That standalone runner was retired once the Harbor
run below reproduced its score; agentic runs now go through Harbor
(`tools/export_harbor_tasks.py`), and the runner remains in the repository
history (commit `a4c5321`).

## Harness

- mini-swe-agent 2.4.6, set up like Artificial Analysis's Terminal-Bench 4.0
  runs: `DefaultAgent` with the `mini` config and prompts, the native bash
  tool, the full transcript with no compaction, at most 500 steps, and
  mini-swe-agent's defaults otherwise (30 s per command)
- One fresh Docker container per run, without network, built from
  `agentic/harness/miniswe-ngspice-sky130.Dockerfile` (since renamed
  `harbor-ngspice-sky130.Dockerfile`): ngspice 47 built from
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

## Harbor parity run (2026-10-30)

The same model and settings were run again through Harbor 0.25.0, to check
that Harbor reproduces the runner. The tasks came from
`tools/export_harbor_tasks.py --network public --preinstall mini-swe-agent`
(Docker Desktop cannot restrict egress, so the network was open and the
instruction asked the agent not to use the internet). The agent was
`agentic/harbor/razavi_mini_swe_agent.py`: the same mini-swe-agent 2.4.6
config, prompts and 500-step cap, with the figures attached as images. The run
used 8 trials at a time, 3 attempts per task. Each answer was graded in a
separate verifier container by the same GPT-6 Luna judge.

| Run | Overall | Part 1 | Part 2 | Per rollout or attempt |
|---|---:|---:|---:|---|
| Harbor | **87.83%** | 96.11% | 75.42% | 86.50%, 88.50%, 88.50% |
| Runner (above) | 87.50% | 96.39% | 74.17% | 84.50%, 90.50%, 87.50% |
| Direct QA | 82.50% | 88.33% | 73.75% | |

Harbor reproduces the runner: the overall scores differ by 0.33 points, less
than the spread between rollouts. 40 of the 50 tasks have the same mean score
in both, and the mean per-task difference is 0.11 on the 0–4 scale. The
`part1-006` and `part1-015` gains over Direct QA reappear. Behaviour matches
too: all 150 runs submitted, ngspice ran in 76 (runner: 81) and the agent
decoded a figure PNG itself in 75 (runner: 79), with a median of 14 steps
(runner: 17.5).

The two setups still differ in ways that did not move the score: Harbor runs
mini-swe-agent's CLI (its interactive agent in yolo mode) through LiteLLM,
where the runner drives `DefaultAgent` with direct HTTP calls, and Harbor's
container had network access. One attempt at `part2-007` used it to
`pip install` Pillow and OpenCV to read the figure; it scored 1, like every
other attempt at that task in both runs. No run looked anything up online.

39 answers could not be graded at first: the judge's OpenRouter calls returned
HTTP 403 for 33 minutes (07:21–07:54 UTC), and the verifier wrote no reward.
`harbor trial regrade` re-ran only their verifiers, with the same answers.
The run took 2 h 21 min. Usage: 103,380,518 input tokens (100,679,410
cached) and 5,664,170 output tokens, about $4.11 at the DeepSeek price above
(LiteLLM's own estimate is $8.21).

## Contents

- `deepseek-v41-flash-1017/model_outputs/`: three 50-answer rollout JSONL
  files, with agent steps, exit status and ngspice command counts per answer
- `deepseek-v41-flash-1017/judge_outputs/gpt-6-luna-max.scores.jsonl`:
  per-answer GPT-6 Luna scores and rationales
- `harbor-deepseek-v41-flash-1017/scores.jsonl`: the Harbor run's 150 scores
  and rationales, one row per trial, with the answer's SHA-256, agent steps
  and ngspice command count; the Harbor job directories stay local

Trajectories, raw logs, the judge's local metadata manifest and the validation
report stay local.
