# Human Source Audit - Part 1 Q11-Q20

Date: 2026-06-25

Scope: `tasks/part1-011-*` through `tasks/part1-020-*`.

Method: compared each current `golden_solution.md` against the corresponding question, figure, ChatGPT answer, and Razavi comment in "Analog Design Experiments With AI - Part 1." This PR records the review result only; it does not modify task golden solutions.

## Results

| Q | Task | Human audit verdict | Risk | Proposed repo action |
|---|---|---|---|---|
| 11 | `part1-011-many-poles-have` | OK | Low | None. The current golden correctly counts independent energy-storage state variables rather than capacitors drawn. |
| 12 | `part1-012-source-input-resistive-feedback` | OK | Low | None. The current golden correctly keeps `Vin` at the source and treats `R1`/`R2` as output-to-gate feedback. |
| 13 | `part1-013-source-follower-current-source-load` | OK | Low | None. The current golden correctly identifies the source-follower topology and rejects the common-source active-load reading. |
| 14 | `part1-014-cmos-inverter` | OK | Low | None. The current golden matches the standard CMOS inverter in Figure 11(a). |
| 15 | `part1-015-malformed-cmos-inverter` | Needs clarification | Medium-low | Clarify the actual circuit behavior, not only that it is not a proper CMOS inverter. A useful note would describe its degraded non-inverting/source-follower-like behavior and threshold-limited swing. |
| 16 | `part1-016-common-source-diode-connected-load` | OK | Low | None. The current golden correctly identifies the common-source NMOS stage with diode-connected PMOS load. |
| 17 | `part1-017-pmos-input-invalid-pulldown` | Needs fix | High | Fix the device identification and analysis. The lower `M1` is not an NMOS with gate/source grounded; as drawn it should be treated as a PMOS-like nonlinear pull-down/load under the source-at-higher-potential convention. |
| 18 | `part1-018-find-rout` | OK | Medium-low | None. The current golden correctly assigns the cascode/common-gate output-resistance boost to lower PMOS `M1`. |
| 19 | `part1-019-ensure-m2-saturation` | OK with minor clarification | Medium-low | Optional wording clarification: `Vb2` sets the upper PMOS overdrive/saturation boundary, while `Vb1` controls whether node `X` leaves enough `VSD2`; both constraints must hold together. |
| 20 | `part1-020-nmos-cascode-gain-stage` | OK | Low | None. The current golden correctly identifies Figure 15 as an NMOS cascode gain stage and rejects the PMOS active-load interpretation. |

## Follow-up Notes

- Q15 is comment-aligned but analysis-incomplete: the golden reaches the right high-level conclusion, but a future edit should explain what the malformed topology actually does.
- Q17 appears to be a substantive golden issue and should be fixed in a separate, focused PR.
- Q19 is acceptable, but a small wording pass would make clear that `Vb1` and `Vb2` impose simultaneous saturation constraints.
