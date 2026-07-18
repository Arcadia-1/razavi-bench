# Direct QA experiment - 2026-07-18

This directory contains the Kimi K3 Direct QA evaluation run completed on
2026-07-18. The model was evaluated with three rollouts over all 50
Razavi-Bench questions, for 150 final answers in total.

## Setup

- Mode: direct multimodal QA
- Answer model: Kimi K3 (`kimi-for-coding`, evaluation model ID `209566`)
- Rollouts: 3
- Questions per rollout: 50
- Part 1: first 30 questions
- Part 2: last 20 questions
- Figure-bearing questions: 46 per rollout, 138 total
- Temperature: 1, as required by the model endpoint
- Maximum output tokens: 65,536

The initial generation encountered provider quota errors and several stalled
or gateway-timed-out requests. Only records with a non-empty visible answer
were retained. Missing rollout slots were retried with the same question,
figure, model, and decoding configuration until all three rollouts contained
50 answers.

## Contents

- `model_outputs/kimi-k3-209566-rollout-1.jsonl`
- `model_outputs/kimi-k3-209566-rollout-2.jsonl`
- `model_outputs/kimi-k3-209566-rollout-3.jsonl`

Each JSONL line contains the effective benchmark question, final visible
answer, figure paths, rollout number, model name, and model-call attempt count.
The files exclude hidden reasoning, API keys, platform session IDs, internal
task IDs, provider response metadata, and token or cost records.

Intermediate empty responses and retry artifacts are not included. When a
rollout slot required a retry, the corresponding JSONL line contains its final
successful answer while preserving the original rollout assignment and task
order.

## Evaluation status

This snapshot contains model outputs only. Judge outputs, score tables, and
comparison figures have not yet been added. Future scoring should use the
repository-level evaluator at
[`../../tools/evaluate_answers.py`](../../tools/evaluate_answers.py) and store
the evaluator metadata next to the score files.
