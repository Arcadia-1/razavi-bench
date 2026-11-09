# Golden Solution - part1-010-source-input-shorted-to-ground

In Figure 7, `Vin` is coupled through `C1` to the source node of `M1`, but that same source node is directly shorted to ground. The gate is biased by `Vb`, and the output is taken at the drain through `RD`.

Because the input is applied to a node that is hard-shorted to ground, the ideal small-signal voltage at the source is zero. Therefore the transistor does not receive a useful small-signal input from `Vin`.

At midband, with an ideal short to ground,

`vout/vin ~= 0`.

The circuit is not a valid common-gate amplifier as drawn; the source-ground short must be noticed before assigning a gain expression. Only nonideal source impedance or parasitics in the short would allow a residual signal to appear at the source.

Full-credit rule: give full credit if the answer notices that the source is shorted to ground and concludes that the input is shorted, so the circuit provides no (ideally zero) voltage gain from `Vin`. An answer that misses the short and also misreads the topology, for example by placing the input at the gate, earns 0. An answer that notices the short but still assigns a common-gate gain as if it were absent earns at most 2.
