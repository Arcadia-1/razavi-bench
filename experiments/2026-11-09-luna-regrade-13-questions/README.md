# 2026-11-09 GPT-6 Luna re-grade of 13 questions

The reference answers of 13 questions were brought in line with Razavi's own
comments and scores in the two articles, and every published answer to them
(77 entries x 3 rollouts x 13 questions = 3,003 answers) was re-graded by GPT-6
Luna at maximum reasoning effort with `tools/evaluate_answers.py --model
openai/gpt-6-luna --reasoning-effort max --max-tokens 128000 --json-mode`. No
answer model was re-run, and the scores of the other 37 questions are unchanged.

Where Razavi scored an article answer, the revised reference gives an answer of
the same kind the same score.

- `part1-006` (can a diode-connected device act as a current source?): Razavi
  names two mistakes, missing the low impedance and calling the PMOS an NMOS.
  Identifying the PMOS is now required; the low-impedance answer that calls it an
  NMOS earns at most 2, and "no, because the NMOS is off" earns 0.
- `part1-010` (source input shorted to ground): missing the short but reading
  the common-gate topology earns 1, Razavi's score; misreading the topology too
  earns 0.
- `part1-014` (CMOS inverter): Razavi gives "This is the classic CMOS inverter"
  4. The small-signal gain at the switching point was effectively required and
  is now optional.
- `part1-016` (common-source stage with a diode-connected load): `-gm1/gm2` and
  `-gm1 (1/gm2 || ro1 || ro2)` are both full credit; a mixed treatment of
  channel-length modulation earns 3, Razavi's score.
- `part1-019` (keeping M2 saturated): the reference now states that both
  devices are PMOS and accepts every equivalent form of Razavi's condition on
  `Vb1`. Giving the condition only in terms of `VX` and `Vb2` earns 1, Razavi's
  score for that answer.
- `part1-024` (number of poles): the reference no longer calls the output a
  cascode node, lists `CGD2` at the output, and no longer requires a discussion
  of how `CGD` loads both nodes; two poles with a wrong capacitor at the output
  earns 3, Razavi's score.
- `part1-030` (current-input feedback): reading `M1` as a PMOS device earns 1
  instead of 0 when the rest of the analysis is right, as in Razavi's score for
  a device-type confusion with a correct gain (Part 1 Q7). The reference notes
  that the article's caption about `M1` refers to `M2`.
- `part2-001` (ring with three large capacitors): a delay argument or a
  small-signal argument is complete, as in Gemini's answer that Razavi scores 4;
  the contrast with loading one node is optional. "It fails to oscillate" earns
  at most 1.
- `part2-004` (doubling the ring's widths): about 3 dB is the answer, as Razavi
  scores it; "phase noise decreases" without a magnitude earns at most 2.
- `part2-010` (widening the clocked transistors): Razavi's "if the data-driven
  devices are the bottleneck" grants Gemini's premise and is no longer a
  required condition. "Improves initially, up to an optimum" earns 4, and
  "degrades" earns 2, Razavi's score.
- `part2-011` (quadrature outputs): Miller multiplication within `Inv3` is
  Razavi's example of the unequal latch loading, not a separate requirement;
  either `X` and `Y` or `X` and `Z` may be named as the nominal pair.
- `part2-014` and `part2-015` (the red inverter): the reference now explains
  how the unclocked branch overpowers the main path (with the `CKbar` switch on
  it closes a three-inversion ring and fights `Inv1`) and accepts that
  description.

Four references were refined while the re-grade ran, after reading the judge's
rationales, and those questions were re-graded in full: `part1-019` (an answer
that gives `VX = Vb1 + |VGS1|` and the bound on `VX` has given the condition on
`Vb1`), `part1-006` (an answer saying "no, because the NMOS is off" earns 0;
adding that the device carries a nearly constant leakage current for `VX` below
ground is not a claim that it acts as a current source), `part2-010` (a hedged
answer that still gives the initial improvement and the optimum earns full
credit) and `part2-004` (an argument from the node capacitance is valid). Every
score here was given against the final reference.

| Question | Before | After | Answers up / down | Full credit |
|---|---:|---:|---|---|
| `part1-006` | 45.5% | 37.6% | 1 / 59 | 93 -> 58 |
| `part1-010` | 69.9% | 71.4% | 22 / 9 | 150 -> 157 |
| `part1-014` | 68.7% | 98.2% | 166 / 0 | 62 -> 221 |
| `part1-016` | 86.4% | 88.0% | 43 / 23 | 147 -> 184 |
| `part1-019` | 68.2% | 59.2% | 23 / 86 | 97 -> 104 |
| `part1-024` | 71.4% | 71.2% | 29 / 28 | 137 -> 137 |
| `part1-030` | 62.0% | 62.0% | 14 / 10 | 136 -> 137 |
| `part2-001` | 85.9% | 82.5% | 3 / 35 | 176 -> 170 |
| `part2-004` | 90.5% | 87.3% | 6 / 35 | 166 -> 170 |
| `part2-010` | 64.9% | 70.0% | 65 / 19 | 67 -> 77 |
| `part2-011` | 43.9% | 48.4% | 47 / 7 | 0 -> 17 |
| `part2-014` | 24.4% | 31.2% | 68 / 16 | 11 -> 16 |
| `part2-015` | 39.4% | 40.2% | 35 / 32 | 8 -> 15 |

Overall scores move by -1.33 to +2.00 points (3 entries unchanged); no entry
moves more than five places. Gemini 4 Argon stays first (95.50% -> 96.83%),
ahead of Claude Opus 5.5 (96.17%) and GPT-6 Astra (95.17%).

The 72 Part 1 Q14 answers of the reasoning-trace probe were re-graded with the
same reference (`../2026-11-05-reasoning-traces/`).

## Contents

- `gpt-6-luna-max.scores.jsonl`: the 3,003 new scores and rationales
- `merge.py`: replaces those scores in `docs/data/direct_qa/models/` (checking
  each answer's SHA-256) and recomputes the judge summaries; then run
  `tools/apply_active_judge.py` and `tools/aggregate_questions.js`
