# Golden Solution - part1-008-source-follower

Figure 5 is a source follower. The input is applied to the gate, the output is at the source, and `RS` is the source load.

Neglecting body effect and `ro`,

`Av = vout/vin ~= gm RS / (1 + gm RS)`.

The gain is positive and less than unity. The output resistance looking into the source is approximately `1/gm` in parallel with `RS`.
