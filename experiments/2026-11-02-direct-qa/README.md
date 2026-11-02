# 2026-11-02 Direct QA

Direct multimodal QA runs generated with `tools/direct_qa_openrouter.py` and
published with `tools/build_model_json.py`. They fill the gap between April and
December 2025 on the release-date timeline with six models still served by
OpenRouter, each at the highest reasoning effort it accepts.

- Rollouts: 3 × 50 tasks per model
- Judge: GPT-6 Luna at maximum reasoning effort through OpenRouter
- Release dates: the date OpenRouter first listed each model

| Model | OpenRouter id | Effort | `max_tokens` | Overall | Part 1 | Part 2 | Rank (of 71) |
|---|---|---|---:|---:|---:|---:|---:|
| o3 | `openai/o3` | high | 100,000 | **55.83%** | 59.72% | 50.00% | 58 |
| Claude Sonnet 4.5 | `anthropic/claude-sonnet-4.5` | max | 64,000 | **57.33%** | 61.67% | 50.83% | 57 |
| GPT-5.1 | `openai/gpt-5.1` | high | 128,000 | **62.50%** | 67.50% | 55.00% | 53 |
| Claude Opus 4.5 | `anthropic/claude-opus-4.5` | max | 64,000 | **64.67%** | 67.78% | 60.00% | 50 |
| GPT-5.2 | `openai/gpt-5.2` | xhigh | 128,000 | **78.33%** | 85.28% | 67.92% | 34 |
| Gemini 3 Flash | `google/gemini-3-flash-preview` | high | 65,536 | **78.33%** | 87.22% | 65.00% | 33 |

`max_tokens` is each model's output limit on OpenRouter. OpenRouter lists no
efforts for o3 or the two Claude models: o3 runs at high, the highest OpenAI
offers, and the Claude models at max, which OpenRouter sends as an
extended-thinking budget of 60,800 tokens (95% of `max_tokens`). The other
three run at the highest effort OpenRouter lists for them.

| Model | Rollouts | Score distribution (4/3/2/1/0) |
|---|---|---|
| o3 | 55.00%, 56.00%, 56.50% | 36 / 29 / 37 / 30 / 18 |
| Claude Sonnet 4.5 | 59.00%, 57.50%, 55.50% | 46 / 29 / 23 / 27 / 25 |
| GPT-5.1 | 61.50%, 65.00%, 61.00% | 65 / 19 / 16 / 26 / 24 |
| Claude Opus 4.5 | 64.00%, 66.00%, 64.00% | 67 / 22 / 18 / 18 / 25 |
| GPT-5.2 | 79.50%, 79.50%, 76.00% | 95 / 16 / 13 / 16 / 10 |
| Gemini 3 Flash | 79.50%, 79.00%, 76.50% | 95 / 18 / 12 / 12 / 13 |

Re-sampled requests: one o3, one Claude Opus 4.5 and one GPT-5.2 request lost
the connection mid-response; one GPT-5.1 and one GPT-5.2 request ended in a
provider error; one GPT-5.2 request returned nothing for over an hour and was
cancelled. Requests that OpenRouter refused for insufficient account credit
(HTTP 402) were sent again later and were not billed. Every billed attempt is
counted in tokens and cost.

| Model | Billed requests | Input (cached) | Output (reasoning) | Cost |
|---|---:|---:|---:|---:|
| o3 | 150 | 121,236 (13,568) | 657,938 (567,040) | $5.49 |
| Claude Sonnet 4.5 | 150 | 203,313 (0) | 750,472 (658,947) | $11.87 |
| GPT-5.1 | 150 | 113,706 (3,456) | 1,175,632 (1,107,933) | $11.89 |
| Claude Opus 4.5 | 150 | 203,313 (0) | 797,956 (713,375) | $20.97 |
| GPT-5.2 | 151 | 270,446 (80,384) | 2,255,776 (2,184,616) | $31.72 |
| Gemini 3 Flash | 150 | 158,752 (0) | 714,932 (606,518) | $2.22 |

Costs are OpenRouter's billed amounts at each model's published API price;
judge cost is excluded.

## GPT-4o snapshots

The GPT-4o entry published from `2026-08-01-direct-qa` was run through
OpenRouter's `openai/gpt-4o` alias but dated to the original May 13, 2024
release. That alias serves `gpt-4o-2024-08-06`: on 2026-11-02 it returned the
same system fingerprint (`fp_625eb29508`) and charged the same price as
`openai/gpt-4o-2024-08-06`, while `openai/gpt-4o-2024-05-13` returned a
different one. The existing entry is therefore relabelled GPT-4o (2024-08-06)
and dated August 6, 2024, and the May snapshot was run here as its own entry.

- Answer model: `openai/gpt-4o-2024-05-13` (served by Azure), no reasoning
  setting
- Temperature 0, as in the August run; `max_tokens` 4,096, the snapshot's
  output limit (the August run used 8,192)
- Rollouts: 3 × 50 tasks, generation concurrency 8

| Model | Overall | Part 1 | Part 2 | Rollouts | Score distribution (4/3/2/1/0) |
|---|---:|---:|---:|---|---|
| GPT-4o (2024-05-13) | **35.67%** | 28.61% | 46.25% | 34.00%, 35.00%, 38.00% | 8 / 25 / 30 / 47 / 40 |
| GPT-4o (2024-08-06), August run | 43.00% | 37.78% | 50.83% | 43.00%, 44.50%, 41.50% | 7 / 42 / 32 / 40 / 29 |

Eleven requests that timed out at the gateway (HTTP 504) and one answer that
ran into the 4,096-token limit were re-sampled. The 151 billed requests used
137,600 input and 81,518 output tokens; at OpenRouter's price for this snapshot ($5 input, $15
output per 1M tokens, no cached-input discount) the answer-model cost is about
$1.91.

## GPT-5.3 at xhigh

The published GPT-5.3 entry (`2026-08-01-direct-qa`) is GPT-5.3-Codex run at
the provider's default effort (medium) with temperature 0 and `max_tokens`
8,192, a cap that reasoning and answer share. It was repeated here at the
model's highest effort and full output limit and published as a second
configuration, `gpt_53_xhigh`; the original entry is kept.

- Answer model: `openai/gpt-5.3-codex`, reasoning effort xhigh (OpenRouter
  lists `xhigh, high, medium, low, none`), `max_tokens` 128,000
- Rollouts: 3 × 50 tasks, generation concurrency 12

| Configuration | Overall | Part 1 | Part 2 | Rollouts | Score distribution (4/3/2/1/0) |
|---|---:|---:|---:|---|---|
| GPT-5.3 [xhigh] | **84.00%** | 90.83% | 73.75% | 85.00%, 83.50%, 83.50% | 107 / 13 / 13 / 11 / 6 |
| GPT-5.3 [default], August run | 74.67% | 82.78% | 62.50% | 72.00%, 79.00%, 73.00% | 91 / 11 / 14 / 23 / 11 |

All 150 requests finished on the first attempt: 268,884 input tokens (75,264
cached) and 1,196,908 output tokens (1,144,177 reasoning), about $17.11 at
OpenRouter's price ($1.75 input, $0.175 cached input, $14 output per 1M
tokens). GPT-5.3 [xhigh] ranks 20th of 73 and sets the score frontier from
February 5, 2026 until Claude Opus 4.8.

## Contents

- `<model>/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `<model>/judge_outputs/gpt-6-luna-max.scores.jsonl`: per-answer GPT-6 Luna
  scores and rationales

Per-answer token usage is published in `docs/data/direct_qa/models/`. Raw
provider responses remain outside the repository.
