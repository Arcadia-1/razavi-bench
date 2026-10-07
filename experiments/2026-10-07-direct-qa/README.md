# 2026-10-07 Direct QA

Direct multimodal QA runs generated with the public standalone runner,
`tools/direct_qa_openrouter.py`, and published with `tools/build_model_json.py`.

## Mistral Large 4

- Answer model: `mistralai/mistral-large-4-0` through OpenRouter Chat Completions
- Reasoning effort: max; `max_tokens` 131,072
- Rollouts: 3 × 50 tasks, generation concurrency 20
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **79.83%** | **88.06%** | **67.50%** |

Rollout results are 78.00%, 79.50%, and 82.00%. Score distribution over 150
answers: 103 fours, 7 threes, 10 twos, 26 ones, 4 zeros.

Three answer slots needed a second sample: two rollout-2 answers ended with a
provider `finish_reason=error`, and one rollout-3 answer spent the whole 131,072
token budget reasoning (`finish_reason=length`). Each was re-sampled once and
then finished normally. The runner now retries such responses automatically.

Usage covers all 150 slots, including the three discarded attempts: 243,853
input tokens (2,008 cached reads), 2,719,959 output tokens (2,291,585 reasoning
tokens), and 2,963,812 total tokens. At OpenRouter's listed price ($0.68 input,
$0.07 cached input, $2.09 output per 1M tokens) the answer-model cost is about
$5.85; judge cost is excluded.

## Claude Haiku 5.5

- Answer model: `anthropic/claude-haiku-5.5` through OpenRouter Chat Completions
- Reasoning effort: max; `max_tokens` 128,000 (the model's output limit)
- Rollouts: 3 × 50 tasks, generation concurrency 10
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **87.67%** | **96.67%** | **74.17%** |

Rollout results are 90.50%, 86.00%, and 86.50%. Score distribution over 150
answer slots: 120 fours, 5 threes, 8 twos, 15 ones, 2 zeros.

Haiku 5.5 sometimes reasons until it hits the 128,000-token output limit and
returns no answer (`finish_reason=length`). Three slots did so in the main run.
Two finished on a second sample. The third, `part2-016` in rollout 2, was cut
off in all four attempts, so it is published as unanswered with score 0 and
was not sent to the judge (149 judged answers plus that slot).

Usage covers all 150 slots, including every discarded attempt: 330,564 input
tokens (no cached reads reported), 8,108,043 output tokens (7,925,621 reasoning
tokens), and 8,438,607 total tokens; the four attempts on the unanswered slot
account for 522,960 of them. At OpenRouter's listed price ($0.10 input, $0.01
cached input, $0.50 output per 1M tokens) the answer-model cost is about $4.09;
judge cost is excluded.

## Contents

- `<model>/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `<model>/judge_outputs/`: per-answer DeepSeek V4 Pro scores and rationales
  plus the judge metadata manifest

Per-answer token usage, including retried attempts, is published in
`docs/data/direct_qa/models/<model_key>.json`. Raw provider responses, probe
runs, and retry working directories remain outside the repository.
