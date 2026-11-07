# 2026-11-07 Direct QA

Two self-hosted Qwen checkpoints, each answering all 50 tasks in three rollouts,
generated with each folder's `run.py` and published with
`tools/build_model_json.py --tokens`.

- Server: vLLM 0.33.0 with the `qwen3` reasoning parser and a 262,144-token
  context, on a university GPU server, reached through an SSH tunnel
- Requests: streamed chat completions; thinking on; Qwen's recommended
  thinking-mode sampling (temperature 1.0, top_p 0.95); `max_tokens` 245,760
- Judge: GPT-6 Luna at maximum reasoning effort, with
  `tools/evaluate_answers.py --model openai/gpt-6-luna --reasoning-effort max
  --max-tokens 128000 --json-mode`
- All 150 answers of each model succeeded on the first attempt

| Model | Checkpoint | Overall | Part 1 | Part 2 | Rollouts |
|---|---|---:|---:|---:|---|
| Qwen 3.5 9B | `Qwen/Qwen3.5-9B` BF16, revision `c2022362` | **55.17%** | 60.00% | 47.92% | 56.5, 55.0, 54.0 |
| Qwen 3.8 27B | `Qwen/Qwen3.8-27B` BF16, revision `8c0b3d30` | **77.17%** | 86.67% | 62.92% | 78.5, 77.0, 76.0 |

Both are published at their default setting, so the site shows no effort tag.
Qwen 3.5 9B has no reasoning-effort levels, only thinking on or off. The
Qwen 3.8 27B requests sent `reasoning_effort` `xhigh`, which on this server only
adds an instruction to the prompt and is also what the chat template uses when
no effort is given; its median output length (10,352 tokens) matches the earlier
run's (10,457).

The Qwen 3.8 27B run replaces the 2026-08-15 run of the FP8 checkpoint at
temperature 0 (77.67%, `../2026-08-15-direct-qa/`), whose files stay in that
experiment.

One Qwen 3.5 9B answer (`part2-005`, rollout 3) came back with the end of its
reasoning in the final text, up to a `</think>` tag. The published answer is the
text after that tag, and it was regraded (1 point, as before). The server did not
report cached input tokens; they are recorded as 0. The models are self-hosted,
so the site shows no API cost.

## Contents

Per model folder (`selfhosted-qwen3-5-9b/`, `selfhosted-qwen3-8-27b/`):

- `run.py`: the runner
- `model_outputs/`: three 50-answer rollout JSONL files
- `judge_outputs/gpt-6-luna-max.scores.jsonl`: per-answer GPT-6 Luna scores and
  rationales
- `tokens.json`: per-answer token usage keyed `"<rollout>:<task_slug>"`
- `<folder>.metadata.json`: run settings, runtime and totals

Raw responses with reasoning text, timings and logs remain outside the repository.
