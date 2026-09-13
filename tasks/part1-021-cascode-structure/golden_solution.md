# Golden Solution - part1-021-cascode-structure

No. Figure 16 is not a cascode in the usual sense because the lower device does not operate as a common-source input device feeding a common-gate cascode. Instead, `M1` acts as a source follower.

The output resistance is therefore not the usual cascode value `gm ro1 ro2`. Razavi gives the resistance as approximately

`Rout = (1 + gm2 ro2)/gm1 + ro2`.

The important distinction is the local source-follower action of `M1`, which changes the resistance transformation.
