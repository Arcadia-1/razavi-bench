# Golden Solution - part1-023-common-gate-pmos-load

Figure 17 is a common-gate NMOS stage with a PMOS current-source load. The
input `Vin` is applied at the source side of `M2`, while the gate of `M2` is
biased by `Vb1`. `M1`, biased by `Vb2`, provides the PMOS current-source load
from `VDD`.

Because the input is at the source of `M2`, the stage is not a gate-driven
common-source amplifier. A small increase in the source input tends to reduce
`vgs2`, reducing the NMOS current and moving the output upward. Thus the gain is
non-inverting.

The voltage gain is set by the transconductance of `M2` times the resistance
seen at the output node:

`Av = [1 + (gm2 + gmb2) ro2] ro1/(ro1 + ro2) ≈ gm2 (ro1 || ro2)`.

The input resistance is low, but with the current-source load it is not simply
`1/gm2`:

`Rin = (ro1 + ro2) / [1 + (gm2 + gmb2) ro2] ≈ (1/gm2)(1 + ro1/ro2)`,

roughly `2/gm2` for comparable output resistances, and it grows without bound as
the load approaches an ideal current source.

Razavi scores 0 ChatGPT's answer, which places `Vin` at the gate of `M2` and
calls the circuit a common-source amplifier with an active load.

Including body effect as `gm2 + gmb2`, or keeping finite-`ro`/`go` terms in a
more exact expression, is an acceptable refinement.

Full-credit rule for this task: assign score 4 to answers that identify the
common-gate NMOS stage with PMOS current-source load, place `Vin` at the source
of `M2`, identify `Vb1` and `Vb2` as bias voltages, describe the non-inverting
gain and low input resistance, and give `Av ≈ gm2(ro1 || ro2)` or an equivalent
gain expression. More detailed formulas for `Rin`, `Rout`, body effect, or
finite-`ro` are not required for full credit and should not reduce the score
unless they directly contradict the common-gate topology or the gain mechanism.
Describing `Rin` as low, on the order of `1/gm2`, or giving the formula above
are both acceptable; saying that `Rin` exceeds `1/gm2` with this load is correct.
An answer that places `Vin` at the gate of `M2` earns 0, Razavi's score.
