# Golden Solution - part1-009-common-gate-source-input

In Figure 6, `Vin` is applied to the source of `M1`, the gate is tied to a dc bias at `VDD` and is therefore ac-grounded, and the output is taken at the drain through `RD`.

This is a common-gate stage, not a common-source stage. Neglecting `ro`, the small-signal input resistance seen at the source is approximately

`Rin ~= 1/gm`.

The voltage gain from the source input to the drain output is non-inverting:

`Av ~= +gm RD`

or, including output resistance,

`Av ~= +gm (RD || ro)`.

The essential point is that the input terminal is the source. An analysis that treats `Vin` as a gate input gives the wrong topology and the wrong sign.
