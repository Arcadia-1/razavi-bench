# Golden Solution - part1-008-source-follower

Figure 5 is a source follower. The input is applied to the gate, the output is at the source, and `RS` is the source load to ground.

Neglecting body effect and `ro`,

`Av = vout/vin ~= gm RS / (1 + gm RS)`.

The gain is positive and less than unity. The resistance looking into the source of the transistor is `1/gm` (or `1/(gm + gmb)` with body effect), so the output resistance of the stage is `Rout = RS || (1/gm)`.

Full-credit rule: give full credit if the answer identifies the source follower and gives its positive, less-than-unity gain `gm RS/(1 + gm RS)` or an equivalent form. The output resistance is supplementary: do not deduct for omitting it, or for writing it as about `1/gm` when `gm RS >> 1`. Including body effect or `ro` is a welcome refinement. An answer that identifies the source follower but says only that the gain is close to one, without an expression, earns at most 3. An answer that misreads the topology earns at most 1.
