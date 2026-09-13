# Golden Solution - part1-007-pmos-common-source-source-degeneration

Figure 4 is a PMOS common-source stage with source degeneration. The source is connected to `VDD` through `RS`, the drain is loaded by `RD`, the input is applied to the gate, and the output is taken at the drain.

For a small-signal analysis with `VDD` as ac ground, the gain magnitude is reduced by the source degeneration. Neglecting `ro`,

`Av = vout/vin ~= -gm RD / (1 + gm RS)`.

The stage inverts. The PMOS sign convention gives the same common-source inversion when expressed as `vout/vin`.
