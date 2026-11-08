# 2026-11-08 GPT-6 Luna re-grade of Part 1 Q15 and Q28 and Part 2 Q5 and Q16

The reference answers of four questions made physics claims that ngspice
simulations of the circuits (level-1 square-law devices, and BSIM4 defaults for
the ring oscillator) contradict. The answers were revised, and every published
answer to the four questions was re-graded by GPT-6 Luna at maximum reasoning
effort with `tools/evaluate_answers.py --model openai/gpt-6-luna
--reasoning-effort max --max-tokens 128000 --json-mode`: 922 answers, plus two
slots without a final answer that stay at 0 without a judge call (77 entries x 3
rollouts x 4 questions = 924). No answer model was re-run, and the scores of the
other 46 questions are unchanged.

- `part1-015` (two NMOS devices drawn as an inverter): the reference claimed the
  two devices' effects may cancel at a zero-gain bias point. With both devices
  on, `M2` is in triode and the circuit is a non-inverting attenuator with gain
  `1 - sqrt(K2/(K1 + K2))` (0.09 to 0.62 in simulation), with no zero-gain point.
  The scoring gate and full-credit rule are unchanged. This task's
  `golden_solution.md`, which the judge reads, had a scoring gate that the copy in
  `data/tasks.jsonl` lacked; both copies now match.
- `part1-028` (current input with positive feedback): the reference said the
  input resistance becomes "very large or even negative" at high loop gain. With
  `T = gm1 (RD1 || ro1) gm2 ro2`, `Rin = ro2/(1 - T)`, which for `T >> 1` is
  negative and small (-0.875 kohm in simulation at `T = 250`). That bias point
  has a right-half-plane pole, and the circuit latches within about 0.35 ns of a
  1 mV disturbance. Answers that say it latches or is bistable are now correct.
- `part2-005` (resistance into a ring oscillator's supply node): Razavi's
  `1/(3 f0 CL)` holds `f0` fixed. Simulation gives `IDD ~= 3 f0 CL VDD` but
  `RX ~= 1/(8 f0 CL)` to `1/(9 f0 CL)`, because `f0` rises with `VDD`. Answers
  that include this dependence, such as `1/(6 f0 CL)`, now also earn full credit,
  and the static `gm`-based answer, which Razavi scores 1, now earns 1.
- `part2-016` (inverter LNA noise figure with `Rin` held at 50 ohm): the
  reference called raising `gm` and `RF` the naive direction Razavi rejects.
  Keeping the match through `RF = Rs (1 + gm ro) - ro`, the noise figure falls
  monotonically as `gm` rises above `1/Rs`, from 3.9 dB to 0.3 dB in simulation,
  well below `1 + gamma` (2.22 dB). What Razavi rejects is pinning `gm` at `1/Rs`
  by making `ro` large with `RF` finite, which leaves the noise figure at about
  `1 + gamma`.

| Question | Before | After | Answers up / down | Full credit |
|---|---:|---:|---|---|
| `part1-015` | 27.8% | 27.2% | 2 / 7 | 55 -> 52 |
| `part1-028` | 67.5% | 81.3% | 96 / 6 | 94 -> 175 |
| `part2-005` | 81.7% | 86.1% | 34 / 1 | 162 -> 176 |
| `part2-016` | 28.6% | 67.5% | 156 / 8 | 3 -> 111 |

Overall scores move by -0.67 to +2.33 points (3 entries unchanged); no entry
moves more than four places. Gemini 4 Argon stays first (94.00% -> 95.50%).

## Contents

- `gpt-6-luna-max.scores.jsonl`: the 922 new scores and rationales
- `merge.py`: replaces those scores in `docs/data/direct_qa/models/` (checking
  each answer's SHA-256) and recomputes the judge summaries; then run
  `tools/apply_active_judge.py` and `tools/aggregate_questions.js`
