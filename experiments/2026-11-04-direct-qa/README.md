# 2026-11-04 Direct QA

Direct multimodal QA run generated with `tools/direct_qa_openrouter.py` and
published with `tools/build_model_json.py`.

## Hy4

- Answer model: Tencent Hy4 through OpenRouter (`tencent/hy4`, first listed
  2026-11-04)
- Reasoning effort: high, the highest OpenRouter lists for the model (`high,
  low, none`); `max_tokens` 65,536, the model's output limit
- Rollouts: 3 × 50 tasks, generation concurrency 15
- Judge: GPT-6 Luna at maximum reasoning effort through OpenRouter

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| GPT-6 Luna (max) | **89.00%** | **94.17%** | **81.25%** |

Rollout results are 88.00%, 90.50%, and 88.50%. Score distribution over 150
answers: 119 fours, 9 threes, 13 twos, 5 ones, 4 zeros. It ranks 10th of 76,
between Claude Opus 5 (high, 90.00%) and Kimi 3.1 Pro (max, 88.67%), and is
the first Tencent model on the leaderboard.

Three answers were re-sampled: two were stopped by the provider's content
filter and one request failed. Every attempt is counted in tokens and cost.

Usage covers every request: 250,791 input tokens (159,680 cached reads),
3,613,787 output tokens (3,506,352 reasoning tokens), and 3,864,578 total
tokens. At OpenRouter's Hy4 price ($0.417 input, $0.021 cached input, $1.2505
output per 1M tokens) the answer-model cost is about $4.56; judge cost is
excluded.

## Contents

- `tencent-hy4/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `tencent-hy4/judge_outputs/gpt-6-luna-max.scores.jsonl`: per-answer GPT-6
  Luna scores and rationales

Per-answer token usage is published in `docs/data/direct_qa/models/hy4.json`.
Raw provider responses remain outside the repository.
