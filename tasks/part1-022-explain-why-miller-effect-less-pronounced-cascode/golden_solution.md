# Golden Solution - part1-022-explain-why-miller-effect-less-pronounced-cascode

In a cascode, the drain of the input common-source transistor is held at a relatively low-impedance node by the common-gate cascode device. Therefore the voltage swing across the input transistor's `Cgd` is much smaller than in a single common-source stage whose drain has a large gain swing.

The Miller multiplication of `Cgd` is reduced because the gain from the input gate to the input transistor's drain is small compared with the total stage gain. It is not necessarily zero; Razavi notes that the effective gain across `Cgd1` can be around `-2`, but this is far smaller than the full output gain of the cascode stage.
