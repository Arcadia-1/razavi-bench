# P2 Q6 and Q12 rerun (2026-11-10)

The user approved restoring two questions to Razavi's wording (commit 728956d on
`question-only-rerun`), which settles the pending review in
`../round456.proposed-input-changes.json`:

- `part2-006-oscillates-change` no longer states `RX ~= 1/(3 f0 CL)` or defines
  `TD`. It asks Razavi's question, "If the circuit oscillates, does this answer
  change?", after the static answer `RX ~= (1/3)(1/gmn + 1/gmp)` it follows up on in
  the article. Its reference was rewritten for the new question.
- `part2-012-repeat-question-10-for-topology` uses Q10's sentence, without the
  circuit name or the clock-terminal explanation.

This folder holds the answers to these two questions for every API entry run so
far: the 30 entries in `../runs`, `../batch3/runs` and `../batch3/addon_hy4/runs`
(whose earlier answers to the two questions are now stale) and the 20 entries of
`../batch4` and `../batch5` (which had not answered them). It was produced with

    python3 ../run.py --only <each entry> --output-dir q6q12 \
        --task-slug part2-006-oscillates-change \
        --task-slug part2-012-repeat-question-10-for-topology

with the entries' settings unchanged in `run.py`, and graded by GPT-6 Luna at
maximum effort (`scores-gpt-6-luna-max.jsonl`). For each entry, the score over
the 50 questions is its batch's scores for the other 48 questions plus these.

Batches 4 and 5 do not need to answer the two questions again; an input
snapshot taken before 728956d (such as `../inputs456-e65d05f2e2741af4`) still
holds the old wording and must not be used for them.

The self-hosted entries were rerun with `../run_selfhosted.py` into
`../runs_selfhosted/`.

Re-grading Gemini's article answers to the two questions against the new
references still gives Razavi's score (1 and 1), so the calibration in
`../../2026-11-09-razavi-calibration/` stays at 48 of 50.
