# Golden Solution - part1-007-pmos-common-source-source-degeneration

Figure 4 is a PMOS common-source stage with source degeneration. `M1` is a PMOS device: its source is connected to `VDD` through `RS`, its drain to ground through `RD`, the input is applied to the gate, and the output is taken at the drain.

For a small-signal analysis with `VDD` as ac ground, the source degeneration reduces the gain magnitude. Neglecting `ro` and body effect,

`Av = vout/vin ~= -gm RD / (1 + gm RS)`.

The stage inverts. With body effect (the source of `M1` sits below `VDD`, where its bulk is normally tied), the denominator becomes `1 + (gm + gmb) RS`.

Full-credit rule: give full credit if the answer identifies `M1` as a PMOS common-source stage with source degeneration and gives the inverting gain `-gm RD/(1 + gm RS)` or an equivalent form; including body effect or `ro` is a welcome refinement. An answer with this gain that never states the device type earns at most 3. An answer that misreads the topology, for example as a source follower, earns at most 1.
