# Golden Solution - part1-013-source-follower-current-source-load

Figure 10 is a source follower, not a common-source amplifier with an active load. `M1` receives the input at its gate, and the output is taken from its source. `M2` provides a bias current path to ground.

The small-signal voltage gain is positive and less than unity. Neglecting body effect and output resistances, the follower gain is approximately

`Av ~= gm1 Rout_source / (1 + gm1 Rout_source)`

where `Rout_source` is the small-signal resistance seen from the source node into the bias device and load. The output resistance is low, on the order of `1/gm1` in parallel with the bias-device resistance.
