# Human Source Audit: Part 1 Q1-Q10

Date: 2026-06-25

Scope: `tasks/part1-001-*` through `tasks/part1-010-*`.

Method: direct comparative reading against Razavi, "Analog Design Experiments
With AI - Part 1," with visual inspection of the referenced figures. This
slice checks whether each `golden_solution.md` is technically correct and
source-aligned. It does not add simulator validation.

Overall result: all ten reviewed golden solutions are OK. No repository changes
to these task answers are proposed in this slice.

The entry fields follow issue #1's suggested review shape:
`Task`, `Golden solution`, `Rubric implications`, `Notes`, and
`Suggested change`.

| Task | Golden solution | Rubric implications | Notes | Suggested change |
|---|---|---|---|---|
| `part1-001-double-length-and-width-mosfet-its-intrinsic` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q1. The golden solution matches the source's constant-overdrive interpretation: `W/L` stays fixed, `gm` is approximately unchanged, and `ro` increases with channel length. | None. |
| `part1-002-student-says-transconductance-mosfet-goes-up-as` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q2. The golden solution correctly distinguishes the fixed-`W/L` reading from the fixed-`ID` reading and preserves the source's preferred fixed-size conclusion. | None. |
| `part1-003-small-signal-model-pmos-device-identical-nmos` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q3. The golden solution correctly treats PMOS and NMOS small-signal models as structurally equivalent when consistent terminal polarities and sign conventions are used. | None. |
| `part1-004-sketch-ix-versus-vx` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q4, Figure 1. The golden solution correctly identifies the diode-connected NMOS behavior: near-zero current below threshold and square-law rise after turn-on. | None. |
| `part1-005-sketch-ix-versus-vx` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q5, Figure 2. The golden solution correctly reads the circuit as a gate sweep with fixed `VDS = 1 V`: off below threshold, quadratic in saturation, then approximately linear after entering triode. | None. |
| `part1-006-device-act-as-current-source` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q6, Figure 3. The golden solution correctly rejects a diode-connected MOS device as a good current source because it presents low small-signal resistance rather than high output resistance. | None. |
| `part1-007-pmos-common-source-source-degeneration` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q7, Figure 4. The golden solution correctly identifies the device as PMOS and the circuit as a common-source stage with source degeneration. | None. |
| `part1-008-source-follower` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q8, Figure 5. The golden solution correctly identifies the NMOS source follower and its positive sub-unity gain. | None. |
| `part1-009-common-gate-source-input` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q9, Figure 6. The golden solution correctly notices that the input is applied at the source, so the circuit is common-gate rather than common-source. | None. |
| `part1-010-source-input-shorted-to-ground` | OK | No task-specific rubric change identified. | Source anchor: Part 1 Q10, Figure 7. The golden solution correctly notices the source-to-ground short, so the ideal small-signal transfer from `Vin` is approximately zero. | None. |
