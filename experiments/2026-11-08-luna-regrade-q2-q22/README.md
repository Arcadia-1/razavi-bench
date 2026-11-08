# 2026-11-08 GPT-6 Luna re-grade of Part 1 Q2 and Q22

The reference answers of two concept questions without a figure were revised,
and every published answer to them (77 entries x 3 rollouts x 2 questions =
462 answers) was re-graded by GPT-6 Luna at maximum reasoning effort with
`tools/evaluate_answers.py --model openai/gpt-6-luna --reasoning-effort max
--max-tokens 128000 --json-mode`. No answer model was re-run, and the scores of
the other 48 questions are unchanged.

- `part1-002` (does gm rise or fall with overdrive?): Razavi's answer is that
  gm rises with Vov for a fixed W/L. The previous reference answer also required
  the fixed-ID case, in which gm falls, and the judge docked answers that omitted
  it. That case is now welcome but optional.
- `part1-022` (why is the Miller effect weaker in a cascode?): the reference now
  gives the gain from the input gate to the cascode node as about
  -gm1/(gm2 + gmb2), roughly -1, and the Miller factor of Cgd1 as about 2,
  instead of "a gain of about -2", and notes the low-impedance node assumes a
  load impedance that is not too large.

| Question | Before | After | Answers changed |
|---|---:|---:|---|
| `part1-002` | 88.9% | 98.9% | 92 rose 3 -> 4, 1 rose 2 -> 4, 1 fell 4 -> 3 |
| `part1-022` | 92.1% | 91.6% | 24 rose 3 -> 4, 29 fell 4 -> 3, 2 fell 3 -> 2, 1 rose 0 -> 2 |

Overall scores move by -0.33 to +0.83 points (23 entries unchanged); no entry
moves more than three places. Gemini 4 Argon stays first (94.17% -> 94.00%).

## Contents

- `gpt-6-luna-max.scores.jsonl`: the 462 new scores and rationales
- `merge.py`: replaces those scores in `docs/data/direct_qa/models/` (checking
  each answer's SHA-256) and recomputes the judge summaries; then run
  `tools/apply_active_judge.py` and `tools/aggregate_questions.js`
