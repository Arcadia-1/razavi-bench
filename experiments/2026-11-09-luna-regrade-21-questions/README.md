# 2026-11-09 GPT-6 Luna re-grade of 21 more questions

The reference answers of 21 further questions were corrected and brought in line
with Razavi's comments and scores, and every published answer to them (77
entries x 3 rollouts x 21 questions = 4,851 answers) was re-graded by GPT-6
Luna at maximum reasoning effort with `tools/evaluate_answers.py --model
openai/gpt-6-luna --reasoning-effort max --max-tokens 128000 --json-mode`. No
answer model was re-run, and the scores of the other 29 questions are unchanged.

Each reference now quotes Razavi's comment and score on the article's answer and
gives an answer of the same kind the same score. Most changes correct a physics
statement or make a rule explicit:

- `part1-004`: drain-bulk conduction for negative `VX` is correct but optional.
- `part1-007`: identifying the PMOS is required; the right gain with an NMOS
  earns 1, Razavi's score.
- `part1-008`: the output resistance is `RS || 1/gm` (the resistance into the
  source alone is `1/gm`) and is optional, as in Razavi's 4.
- `part1-011`: two poles justified only by counting two energy-storing nodes
  earn 3, Razavi's score; full credit accounts for the capacitors (`CSB` shorted,
  the `CGS`-`CGD`-`CDB` loop).
- `part1-012`: the closed-loop gain is optional, since Razavi's only objection
  to the article's answer is the grounded source.
- `part1-013`: the follower gain with body effect and `ro`; "about unity" is
  correct in the ideal model.
- `part1-018`: `X` is set by `Vb1`, not `M2`; the approximation needs `gm1 ro2
  >> 1` as well.
- `part1-020`: node `X` is shielded from the output, not quiet; it swings by
  `-gm1 ro1 vin` with an ideal load.
- `part1-021`: Razavi's resistance is the one into the drain of `M2`, about
  `(1 + gm2/gm1) ro2`; "no `gm ro` boosting" is correct.
- `part1-023`: `Rin = (ro1 + ro2)/(1 + gm2 ro2)`, about `2/gm2`, not `1/gm2`
  (confirmed in ngspice).
- `part1-025`: "self-cascode" is an acceptable name; `M1` is in triode and the
  output resistance is about `2 ro2`, not a cascode's.
- `part1-026`: the differential-pair view is acceptable; the gain is
  `gm1 gm2 RD/(gm1 + gm2)`, non-inverting.
- `part1-027`: `Zout = (1 + s RS CGS1)/(gm1 + s CGS1)`, inductive when
  `RS > 1/gm1`.
- `part1-029`: the feedback is negative and the transimpedance tends to `-RF`.
- `part2-002`: the 6 dB holds at a fixed offset; an edge-rate argument without
  stating the frequency halving is complete, as in Razavi's 4.
- `part2-006`: any argument that `RX` stays on the order of `Req` is complete.
- `part2-007` and `part2-008`: the initial gain forms in the amplification
  phase; Q8 explains why the node capacitance cancels.
- `part2-012`: Razavi's reason (the clocked devices stay out of the data path)
  is accepted; "improves, then charge sharing limits it" is full credit.
- `part2-019`: explicit tiers replace a self-contradictory rule.
- `part2-020`: the oscillator can settle above or below `omega0`.

Seven references (`part1-013`, `part1-018`, `part1-025`, `part2-008`,
`part2-012`, `part2-019`, `part2-020`) were refined after reading the judge's
rationales on the first pass, and those questions were re-graded in full. Every
score here was given against the final reference.

| Question | Before | After | Answers up / down |
|---|---:|---:|---|
| `part1-004` | 82.8% | 85.1% | 22 / 4 |
| `part1-007` | 90.8% | 94.6% | 38 / 5 |
| `part1-008` | 93.7% | 96.2% | 25 / 3 |
| `part1-011` | 77.2% | 77.8% | 19 / 12 |
| `part1-012` | 71.5% | 74.1% | 26 / 6 |
| `part1-013` | 86.9% | 92.4% | 47 / 2 |
| `part1-018` | 72.2% | 72.2% | 24 / 19 |
| `part1-020` | 95.3% | 94.8% | 2 / 6 |
| `part1-021` | 25.2% | 24.4% | 9 / 11 |
| `part1-023` | 79.3% | 77.6% | 10 / 22 |
| `part1-025` | 71.1% | 68.1% | 7 / 28 |
| `part1-026` | 88.4% | 95.1% | 48 / 3 |
| `part1-027` | 70.0% | 68.4% | 27 / 40 |
| `part1-029` | 79.5% | 88.5% | 75 / 1 |
| `part2-002` | 83.2% | 82.7% | 6 / 11 |
| `part2-006` | 87.4% | 89.5% | 26 / 7 |
| `part2-007` | 62.0% | 60.1% | 1 / 19 |
| `part2-008` | 47.3% | 43.7% | 7 / 39 |
| `part2-012` | 64.6% | 64.8% | 7 / 9 |
| `part2-019` | 31.4% | 34.1% | 37 / 13 |
| `part2-020` | 60.6% | 56.3% | 7 / 41 |

Overall scores move by -1.50 to +2.33 points (12 entries unchanged); no entry
moves more than four places. Gemini 4 Argon stays first (96.83% -> 97.33%),
ahead of Claude Opus 5.5 (96.50%) and GPT-6 Astra (95.33%).

The 144 Part 1 Q20 and Q21 answers of the reasoning-trace probe were re-graded
with the same references (`../2026-11-05-reasoning-traces/`).

## Contents

- `gpt-6-luna-max.scores.jsonl`: the 4,851 new scores and rationales
- `merge.py`: replaces those scores in `docs/data/direct_qa/models/` (checking
  each answer's SHA-256) and recomputes the judge summaries; then run
  `tools/apply_active_judge.py` and `tools/aggregate_questions.js`
