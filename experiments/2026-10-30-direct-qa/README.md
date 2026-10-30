# 2026-10-30 Direct QA

Direct multimodal QA run generated with `tools/direct_qa_openrouter.py` and
published with `tools/build_model_json.py`.

## GPT-6 Luna

- Answer model: GPT-6 Luna through OpenRouter (`openai/gpt-6-luna`, first
  listed 2026-09-22)
- Reasoning effort: max, the highest OpenRouter lists for the model (`max,
  xhigh, high, medium, low, none`); `max_tokens` 128,000, the model's output
  limit
- Rollouts: 3 × 50 tasks, generation concurrency 15
- Judge: GPT-6 Luna at maximum reasoning effort through OpenRouter

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| GPT-6 Luna (max) | **83.00%** | **90.56%** | **71.67%** |

Rollout results are 84.00%, 82.00%, and 83.00%. Score distribution over 150
answers: 103 fours, 13 threes, 19 twos, 9 ones, 6 zeros. It ranks 24th of 65;
the earlier GPT-5.6 Luna entry (max) scores 79.83% under the same judge.

Four answers were re-sampled: two requests timed out and two ended in a
provider error. Every attempt is counted in tokens and cost.

Usage covers all 154 requests: 295,836 input tokens (121,442 cached reads),
1,639,152 output tokens (1,594,189 reasoning tokens), and 1,934,988 total
tokens. At OpenRouter's GPT-6 Luna price ($0.10 input, $0.01 cached input,
$0.50 output per 1M tokens) the answer-model cost is about $0.84; judge cost
is excluded.

## Contents

- `gpt-6-luna/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `gpt-6-luna/judge_outputs/gpt-6-luna-max.scores.jsonl`: per-answer GPT-6
  Luna scores and rationales

Per-answer token usage is published in
`docs/data/direct_qa/models/gpt_6_luna.json`. Raw provider responses remain
outside the repository.
