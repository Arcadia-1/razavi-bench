# 2026-10-27 GPT-6 Luna re-grade

Every published Direct QA answer (64 model configurations, 9,600 answers) was
re-graded by GPT-6 Luna (`openai/gpt-6-luna` through OpenRouter) at maximum
reasoning effort, and its scores became the active leaderboard scores
(`gpt_6_luna_max`). No answer model was re-run.

## Judge setup

- `tools/evaluate_answers.py --model openai/gpt-6-luna --reasoning-effort max
  --max-tokens 128000 --json-mode`, with the current `evaluation_rubric.md`,
  golden solutions, and judge system prompt
- Each answer graded once; no parse errors
- Slots published as unanswered (two: Claude Haiku 5.5 `part2-016` rollout 2 and
  Muse Wonder Full 1.0 `part1-015` rollout 2) keep score 0 without a judge call
- Judge cost: about $11 for all 9,600 answers plus a local re-grade of one
  unpublished run

The previous active judge, DeepSeek V4 Pro with reasoning disabled, stays in
every model file under `deepseek_v4_pro` (and MiniMax M3 under `minimax_m3` for
legacy entries).

## Effect on the leaderboard

GPT-6 Luna is stricter: scores fall by 4.03 points on average
(range -10.17 to +0.50). Ten configurations keep their rank and 49
move by at most two places; the top model is unchanged. On a 20-model
September-October sample, the two judges gave the identical score to 75-91% of
answers for most models and were within one point on 96-100%.

The largest drop is Muse Spark 1.2 (rank 10 to 25). Its long answers often
reach a wrong central conclusion that DeepSeek V4 Pro without reasoning still
credited; for example, a `part1-015` answer that analyzes the two-NMOS stage as a
pMOS pull-up with an nMOS pull-down scored 4 under DeepSeek, while the golden
solution's device-type rule requires 0, which GPT-6 Luna assigned.

