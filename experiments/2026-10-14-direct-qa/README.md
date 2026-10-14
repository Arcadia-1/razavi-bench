# 2026-10-14 Direct QA

Direct multimodal QA run generated with the public standalone runner,
`tools/direct_qa_openrouter.py`, and published with `tools/build_model_json.py`.

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

## Contents

- `gemini-4-argon/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `gemini-4-argon/judge_outputs/`: per-answer DeepSeek V4 Pro scores and
  rationales plus the judge metadata manifest

Per-answer token usage is published in
`docs/data/direct_qa/models/gemini_4_argon.json`. Raw provider responses and the
probe run remain outside the repository.
