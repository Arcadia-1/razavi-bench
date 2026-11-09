# Golden Solution - part1-028-current-input-positive-feedback

Figure 22 is a current-input circuit with positive feedback. The input current is injected into node `X`, which drives the gate of `M1`. `M1` is a common-source device with load `RD1`, so an increase in `X` lowers `Vout`. The gate of `M2` is tied to `Vout`, not to its drain at `X`, so `M2` is not diode-connected: it is a common-source device that sinks current from `X` under the control of `Vout`.

The loop through `M1` and `M2` is positive: if `X` rises, `Vout` falls, `M2` sinks less current from `X`, and `X` rises further. With both devices in saturation, the loop gain is

`T = gm1 (RD1 || ro1) gm2 ro2`,

and the small-signal input resistance at `X` is

`Rin = ro2 / (1 - T)`, equivalently `Gin = 1/ro2 - gm1 gm2 (RD1 || ro1)`.

For the usual case `T > 1`, `Rin` is negative, about `-1/[gm1 gm2 (RD1 || ro1)]`, and small in magnitude; it is very large only when `T` is close to 1.

Because the input is a current source, a negative conductance at `X` makes this bias point unstable: with the node capacitances included, the circuit has a right-half-plane pole. The circuit therefore latches into one of two states. Either `X` falls, `M1` turns off, `Vout` goes to `VDD`, and `M2` enters the triode region and holds `X` low; or `X` rises, `Vout` falls, `M2` turns off, and the input current drives `X` up to the compliance limit of the source. It cannot operate as a linear amplifier unless the loop gain is kept below one.

Full-credit rule: give full credit if the answer recognizes that the gate of `M2` is tied to `Vout` (so `M2` is not diode-connected), identifies the positive-feedback loop through `M1` and `M2`, and states at least one correct consequence, such as a negative or loop-gain-modified input resistance, instability, or latching/bistable behavior. A precise `Rin` formula is not required. An answer that concludes the circuit latches, is bistable, or cannot hold a stable linear bias is correct and must not be penalized for it. Do not give full credit to an answer that treats `M2` as diode-connected or misses the feedback loop.
