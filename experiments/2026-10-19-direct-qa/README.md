# 2026-10-19 Direct QA

Direct multimodal QA run generated with `tools/direct_qa_openrouter.py
--provider nvidia` and published with `tools/build_model_json.py`.

## Nemotron 3.5 Super VL

- Answer model: NVIDIA-Nemotron-3.5-Super-VL-120B-A12B (released 2026-10-15)
  through NVIDIA's API catalog, model `nvidia/nemotron-3.5-super-vl-120b-a12b`
  (the API reports the served model as `nemotron-3.5-super-120b-a12b`)
- Full reasoning: `chat_template_kwargs: {"enable_thinking": true}`, the highest
  of the model's off / on (medium) / on levels
- Sampling per the model card's reasoning examples: temperature 1.0, top_p 0.95;
  `max_tokens` 131,072
- Rollouts: 3 × 50 tasks, generation concurrency 10, then 4 for the re-runs
- Judge: DeepSeek V4 Pro through OpenRouter, reasoning disabled

| Judge | Overall | Part 1 | Part 2 |
|---|---:|---:|---:|
| DeepSeek V4 Pro (OpenRouter) | **44.50%** | **49.44%** | **37.08%** |

Each rollout scored 44.50%. Score distribution over 150 answers: 45 fours, 5
threes, 9 twos, 54 ones, 37 zeros.

The visible answers are very short: the median answer is about 30 characters
and 65% are 40 characters or fewer, often just "Yes" or "No", with the analysis
left in the reasoning trace (median about 7,100 reasoning tokens per answer),
which the judge does not see. A bare correct conclusion can still earn full
credit (a plain "No" to `part1-006` scored 4). The low score comes from wrong
conclusions (33 of the 97 answers of 40 characters or fewer scored 0) and from
open questions such as "Analyze the circuit" answered with only a topology name
(for example "Source Follower", scored 1). Answers of 40 characters or fewer
average 32.7%; longer answers average 66.0%. A direct re-check of `part1-006`
showed a 36,689-character reasoning trace that planned a full explanation,
followed by a final answer of "No". The chat template has no option to force a
fuller final answer, and the benchmark prompt was not changed for this model.

NVIDIA's trial API often returned HTTP 500 errors or dropped the connection on
long requests. Such requests were retried; twelve slots that still failed after
three attempts in the main pass were re-run with `--resume` and all finished.

Usage covers all 150 answers: 241,824 input tokens, 1,135,470 output tokens
(1,128,203 reasoning tokens), and 1,377,294 total tokens. NVIDIA's trial API is
free; at OpenRouter's Nemotron 3.5 Super VL price ($0.10 input, $0.08 cached
input, $0.40 output per 1M tokens) the cost would be about $0.48. Judge cost is
excluded.

## Contents

- `nemotron-3-5-super-vl/model_outputs/`: three cleaned 50-answer rollout JSONL files
- `nemotron-3-5-super-vl/judge_outputs/`: per-answer DeepSeek V4 Pro scores and
  rationales plus the judge metadata manifest

Per-answer token usage is published in
`docs/data/direct_qa/models/nemotron_35_super_vl.json`. Raw provider responses
and the probe run remain outside the repository.
