# Part 1 Q15 score correction - 2026-07-19

This experiment re-scores only
`part1-015-malformed-cmos-inverter` after the golden solution was corrected on
`origin/main`.

The corrected golden states that Figure 11(b) contains two NMOS devices: the
upper NMOS is a source-follower pull-up and the lower NMOS is a common-source
pull-down. It is not a normal complementary CMOS inverter. The final hard-rule
golden assigns 0 if an answer misidentifies either transistor type, or if it
analyzes the circuit as a complementary push-pull stage or ordinary CMOS
inverter.

## Scope

- No answer model was rerun.
- No historical `model_outputs/` file was modified.
- All non-Q15 scores are reused unchanged.
- Part 2 scores are unchanged.
- Historical Q15 scores remain in the provenance manifest and are marked
  `superseded_by_2026-07-19-part1-q15-score-correction`.

The canonical manifest contains 36 unique Q15 answer sources: 24 Direct QA
sources and 12 agentic multimodal sources. Each source was re-scored once by
MiniMax M3 and once by DeepSeek V4 Pro, for 72 new Q15 judgments.

## Judges

The re-score uses the current repository-level evaluator:

- MiniMax M3
- DeepSeek V4 Pro

Both runs use the current `evaluation_rubric.md`, current judge system prompt,
current `tools/evaluate_answers.py`, and the final hard-rule Q15 golden
solution. The public score rows retain answer hashes, golden/rubric/script/system
hashes, judge model names, and repo commit provenance. Private raw judge
rationales and private Vela source artifacts are not included.

An earlier soft-gate re-score was kept only as private pre-hard-rule audit
material and is not used by the public active scores, aggregates, dashboard, or
figures.

## Q15 score shift

| Judge | Old Q15 mean | New Q15 mean | Delta |
|---|---:|---:|---:|
| MiniMax M3 | 2.389 / 4 | 0.222 / 4 | -2.167 |
| DeepSeek V4 Pro | 2.778 / 4 | 0.222 / 4 | -2.556 |

Both judges assigned 0 to 34 of 36 Q15 answers and 4 to the same two answers.
The two nonzero answers explicitly identify both devices as NMOS and describe
the upper source-follower pull-up and lower common-source pull-down actions.

## Active aggregates

Current active aggregates apply the Q15 overlay and leave every other task
score unchanged:

- `judge_scores/direct_active_comparison.csv`
- `judge_scores/direct_active_comparison_by_judge.csv`
- `judge_scores/agentic_active_comparison.csv`
- `judge_scores/agentic_active_comparison_by_judge.csv`
- `judge_scores/active_score_summary.csv`
- `judge_scores/aggregate_deltas.csv`

The public leaderboard and figures under `experiments/2026-07-18-direct-qa/`,
`experiments/2026-07-15-direct-qa/`, `docs/assets/`, and the static dashboard
embed the same corrected active aggregate.

## Validation

`validation_report.json` records the source count, score count, corrected
golden hash, parse-error count, and Part 2 invariant check. The public
correction files contain no private Vela paths, Vela record/session/task IDs,
or local absolute paths.
