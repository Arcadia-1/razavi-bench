# Claude Opus 5.5 and Claude Fable 5.1 Direct QA

This experiment publishes cleaned answers from Vela Direct QA tasks 609968
(Claude Opus 5.5, model 215423) and 609972 (Claude Fable 5.1, model 213099).
Each model answered all 50 questions in three independent one-turn rollouts.
Both tasks completed 150/150 records with no failed or empty answer. All 46
image-bearing questions in each rollout included their image in the request.
The answer models used adaptive thinking at maximum effort; no answer used tools
or web search.

The active score is the mean of independent per-answer grading by MiniMax M3
and DeepSeek V4 Pro using the current rubric and golden solutions. Both judges
were run with thinking disabled and scored each answer separately.

| Answer model | Judge | Overall | Part 1 | Part 2 |
|---|---|---:|---:|---:|
| Claude Opus 5.5 | MiniMax M3 | 92.00% | 97.78% | 83.33% |
| Claude Opus 5.5 | DeepSeek V4 Pro | 95.33% | 100.00% | 88.33% |
| Claude Opus 5.5 | Active mean | **93.67%** | **98.89%** | **85.83%** |
| Claude Fable 5.1 | MiniMax M3 | 91.17% | 95.28% | 85.00% |
| Claude Fable 5.1 | DeepSeek V4 Pro | 93.00% | 96.39% | 87.92% |
| Claude Fable 5.1 | Active mean | **92.08%** | **95.83%** | **86.46%** |

The Vela-embedded MiniMax scores, 91.50% and 91.00%, are retained in
`judge_outputs/minimax-m3-vela-20260925/` for audit only. They are not used in
the active double-judge aggregate. Independent judge score files include answer,
rubric, golden-solution, script, and prompt hashes.

Answer-model usage is complete for both sets of 150 answers. Opus 5.5 used
317,817 input tokens (0 cached reads) and 3,648,673 output tokens; Fable 5.1
used 317,817 input tokens (0 cached reads) and 1,868,701 output tokens. Vela
task totals include the embedded judge calls and are not answer-model totals.
