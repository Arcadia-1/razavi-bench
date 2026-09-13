# Inkling Fair Comparison

This experiment reruns only `thinkingmachines/inkling` against the same 50
Direct QA tasks used for Inkling Small. It uses three rollouts, temperature 0,
provider-default reasoning, and `max_tokens=65536`.

The answer model produced 150 non-empty responses with `finish_reason=stop`.
Each answer was graded independently by MiniMax M3 and DeepSeek V4 Pro using
the same judge script, system prompt, rubric, and parameters as the Inkling
Small evaluation.

This experiment is the current public Inkling result used by the active Direct
QA aggregate.
