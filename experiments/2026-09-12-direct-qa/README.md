# GPT-6 Astra Direct QA

This experiment publishes the cleaned GPT-6 Astra answers from EvalForge task
22646 / Vela AgentTask 474450. The evaluated model was Vela model 213549
(`gpt-6-astra`) with maximum reasoning effort. The run covered all 50 tasks in
three rollouts.

All 150 records completed without a failed or empty answer. Each rollout
included all 46 image-bearing tasks with the image present in the model request.
No answer-model request used tools or web search.

The active public score is the mean of independent per-answer grading by
MiniMax M3 and DeepSeek V4 Pro under the current repository rubric and golden
solutions:

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| MiniMax M3 | 92.50% | 98.89% | 82.92% |
| DeepSeek V4 Pro | 95.50% | 100.00% | 88.75% |
| Active mean | 94.00% | 99.44% | 85.83% |

The Vela run's embedded MiniMax M3 score was 92.00%. It is retained under
`judge_outputs/minimax-m3-vela-20260912/` for provenance and is not used as the
active double-judge aggregate.

Answer-model usage is complete for 150/150 answers: 292,863 input tokens,
3,864 cached input tokens (a subset of input), and 734,138 output tokens. The
Vela task-level total also includes embedded judge calls and therefore is not
the public answer-model token total.
