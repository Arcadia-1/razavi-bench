# 2026-10-08 Direct QA

Direct multimodal QA run generated with the public standalone runner,
`tools/direct_qa_openrouter.py`, and published with `tools/build_model_json.py`.

## Muse Spark 1.3

- Answer model: `meta/muse-spark-1.3` through OpenRouter Chat Completions
- Reasoning effort: max, the highest OpenRouter lists for this model
  (`max, xhigh, high, medium, low, minimal`); `max_tokens` 131,072
- Rollouts: 3 × 50 tasks, generation concurrency 20
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **86.67%** | **93.33%** | **76.67%** |

Rollout results are 85.00%, 88.00%, and 87.00%. Score distribution over 150
answers: 121 fours, 2 threes, 9 twos, 12 ones, 6 zeros. For comparison, Muse
Spark 1.2 at xhigh (its highest effort) scored 92.00%.

Two answers (`part2-008`, rollouts 1 and 3) first ended with a provider
`finish_reason=error` and were re-sampled automatically by the runner.

Usage covers all 150 slots, including the two discarded attempts: 304,516 input
tokens (8,588 cached reads), 1,409,004 output tokens (1,237,640 reasoning
tokens), and 1,713,520 total tokens. At OpenRouter's listed price ($1.25 input,
$0.15 cached input, $4.25 output per 1M tokens) the answer-model cost is about
$6.36; judge cost is excluded.

An earlier partial run at xhigh was stopped once it turned out that max is the
model's highest listed effort; none of its answers are published.

## Contents

- `muse-spark-1-3/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `muse-spark-1-3/judge_outputs/`: per-answer DeepSeek V4 Pro scores and
  rationales plus the judge metadata manifest

Per-answer token usage, including retried attempts, is published in
`docs/data/direct_qa/models/muse_spark_13.json`. Raw provider responses and
probe runs remain outside the repository.
