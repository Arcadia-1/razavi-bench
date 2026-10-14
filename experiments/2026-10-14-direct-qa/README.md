# 2026-10-14 Direct QA

Direct multimodal QA runs, published with `tools/build_model_json.py`. Gemini 4
Argon was generated with `tools/direct_qa_openrouter.py`; Muse Wonder Full 1.0
with `tools/direct_qa_muse_code.py` through the local Muse Code CLI.

## Gemini 4 Argon

- Answer model: `google/gemini-4-argon` through OpenRouter Chat Completions
- Reasoning effort: high, the highest OpenRouter lists for this model
  (`high, medium, low`), resolved by the runner from `--effort top`
- `max_tokens` 65,536, the model's output limit
- Rollouts: 3 × 50 tasks, generation concurrency 20
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **95.83%** | **99.44%** | **90.42%** |

Rollout results are 96.00%, 95.50%, and 96.00%. Score distribution over 150
answers: 134 fours, 8 threes, 7 twos, 1 one, no zeros. Every answer finished on
its first attempt.

Usage covers all 150 answers: 163,656 input tokens (no cached reads reported),
766,592 output tokens (563,532 reasoning tokens), and 930,248 total tokens. At
OpenRouter's listed price ($2.00 input, $0.10 cached input, $10.00 output per
1M tokens) the answer-model cost is about $7.99; judge cost is excluded.

## Muse Wonder Full 1.0

- Answer model: `muse-wonder-full-1.0` through the local Muse Code CLI
  (`muse exec`, version 1.4.7), on a Muse Code subscription
- Reasoning effort: max (`ultra` is listed by the CLI but not enabled for the
  account; the runner stops if an effort is downgraded)
- One model call per answer with the figure attached: shell, file writes, web
  tools and reminder agents disabled, `--max-model-steps 1`, contributor mode off
- Rollouts: 3 × 50 tasks, generation concurrency 6
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **88.67%** | **95.28%** | **78.75%** |

Rollout results are 90.50%, 89.50%, and 86.00%. Score distribution over 150
answer slots: 123 fours, 2 threes, 13 twos, 8 ones, 4 zeros.

Muse Code is a coding agent, and the model sometimes spent its single allowed
step trying to call a tool instead of answering. Such attempts were discarded
and re-sampled: ten slots finished on a second sample, and `part1-015` in
rollout 2 tried a tool in all eight attempts, so it is published as unanswered
with score 0 and was not sent to the judge (149 judged answers plus that slot).

Every call carries Muse Code's own system prompt (about 22k tokens), so input
tokens dominate. Usage covers all 150 slots, including every discarded attempt:
3,960,596 input tokens (698,376 cached reads), 1,112,582 output tokens
(1,001,066 reasoning tokens), and 5,073,178 total tokens. Priced at
OpenRouter's Muse Wonder rate ($4.00 input, $0.20 cached input, $20.00 output
per 1M tokens) this is about $35.44; the run itself used the subscription, and
judge cost is excluded. Muse Code does not report the effort it applied, and
whether OpenRouter's `meta/muse-wonder` is the same model as
`muse-wonder-full-1.0` is not stated by either side.

## Contents

- `<model>/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `<model>/judge_outputs/`: per-answer DeepSeek V4 Pro scores and rationales
  plus the judge metadata manifest

Per-answer token usage, including discarded attempts, is published in
`docs/data/direct_qa/models/<model_key>.json`. Raw provider responses, Muse Code
session logs and probe runs remain outside the repository.
