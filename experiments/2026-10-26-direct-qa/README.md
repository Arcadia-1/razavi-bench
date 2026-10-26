# 2026-10-26 Direct QA

Direct multimodal QA run generated with `tools/direct_qa_openrouter.py
--provider moonshot` and published with `tools/build_model_json.py`.

## Kimi 3.1 Pro

- Answer model: Kimi 3.1 Pro through the Kimi API (`https://api.moonshot.ai/v1`),
  model id `kimi-31-pro-nuvora`; the same model is listed on OpenRouter as
  `moonshotai/kimi-k3.1-pro` (first listed 2026-10-23)
- Reasoning effort: max, the highest the model offers (`max, high, low`; thinking
  cannot be turned off, and an unknown effort silently falls back to the
  default, so the runner only accepts the listed levels); `max_tokens` 131,072
- Rollouts: 3 × 50 tasks, generation concurrency 10
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **92.00%** | **96.11%** | **85.83%** |

Rollout results are 92.00%, 92.50%, and 91.50%. Score distribution over 150
answers: 128 fours, 8 threes, 4 twos, 8 ones, 2 zeros. The previous Kimi K3
entry (max) scored 76.83% under the same judge.

Every answer finished normally. Sixteen requests lost their connection
(`Remote end closed connection`, `IncompleteRead`) and were retried; those
attempts returned no tokens.

Usage covers all 150 answers: 330,027 input tokens (221,305 cached reads),
2,138,921 output tokens (2,061,607 reasoning tokens), and 2,468,948 total
tokens. At the Kimi K3 API price ($3.00 input, $0.30 cached input, $15.00 output
per 1M tokens) the answer-model cost is about $32.48; judge cost is excluded.

## Contents

- `kimi-31-pro-nuvora/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `kimi-31-pro-nuvora/judge_outputs/`: per-answer DeepSeek V4 Pro scores and
  rationales plus the judge metadata manifest

Per-answer token usage is published in
`docs/data/direct_qa/models/kimi_31_pro.json`. Raw provider responses and the
probe run remain outside the repository.