| Rank | Previous rank | Model | DeepSeek V4 Pro | GPT-6 Luna (max) | Change |
|---:|---:|---|---:|---:|---:|
| 1 | 1 | Gemini 4 Argon [high] | 95.83% | 94.17% | -1.66 |
| 2 | 3 | Claude Opus 5.5 [max] | 95.33% | 93.83% | -1.50 |
| 3 | 2 | GPT-6 Astra [max] | 95.50% | 93.50% | -2.00 |
| 4 | 5 | Claude Opus 5 [xhigh] | 94.00% | 91.00% | -3.00 |
| 5 | 6 | GPT-6.1 Sol [max] | 93.50% | 91.00% | -2.50 |
| 6 | 7 | Claude Fable 5 [max] | 93.17% | 90.50% | -2.67 |
| 7 | 8 | Claude Fable 5.1 [max] | 93.00% | 90.50% | -2.50 |
| 8 | 9 | Claude Opus 5 [max] | 92.50% | 90.50% | -2.00 |
| 9 | 4 | Claude Opus 5 [high] | 94.83% | 90.00% | -4.83 |
| 10 | 11 | Kimi 3.1 Pro [max] | 92.00% | 88.67% | -3.33 |
| 11 | 12 | Gemini 3.7 Flash [high] | 91.83% | 88.50% | -3.33 |
| 12 | 13 | GPT-6 Sol [max] | 90.33% | 87.17% | -3.16 |
| 13 | 14 | Gemini 3.8 Flash [high] | 90.33% | 87.17% | -3.16 |
| 14 | 16 | Muse Wonder Full 1.0 [max] | 88.67% | 86.67% | -2.00 |
| 15 | 17 | Claude Opus 4.8 [max] | 88.50% | 85.67% | -2.83 |
| 16 | 23 | GPT 5.6 Sol [max] | 86.17% | 85.67% | -0.50 |
| 17 | 18 | Claude Haiku 5.5 [max] | 87.67% | 85.33% | -2.34 |
| 18 | 22 | Muse Spark 1.3 [max] | 86.67% | 84.50% | -2.17 |
| 19 | 24 | Qwen 3.8 Max | 85.67% | 84.00% | -1.67 |
| 20 | 19 | Gemini 3.5 Flash | 87.33% | 83.83% | -3.50 |
| 21 | 15 | Claude Opus 5 [medium] | 88.67% | 83.33% | -5.34 |
| 22 | 21 | GLM 5.3 Flash [max] | 86.67% | 83.33% | -3.34 |
| 23 | 20 | Gemini 3.6 Flash | 86.83% | 83.17% | -3.66 |
| 24 | 25 | DeepSeek V4.1 Flash 1017 [max] | 85.50% | 82.50% | -3.00 |
| 25 | 10 | Muse Spark 1.2 [xhigh] | 92.00% | 81.83% | -10.17 |
| 26 | 29 | Doubao Seed 2.1 Pro [max] | 83.50% | 81.17% | -2.33 |
| 27 | 27 | GPT-5.6 Terra [max] | 85.00% | 80.83% | -4.17 |
| 28 | 33 | Gemini 3.1 Pro [high] | 81.83% | 80.50% | -1.33 |
| 29 | 30 | GPT-5.6 Luna [max] | 83.33% | 79.83% | -3.50 |
| 30 | 28 | Grok 4.6 [xhigh] | 84.50% | 79.17% | -5.33 |
| 31 | 26 | Grok 4.5 | 85.17% | 78.83% | -6.34 |
| 32 | 31 | Qwen 3.8 27B | 82.33% | 77.67% | -4.66 |
| 33 | 37 | GPT-5.5 [max] | 80.17% | 77.67% | -2.50 |
| 34 | 32 | Qwen 3.7 Plus | 82.00% | 77.00% | -5.00 |
| 35 | 34 | Grok 4.7 [xhigh] | 81.67% | 77.00% | -4.67 |
| 36 | 35 | GPT-6 Sol Thinking High [high] | 81.33% | 77.00% | -4.33 |
| 37 | 36 | DeepSeek V4.1 Flash 0910 [max] | 80.50% | 76.17% | -4.33 |
| 38 | 38 | Mistral Large 4 [high] | 79.83% | 75.50% | -4.33 |
| 39 | 40 | GPT-5.3 | 78.00% | 74.67% | -3.33 |
| 40 | 39 | Qwen 3.7 Flash | 79.33% | 73.83% | -5.50 |
| 41 | 41 | Kimi K3 [max] | 76.83% | 73.17% | -3.66 |
| 42 | 42 | Kimi K2.7 | 76.00% | 72.33% | -3.67 |
| 43 | 43 | GPT-5.4 [high] | 75.67% | 72.17% | -3.50 |
| 44 | 44 | Inkling Small | 75.67% | 69.17% | -6.50 |
| 45 | 46 | Claude Sonnet 4.6 | 71.33% | 66.00% | -5.33 |
| 46 | 45 | Mimo 2.6 Pro [thinking] | 73.17% | 65.83% | -7.34 |
| 47 | 49 | GPT-5 | 68.50% | 63.33% | -5.17 |
| 48 | 48 | GPT-5.4 Mini [medium] | 69.17% | 63.00% | -6.17 |
| 49 | 51 | Gemini 2.5 Pro | 64.17% | 62.33% | -1.84 |
| 50 | 47 | Step 3.7 Flash | 71.33% | 62.00% | -9.33 |
| 51 | 50 | Inkling | 64.83% | 58.00% | -6.83 |
| 52 | 57 | Llama 4 Maverick | 52.67% | 51.00% | -1.67 |
| 53 | 52 | Mistral Medium 3.5 [max] | 58.83% | 50.00% | -8.83 |
| 54 | 56 | Qwen3-VL-235B-A22B Instruct | 52.67% | 49.00% | -3.67 |
| 55 | 54 | Claude Sonnet 4 | 53.33% | 48.33% | -5.00 |
| 56 | 53 | MiniMax M3 | 54.83% | 47.67% | -7.16 |
| 57 | 58 | Gemma 4 31B IT | 52.50% | 46.00% | -6.50 |
| 58 | 60 | Nemotron 3.5 Super VL [high] | 44.50% | 45.00% | +0.50 |
| 59 | 55 | Mistral Large 2512 | 53.00% | 44.83% | -8.17 |
| 60 | 59 | GPT-4o | 44.67% | 43.00% | -1.67 |
| 61 | 61 | Claude Haiku 4.5 | 42.33% | 38.00% | -4.33 |
| 62 | 63 | GPT-4o Mini | 38.67% | 36.67% | -2.00 |
| 63 | 62 | Gemini 2.5 Flash-Lite | 42.33% | 36.17% | -6.16 |
| 64 | 64 | Qwen2.5-VL-72B Instruct | 37.83% | 31.83% | -6.00 |

## Contents

- `judge_outputs/<model_key>.gpt-6-luna-max.scores.jsonl`: per-answer GPT-6 Luna
  scores, rationales, answer and golden/rubric hashes, and the judge's token usage

Scores were added to the model files with `tools/add_judge_scores.py` and made
active with `tools/apply_active_judge.py --judge gpt_6_luna_max`.
