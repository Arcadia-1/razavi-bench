# Golden Solution - part1-018-find-rout

Figure 14 is a PMOS current-source stack, and the output resistance is measured looking into the drain of the lower device `M1`.

Here `M1`, not `M2`, is the common-gate/cascode device seen from the output port. The upper PMOS `M2` sets the bias current and the intermediate node `X`; the lower PMOS `M1` shields that node from output-voltage variations.

To first order, the cascoded output resistance is

`Rout ~= ro1 + ro2 + gm1 ro1 ro2`.

If `gm1 ro1 >> 1`, this is approximately

`Rout ~= gm1 ro1 ro2`.

Using `gm2` as the cascode gain factor corresponds to assigning the cascode role to the wrong transistor.
