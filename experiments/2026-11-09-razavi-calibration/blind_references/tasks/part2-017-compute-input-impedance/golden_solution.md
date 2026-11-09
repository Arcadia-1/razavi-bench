# Golden Solution - part2-017-compute-input-impedance

Model the TIA as Razavi's simplified model does (his Figure 14(b), which the question does not show): the input node drives an amplifier of unloaded voltage gain `-A0`, whose output resistance is `RD2`, and `RF` connects the input node to the amplifier's output. Apply Miller's theorem to the feedback resistor.

The exact input resistance is

`Rin = (RF + RD2) / (1 + A0)`

where the unloaded gain is

`A0 = (1/2) gm1 gm2,3 RD1 RD2`.

This expression follows the actual two-stage model and includes the resistance at the output side of the feedback path.

A complete answer should give the exact Miller-theorem result `Rin = (RF + RD2)/(1 + A0)`, with `A0 = (1/2) gm1 gm2,3 RD1 RD2` or an equivalent unloaded-gain definition.

An answer that only writes `Rin = RF/(1 + Avol)` using a loaded gain such as `RD2 || RF` misses the exact resistance at the output side of the feedback path.
