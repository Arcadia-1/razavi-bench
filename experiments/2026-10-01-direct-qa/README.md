# GPT-6.1 Sol Direct QA

GPT-6.1 Sol (`openai/gpt-6.1-sol` on OpenRouter, maximum reasoning effort)
answered all 50 questions in three independent one-turn rollouts. The run
completed 150/150 records with no failed or empty answer, and all 46
image-bearing questions per rollout received their figure image. No answer used
tools or web search.

## Setup

- Mode: direct multimodal QA
- Route: OpenRouter OpenAI-compatible chat completions
- Rollouts: 3 × 50 questions
- Temperature: 0
- Maximum output tokens: 65,536
- Reasoning effort: max
- Generation concurrency: 10
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

## Results

Each answer was graded once against the current golden solution and rubric by
DeepSeek V4 Pro with thinking disabled. The published active score uses
DeepSeek V4 Pro.

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **93.50%** | **100.00%** | **83.75%** |

Rollout results are 93.50%, 93.00%, and 94.00%. Score distribution over 150
answers: 129 fours, 8 threes, 8 twos, 5 ones, no zeros.

For comparison, GPT-6 Sol (max) scored 90.33% and GPT-6 Sol Thinking High (high)
scored 81.33% under the same rubric and active judge.

## Usage

Answer-model usage is complete for all 150 records: 292,863 input tokens
(including 188,452 cached reads), 649,522 output tokens (including 580,925
reasoning tokens), and 942,385 total tokens. The OpenRouter-reported
answer-model cost is $6.77; judge cost is excluded.

During generation, 16 requests hit a transient OpenRouter HTTP 402
in-flight-budget response while concurrency was 10. All were retried
successfully and no answer slot failed.

## Contents

- `model_outputs/`: three cleaned 50-answer rollout JSONL files and the public
  per-answer token manifest
- `judge_outputs/`: per-answer DeepSeek V4 Pro scores and rationales plus the
  judge metadata manifest
- `tools/`: token-manifest and model-JSON build scripts used for this
  experiment

The public answer files exclude system prompts, hidden reasoning, provider
request metadata, and API keys. Raw provider responses remain outside the
repository.

## Judge route

Judging used OpenRouter's `deepseek/deepseek-v4-pro` with reasoning disabled
through the `--openrouter-reasoning` flag in `tools/evaluate_answers.py`. Older
published runs judged through the native DeepSeek API, so the provider route
differs even though the scores share the same rubric, golden solutions, and
active-judge policy.
