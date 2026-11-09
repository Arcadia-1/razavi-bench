# 2026-11-09 Calibration against Razavi's own scores

Razavi's two articles print the AI answers he scored: ChatGPT's answers to the 30
Part 1 questions (49/120, 41%) and Gemini 3.1 Pro's answers to the 20 Part 2
questions (44/80, 55%). This experiment grades those 50 answers with the
benchmark's judge and references and compares the result with Razavi's scores,
question by question.

- `build_answers.py` holds the 50 answers transcribed from the article pages, with
  Razavi's scores, and writes `article_answers.jsonl`. Each answer is listed three
  times (rollouts 1-3) so that the judge grades it three times independently.
- Judge: GPT-6 Luna at maximum reasoning effort, with `tools/evaluate_answers.py
  --model openai/gpt-6-luna --reasoning-effort max --max-tokens 128000
  --json-mode`. The per-question score is the median of the three gradings.
- Control: 38 references quote the article's answer and Razavi's score, which
  makes grading those same answers partly circular. `make_blind_references.py`
  writes `blind_references/`, a copy of the tasks with the 60 sentences that state
  a verdict on the article's answers removed, and the answers were graded again
  against it (`--repo blind_references`). The control uses the references as they
  stood before the four rules below were added.

## Result

| | Razavi | Judge, current references | Judge, blind references |
|---|---:|---:|---:|
| Part 1 (ChatGPT) | 40.8% | 40.8% | 38.1% |
| Part 2 (Gemini 3.1 Pro) | 55.0% | 52.1% | 48.8% |
| Same score as Razavi | | 48 / 50 | 33 / 50 |
| Within 1 point | | 49 / 50 | 46 / 50 |

The first grading against the current references matched 44 of 50 questions.
Four of the six differences came from references stricter than Razavi, and a
scoring rule taken from his verdict was added to each:

- `part1-003`: "the same model" is complete; polarity conventions are optional.
- `part1-005`: a quadratic rise from `VTH` implies the cutoff region.
- `part1-028`: reading `M2` as diode-connected and missing the positive feedback,
  with `M1` and the current input right, earns 1.
- `part2-013`: identifying a divide-by-two built from dynamic latches is complete.

The 12 gradings of those four questions were redone against the new references
(`scores-gpt-6-luna-max.recal4.jsonl`). The two questions still apart, `part2-001`
and `part2-003`, are a limit of the transcription: the article prints Gemini's
yes/no conclusions and notes that a small-signal analysis was also provided, but
not the analysis that earned the 4. Their references are left unchanged.

The blind control shows that the totals do not depend on the quoted verdicts
(within 3-6 points of Razavi), while the per-question agreement does: the
partial-credit scale for a given kind of mistake (for example a wrong device type
with the right gain) is Razavi's and has to be written into the reference.

## Contents

- `build_answers.py`, `article_answers.jsonl`: the transcribed answers and scores
- `article_answers_recal4.jsonl`: the 12 rows of the four re-graded questions
- `scores-gpt-6-luna-max.jsonl`, `scores-gpt-6-luna-max.recal4.jsonl`: gradings
  against the current references; `compare.py` keeps only those given against
  each task's current `golden_solution.md`
- `make_blind_references.py`, `blind_references/`, `scores-blind-gpt-6-luna-max.jsonl`:
  the control
- `compare.py`, `per_question.csv`: the comparison
