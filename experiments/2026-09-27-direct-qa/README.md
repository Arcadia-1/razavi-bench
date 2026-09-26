# DeepSeek V4.1 Flash Direct QA

DeepSeek V4.1 Flash (Vela model `211818`, API model `deepseek-flash`, maximum
thinking effort) answered all 50 questions in three independent one-turn
rollouts. Vela task `632713` completed 150/150 records with no failed or empty
answer. Each rollout included all 46 image-bearing questions with their figure
image; no answer used tools or web search.

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| MiniMax M3 | 77.67% | 85.56% | 65.83% |
| DeepSeek V4 Pro | 80.50% | 86.11% | 72.08% |
| Active score (DeepSeek V4 Pro) | **80.50%** | **86.11%** | **72.08%** |

Each judge independently graded each exported answer against the current
golden solution and rubric with thinking disabled. The published active score
uses DeepSeek V4 Pro; MiniMax M3 remains available for audit. The score files
record the golden hash, rubric hash, answer hash, source task, and judge
provenance for every answer.

Answer-model usage is complete for all 150 records: 125,349 input tokens
(including 65,270 cached reads) and 2,539,826 output tokens. At the official
DeepSeek V4.1 Flash off-peak rates of $0.15 uncached input, $0.003 cached input,
and $0.60 output per million tokens, the estimated answer-model cost is $1.53;
judge cost is excluded.
