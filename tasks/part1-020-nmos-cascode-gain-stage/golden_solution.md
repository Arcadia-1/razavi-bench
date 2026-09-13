# Golden Solution - part1-020-nmos-cascode-gain-stage

Figure 15 is an NMOS cascode gain stage. `M1` is the input common-source transistor, `M2` is the common-gate cascode transistor biased by `Vb1`, and `I1` is the load current source at the output.

A change in `vin` changes the drain current of `M1`; `M2` conveys this current to the output while holding node `X` relatively quiet. The output is therefore an inverted voltage at the drain of `M2`.

The small-signal gain is approximately

`Av ~= -gm1 Rout`

where `Rout` is the resistance seen at the output, including the current-source load and the boosted resistance of the cascoded NMOS stack. The circuit should not be described as a common-source stage with a PMOS active load; `M2` is an NMOS cascode device.

If `I1` is treated as an ideal current-source load, its small-signal resistance is infinite. In that case it is acceptable to write the output-node KCL as zero small-signal current through the cascode stack and derive

`vout = vx [1 + (gm2 + gmb2) ro2]`

and

`vx = -gm1 ro1 vin`

so that

`Av = -gm1 ro1 [1 + (gm2 + gmb2) ro2] ~= -gm1 (gm2 + gmb2) ro1 ro2`.

This is the same result as `Av ~= -gm1 Rout` for an ideal current-source load. With a finite current-source output resistance, that load resistance simply appears in parallel with the cascode-stack output resistance.

Full-credit rule: give full credit if the answer identifies `M1` as the common-source input NMOS, `M2` as the common-gate NMOS cascode, and gives either `Av ~= -gm1 Rout` or the equivalent ideal-load expression `Av ~= -gm1 (gm2 + gmb2) ro1 ro2` (body effect may be omitted as `gm2`). Do not penalize an answer for assuming an ideal current-source load or for deriving the gain from the zero-small-signal-current KCL under that ideal-load assumption.
