# Golden Solution - part1-022-explain-why-miller-effect-less-pronounced-cascode

In a cascode, the drain of the input common-source transistor `M1` drives the source of the common-gate device `M2`, a relatively low-impedance node: about `1/(gm2 + gmb2)` when the load impedance is not too large. The small-signal swing at the drain of `M1` is therefore much smaller than at the output, whereas in a simple common-source stage `Cgd` connects the input to the full-gain output.

The gain from the gate of `M1` to its drain is about `-gm1/(gm2 + gmb2)`, roughly `-1` when `M1` and `M2` have similar dimensions. `Cgd1` is thus multiplied by about `1 + gm1/(gm2 + gmb2)`, roughly 2, instead of by one plus the full stage gain. The Miller effect is reduced but not eliminated: the voltage across `Cgd1` is about twice the input swing, which is the sense of Razavi's remark that the effective gain across `Cgd1` is about 2 in magnitude, not very small.

A complete answer explains the low-impedance node at the drain of `M1` and the resulting small gain across `Cgd1`. Calling that gain negligible or near zero, or the drain of `M1` an AC ground, overstates the effect and is a minor flaw.
