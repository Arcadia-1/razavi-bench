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

The loop is negative feedback: if `vout` rises, `vF` rises, `vgs` grows, `M1`
draws more current and `vout` falls back. The closed-loop gain is non-inverting.

Razavi scores 3 ChatGPT's answer "M1: NMOS, source at ground. R1-R2: resistor
divider at output. The circuit has negative feedback," commenting that it is
mostly correct except that ChatGPT believes the source of `M1` is grounded.

Full-credit rule for this task: assign score 4 to answers that identify the
source input, the divider feedback from the output to the gate, and the negative
feedback (stated, or evident from a correct closed-loop gain). The closed-loop
gain above, in exact form or as `1 + R1/R2` for large loop gain, is welcome but
not required, since Razavi's only objection to ChatGPT's answer is the grounded
source. A gain expression need not be simplified all the way to `1/beta` if it
is algebraically equivalent, and using `RD` for `RD || (R1 + R2)` when
`R1 + R2 >> RD` is acceptable. It is acceptable to call the stage common-gate, common-gate-like,
source-input, series-shunt feedback, voltage-voltage feedback, or a
voltage-feedback amplifier as long as the answer clearly recognizes that the
gate is driven by the feedback divider and the gain relation is correct.

Input/output resistance discussion, body-effect refinements, finite-`ro`
corrections, and DC bias concerns are not required for this task. They may
improve an answer, but mistakes or omissions in those topics should not reduce a
score-4 answer unless they directly contradict the source-input/gate-feedback
model or the closed-loop gain result. Including `gmb` in the gain expression is
an acceptable refinement and should not reduce the score.

An answer that recognizes the divider feedback to the gate and the negative
feedback but treats the source as grounded earns 3, Razavi's score. An answer
with the correct topology and feedback but a wrong closed-loop gain, such as an
inverting one, earns 3. An answer that misses the feedback path or treats the
gate as fixed at AC ground earns at most 1.
