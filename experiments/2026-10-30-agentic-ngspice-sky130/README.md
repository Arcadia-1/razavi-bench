# 2026-10-30 Agentic ngspice-sky130

GPT-6 Luna on the `ngspice-sky130` agentic mode through Harbor 0.25.0. It is
not published on the website, which lists Direct QA only.

## Setup

- Tasks: `tools/export_harbor_tasks.py --network public --preinstall
  mini-swe-agent --preinstall claude-code --preinstall codex --preinstall
  gemini-cli`. Docker Desktop cannot restrict egress, so the network was open
  and the instruction asked the agent not to use the internet.
- Agent: `agentic/harbor/razavi_mini_swe_agent.py` (mini-swe-agent 2.4.6 with
  its `mini` config and prompts, the native bash tool, the full transcript, at
  most 500 steps), with the figures attached as images
- Model: `openrouter/openai/gpt-6-luna` through LiteLLM, `reasoning.effort`
  max (sent in `extra_body`), `max_tokens` 128,000
- Trials: 3 per task, 8 at a time
- Judge: GPT-6 Luna at maximum reasoning effort, in a separate verifier
  container

## Results

| Run | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| GPT-6 Luna, agentic (this run) | **85.17%** | 91.67% | 75.42% |
| GPT-6 Luna, Direct QA (`2026-10-30-direct-qa`) | 83.00% | 90.56% | 71.67% |
| DeepSeek V4.1 Flash 1017, agentic (Harbor, `2026-10-27-agentic-ngspice-sky130`) | 87.83% | 96.11% | 75.42% |
| DeepSeek V4.1 Flash 1017, Direct QA | 82.50% | 88.33% | 73.75% |

The three attempts score 86.00%, 85.50% and 84.00%. Score distribution over
150 answers: 108 fours, 15 threes, 14 twos, 6 ones, 7 zeros.

The agentic mode adds 2.2 points to GPT-6 Luna's Direct QA score, against 5.3
for DeepSeek, though the two models are within half a point of each other in
Direct QA. Ten tasks improve, two get worse and 38 are unchanged. The gains
are mostly in Part 2: `part2-011` (2/2/2 to 3/3/3), `part2-008` (1/1/1 to
2/2/2) and `part2-003` (4/2/3 to 4/4/4), plus `part1-006` (4/2/4 to 4/4/4).
`part2-014` drops from 3/2/2 to 2/0/2 and `part2-016` moves from 2/2/3 to
3/2/1.

The two models use the sandbox differently. GPT-6 Luna simulates in 130 of
150 runs (DeepSeek: 76) and finishes in a median of 4.5 steps, at most 12
(DeepSeek: 14). It decoded the figure PNG itself in only 3 runs, where
DeepSeek did so in 75 to zoom in on device types and connections. That is
where DeepSeek's Part 1 gain came from, and GPT-6 Luna does not get it:
`part1-015` (two NMOS devices) stays at 0/0/0 in both of its modes, while
DeepSeek's agentic run scores 4/4/4. `part1-021` is 0/0/0 for both models.

All 150 runs submitted an answer, and none ran a command that uses the
network.

## Interruption

Docker Desktop stopped between 10:40 and 10:44 UTC. The 87 trials that started
in that window failed to build or start their containers, Harbor's two retries
each included. After restarting Docker, `harbor job resume -f RuntimeError`
re-ran those 87 and kept the 63 already graded; the `run` field in the score
file marks which is which.

The first pass took 39 min 34 s and the resume 50 min. Usage across the 150
trials: 4,920,877 input tokens (3,453,624 cached) and 2,908,292 output tokens,
about $1.64 at OpenRouter's GPT-6 Luna price ($0.10 input, $0.01 cached input,
$0.50 output per 1M tokens).

## Contents

- `harbor-gpt-6-luna/scores.jsonl`: the 150 scores and rationales, one row per
  trial, with the answer's SHA-256, agent steps, ngspice command count and
  whether the trial came from the first pass or the resume

The Harbor job directory, with trajectories and answers, stays local.
