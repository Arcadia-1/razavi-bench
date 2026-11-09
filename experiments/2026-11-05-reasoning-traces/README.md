# 2026-11-05 Reasoning traces and answer times

A side probe for the preprint's analysis of look-alike circuits and of cost
versus time. It does not change the leaderboard.

- Questions: Part 1 Q14 (CMOS inverter), Q15 (the same drawing with two NMOS
  devices), Q20 (NMOS cascode) and Q21 (the same shape with a PMOS source
  follower driving a common-gate stage)
- Models: 24 leaderboard models chosen to span the score range, including every
  model on the cost–score Pareto front, each with the reasoning effort and
  output limit of its published run
- Trials: 3 per question, 288 answers, streamed through OpenRouter on
  2026-11-05 with [`probe.py`](probe.py), which records the wall-clock time of
  every answer and the reasoning text (or provider-written reasoning summary)
  that 21 of the models return
- Judge: GPT-6 Luna at maximum reasoning effort, with
  `tools/evaluate_answers.py --model openai/gpt-6-luna --reasoning-effort max
  --max-tokens 128000 --json-mode`

On each of the four questions, the probe's mean score is within 3.5 points of
the published benchmark's for the same 24 models. All four questions' answers
were re-graded after their reference answers were revised on 2026-11-08 and
2026-11-09 (`../2026-11-08-luna-regrade-q15-q28-p2q5-p2q16/`,
`../2026-11-09-luna-regrade-13-questions/`,
`../2026-11-09-luna-regrade-21-questions/`):

| Question | Probe | Benchmark, same models |
|---|---:|---:|
| Q14 CMOS inverter | 97.2% | 99.7% |
| Q15 two NMOS devices | 47.2% | 46.9% |
| Q20 NMOS cascode | 97.9% | 98.3% |
| Q21 PMOS source follower into common gate | 41.0% | 39.2% |

Median answer times run from 4.9 s (GPT-4o 2024-11-20) to 341 s (Hy4). The
per-model medians, the GPT-6 Luna labels of each reasoning trace, and the
analysis scripts are in the paper repository (`analysis/timing.csv`,
`analysis/trace_labels.jsonl`, `analysis/paper_numbers/`).

## Contents

- `probe.py`: the probe
- `traces.jsonl`: one row per request with timing, token usage, reasoning text
  and answer
- `answers.jsonl`: the answers in the form `tools/evaluate_answers.py` reads
- `scores-gpt-6-luna-max.jsonl`: per-answer GPT-6 Luna scores and rationales
