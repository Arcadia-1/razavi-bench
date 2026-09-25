# GPT-6 Sol Direct QA

GPT-6 Sol (Vela model 215456, `gpt-6-sol`, maximum reasoning effort) answered
all 50 questions in three independent one-turn rollouts. Vela task 624750
completed 150/150 records with no failed or empty answer. All 46 image-bearing
questions in each rollout included their figure image; no answer used tools or
web search. The source task revision was `0058a6ef062374d61eed99e52d38f020c2efa149`.

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| MiniMax M3 | 85.83% | 94.44% | 72.92% |
| DeepSeek V4 Pro | 90.33% | 96.94% | 80.42% |
| Active score (DeepSeek V4 Pro) | **90.33%** | **96.94%** | **80.42%** |

Each judge independently graded each exported answer against the current rubric
and golden solution with thinking disabled. The published active score uses
DeepSeek V4 Pro only; independent MiniMax M3 scores remain available for audit.
Vela's embedded M3 score (84.00%) is retained in
`judge_outputs/minimax-m3-vela-20260926/` for audit only.

Answer-model usage is complete for all 150 records: 292,863 input tokens
(including 1,250 cached reads) and 897,313 output tokens. At the
[standard GPT-6 Sol API rates](https://developers.openai.com/api/docs/models/gpt-6-sol)
of $2 input, $0.20 cached input, and $10 output per million tokens, the
estimated answer-model cost is $9.56; judge cost and provider-specific billing
are excluded.
