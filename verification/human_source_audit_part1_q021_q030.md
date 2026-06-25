# Human Source Audit - Part 1 Q21-Q30

Date: 2026-06-26

Scope: `tasks/part1-021-*` through `tasks/part1-030-*`.

Method: compared the current golden solutions against the Part 1 source article figures and comments, with human review of the circuit interpretation. This PR records audit results only; it does not change golden solution text.

This PR also carries the remaining refreshed local Part 1 figure PNG assets for Q20-Q30, so the image-only asset updates can be reviewed with this audit slice.

## Results

| Q | Task | Human audit verdict | Risk | Proposed repo action |
|---|------|---------------------|------|----------------------|
| 21 | `part1-021-cascode-structure` | OK. The golden correctly rejects the standard cascode interpretation and identifies the lower device as a source-follower element rather than a common-source input device feeding a usual cascode. | Low | None. |
| 22 | `part1-022-explain-why-miller-effect-less-pronounced-cascode` | OK with minor clarification. The core point is correct: the cascode reduces the Miller multiplication of the input transistor `Cgd` because the intermediate node swings much less than the output. | Medium-low | Optional wording / boss check: keep the golden self-contained and say the local input-to-intermediate-node gain is order-unity negative, for example about `-1` to `-2` depending on parameters, rather than presenting a source-specific number as universal. |
| 23 | `part1-023-common-gate-pmos-load` | OK. The golden correctly describes a common-gate NMOS stage with a PMOS current-source load, with `Vin` applied at the source side of `M2`. | Low | None. |
| 24 | `part1-024-many-poles-have` | Needs wording fix. The two-pole conclusion is correct, but the standalone explanation should refer to the input/gate-side node, not an input/source-side node. The `CGS2` sentence is also confusing because the figure does not draw a `CGS2` capacitance at the output node. | Medium | Fix wording before or during a golden edit PR: describe the two independent dynamic nodes directly, and either remove the `CGS2` sentence or frame it as rejecting the article AI answer's nonexistent output-node `CGS2`. |
| 25 | `part1-025-series-nmos-effective-long-channel` | OK. The golden correctly treats the same-gate series NMOS pair as behaving approximately like a single transistor with longer effective channel length under the stated identical-device assumption. | Low | None. |
| 26 | `part1-026-source-follower-drives-common-gate` | OK with minor wording fix. The topology is correctly identified as source follower `M1` driving common-gate `M2`. | Low | Optional wording fix: replace "the output is taken at the drain of `M2` through `RD`" with "the output is the drain node of `M2`, and `RD` is the load from that node to `VDD`." |
| 27 | `part1-027-explain-why-output-impedance-be-inductive` | OK. The golden matches the source-follower intuition: low-frequency output impedance is approximately `1/gm1`, high-frequency behavior approaches the gate-drive resistance path through `CGS1`, and the transition can look inductive. | Low | None required. An optional explanatory note could mention the simplified form `Zout(s) ~= (1 + s RS CGS1)/(gm1 + s CGS1)`. |
| 28 | `part1-028-current-input-positive-feedback` | OK with minor wording fix. The golden correctly identifies the positive feedback loop and the negative-conductance contribution to the input conductance. | Low | Optional wording fix: replace "negative feedback-created term" with "negative-conductance term created by the positive feedback." |
| 29 | `part1-029-feedback-transimpedance-amplifier` | OK. The golden correctly treats `M1` as the common-gate input device, node `X` as the driver of `M2`, and `RF` as the feedback path from output to the input/source node. | Low | None. |
| 30 | `part1-030-pmos-current-input-feedback` | Needs fix. The current golden preserves the important feedback-loop point, but its device identification and topology description are inconsistent with the circuit: visual review indicates `M1` is NMOS, while `M2` is PMOS with source at `VDD`, drain at the input node, and gate tied to `Vout`. | High | Fix in a follow-up golden edit PR. Suggested direction: describe the circuit as a two-node feedback network, `input node -> M1 -> Vout -> M2 -> input node`, then write KCL at both the input/current-summing node and `Vout` to solve the closed-loop transimpedance. |

## Follow-Up Notes

Q24 and Q30 should be highlighted for reviewer attention before golden text edits. Q22, Q26, Q27, and Q28 are mostly wording or explanatory polish. No executable tests are associated with this audit-only change.
