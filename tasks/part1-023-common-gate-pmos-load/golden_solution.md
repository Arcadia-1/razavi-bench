# Golden Solution - part1-023-common-gate-pmos-load

Figure 17 is a common-gate NMOS stage with a PMOS current-source load. The
input `Vin` is applied at the source side of `M2`, while the gate of `M2` is
biased by `Vb1`. `M1`, biased by `Vb2`, provides the PMOS current-source load
from `VDD`.

Because the input is at the source of `M2`, the stage is not a gate-driven
common-source amplifier. A small increase in the source input tends to reduce
`vgs2`, reducing the NMOS current and moving the output upward. Thus the gain is
non-inverting. The input resistance is low, on the order of `1/gm2`.

The voltage gain is set by the transconductance of `M2` times the resistance
seen at the output node. In the usual small-signal approximation,

`Av ≈ gm2 (ro1 || ro2)`.

Including body effect as `gm2 + gmb2`, or keeping finite-`ro`/`go` terms in a
more exact expression, is an acceptable refinement.

Full-credit rule for this task: assign score 4 to answers that identify the
common-gate NMOS stage with PMOS current-source load, place `Vin` at the source
of `M2`, identify `Vb1` and `Vb2` as bias voltages, describe the non-inverting
gain and low input resistance, and give `Av ≈ gm2(ro1 || ro2)` or an equivalent
gain expression. More detailed formulas for `Rin`, `Rout`, body effect, or
finite-`ro` are not required for full credit and should not reduce the score
unless they directly contradict the common-gate topology or the gain mechanism.
