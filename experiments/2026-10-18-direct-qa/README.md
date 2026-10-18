# 2026-10-18 Direct QA

Direct multimodal QA run generated with `tools/direct_qa_openrouter.py
--provider deepseek` and published with `tools/build_model_json.py`.

## DeepSeek V4.1 Flash 1017

- Answer model: DeepSeek-V4.1-Flash-1017 (released 2026-10-17) through the
  official DeepSeek API, model name `deepseek-flash`
- Thinking enabled at reasoning effort max, the highest DeepSeek offers
  (`low, high, max`); `max_tokens` 131,072
- Rollouts: 3 × 50 tasks, generation concurrency 20
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **85.50%** | **90.56%** | **77.92%** |

Rollout results are 83.50%, 87.00%, and 86.00%. Score distribution over 150
answers: 113 fours, 11 threes, 7 twos, 14 ones, 5 zeros. The earlier DeepSeek
V4.1 Flash 0910 entry (September snapshot, same judge) scored 80.50% (Part 1 86.11%,
Part 2 72.08%).

One answer (`part1-020`, rollout 1) failed on its first request and was
re-sampled automatically.

Usage covers all 150 answers: 125,349 input tokens (66,806 cached reads),
3,961,397 output tokens (3,867,166 reasoning tokens), and 4,086,746 total
tokens. At DeepSeek's off-peak price, as used for the earlier entry ($0.15
input, $0.003 cached input, $0.60 output per 1M tokens), the answer-model cost
is about $2.39; judge cost is excluded.

## Contents

- `deepseek-flash-1017/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `deepseek-flash-1017/judge_outputs/`: per-answer DeepSeek V4 Pro scores and
  rationales plus the judge metadata manifest

Per-answer token usage is published in
`docs/data/direct_qa/models/deepseek_v41_flash_1017.json`. Raw provider
responses and the probe run remain outside the repository.
