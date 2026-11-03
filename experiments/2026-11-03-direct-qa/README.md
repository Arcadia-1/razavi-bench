# 2026-11-03 Direct QA

## Claude Fable 5: tool-free reruns of eleven flagged answers

Eleven answers in the published Claude Fable 5 run (`2026-07-15-direct-qa`)
carried `internet_or_tool_evidence: true`. Their text shows no search results,
but Direct QA is tool-free, so these slots were run again and the new answers
replace the flagged ones under the same key, `claude_fable_5`.

- Answer model: `anthropic/claude-fable-5` through OpenRouter's chat completions
  route, reasoning effort max, `max_tokens` 128,000, no tools
- Judge: GPT-6 Luna at maximum reasoning effort

| Rollout | Task | Original score | Rerun score |
|---:|---|---:|---:|
| 1 | part1-022-explain-why-miller-effect-less-pronounced-cascode | 4 | 3 |
| 2 | part1-003-small-signal-model-pmos-device-identical-nmos | 4 | 4 |
| 2 | part1-004-sketch-ix-versus-vx | 4 | 4 |
| 2 | part1-005-sketch-ix-versus-vx | 4 | 4 |
| 2 | part1-017-pmos-input-invalid-pulldown | 4 | 4 |
| 2 | part2-013-dynamic-latch-divide-by-two | 4 | 4 |
| 2 | part2-020-estimate-oscillation-frequency | 4 | 4 |
| 3 | part1-008-source-follower | 4 | 4 |
| 3 | part1-014-cmos-inverter | 4 | 4 |
| 3 | part1-022-explain-why-miller-effect-less-pronounced-cascode | 4 | 4 |
| 3 | part1-023-common-gate-pmos-load | 4 | 4 |

Claude Fable 5 now scores 90.33% overall (Part 1 95.00%, Part 2 83.33%), down
from 90.50%; it still sets the score frontier on its release date. All eleven
requests finished on the first attempt and cost $4.35 at OpenRouter's price
($10 input, $50 output per 1M tokens).

## Contents

- `claude-fable-5-rerun/model_outputs/`: the eleven rerun answers, one JSONL file
  per rollout
- `claude-fable-5-rerun/judge_outputs/gpt-6-luna-max.scores.jsonl`: their GPT-6
  Luna scores and rationales
