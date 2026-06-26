# Human Source Audit - Part 1 Q11-Q20

Date: 2026-06-25

Scope: `tasks/part1-011-*` through `tasks/part1-020-*`.

Method: compared each current `golden_solution.md` against the corresponding question, figure, ChatGPT answer, and Razavi comment in "Analog Design Experiments With AI - Part 1." This PR records the review result only; it does not modify task golden solutions.

The entry fields follow issue #1's suggested review shape: `Task`, `Golden solution`, `Rubric implications`, `Notes`, and `Suggested change`. Rubric comments in this slice are task-specific only; the global 0-4 grading policy still needs a separate full pass.

## Results

| Task | Golden solution | Rubric implications | Notes | Suggested change |
|---|---|---|---|---|
| `part1-011-many-poles-have` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden correctly counts independent energy-storage state variables rather than simply counting capacitors drawn. | None. |
| `part1-012-source-input-resistive-feedback` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden correctly keeps `Vin` at the source and treats `R1`/`R2` as output-to-gate feedback. | None. |
| `part1-013-source-follower-current-source-load` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden correctly identifies the source-follower topology and rejects the common-source active-load reading. | None. |
| `part1-014-cmos-inverter` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden matches the standard CMOS inverter in Figure 11(a). | None. |
| `part1-015-malformed-cmos-inverter` | OK after clarification | OK; reward answers that explain the malformed circuit behavior, not only answers that say it is not a proper CMOS inverter. | Follow-up golden edit added the degraded source-follower/pass-device-like behavior and threshold-limited swing. | None after the clarification edit. |
| `part1-016-common-source-diode-connected-load` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden correctly identifies the common-source NMOS stage with diode-connected PMOS load. | None. |
| `part1-017-pmos-input-invalid-pulldown` | OK after fix | OK; do not reward the NMOS-cutoff-style interpretation as fully correct. | Follow-up golden edit identifies both devices as PMOS and analyzes lower `M1` as a diode-connected PMOS load using the source-at-higher-potential convention. | None after the device-identification fix. |
| `part1-018-find-rout` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden correctly assigns the cascode/common-gate output-resistance boost to lower PMOS `M1`. | None. |
| `part1-019-ensure-m2-saturation` | OK with minor clarification | OK; no task-specific rubric issue identified beyond aligning any future wording clarification. | The answer is acceptable, but the simultaneous role of `Vb1` and `Vb2` can be clearer. `Vb2` sets the upper PMOS overdrive/saturation boundary, while `Vb1` controls whether node `X` leaves enough `VSD2`; both constraints must hold together. | Optional wording clarification that both `Vb1` and `Vb2` impose simultaneous saturation constraints. |
| `part1-020-nmos-cascode-gain-stage` | OK | OK; no task-specific rubric issue identified in this source-audit slice. | The current golden correctly identifies Figure 15 as an NMOS cascode gain stage and rejects the PMOS active-load interpretation. | None. |

## Follow-up Notes

- Q15 has been clarified to explain the malformed topology's degraded source-follower/pass-device-like behavior.
- Q17 has been fixed to identify lower `M1` as PMOS rather than an off NMOS.
- Q19 is acceptable, but a small wording pass would make clear that `Vb1` and `Vb2` impose simultaneous saturation constraints.
