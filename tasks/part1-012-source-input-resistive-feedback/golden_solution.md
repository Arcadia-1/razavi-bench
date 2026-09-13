# Golden Solution - part1-012-source-input-resistive-feedback

Figure 9 is a feedback voltage amplifier. The input `Vin` is applied to the
source of `M1`, the output `Vout` is taken at the drain, and the `R1`-`R2`
divider feeds a fraction of the output voltage back to the gate:

`vF = beta vout`, where `beta = R2/(R1 + R2)`.

The transistor is controlled by the small-signal error voltage

`vgs = vF - vin`.

Let `RL = RD || (R1 + R2)`. Ignoring channel-length modulation and body effect,
KCL at the output gives the closed-loop voltage gain

`vout/vin = gm RL / (1 + gm beta RL)`.

For large loop gain, this approaches

`vout/vin approx 1/beta = 1 + R1/R2`.

This gain expression and the feedback interpretation are the essential answer.

Full-credit rule for this task: assign score 4 to answers that identify the
source input, the divider feedback to the gate, and the closed-loop voltage gain
above, either in exact form or in the large-loop-gain form. The exact expression
does not need to be simplified all the way to `1/beta` if it is algebraically
equivalent. It is acceptable to call the stage common-gate, common-gate-like,
source-input, series-shunt feedback, voltage-voltage feedback, or a
voltage-feedback amplifier as long as the answer clearly recognizes that the
gate is driven by the feedback divider and the gain relation is correct.

Input/output resistance discussion, body-effect refinements, finite-`ro`
corrections, and DC bias concerns are not required for this task. They may
improve an answer, but mistakes or omissions in those topics should not reduce a
score-4 answer unless they directly contradict the source-input/gate-feedback
model or the closed-loop gain result. Including `gmb` in the gain expression is
an acceptable refinement and should not reduce the score.

Do not give full credit to answers that miss the feedback path, treat the gate
as fixed at AC ground, treat the source as grounded, or fail to recognize that
`Vin` is the source input and `Vout` is the voltage output.
