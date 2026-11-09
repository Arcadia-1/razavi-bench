# Golden Solution - part1-026-source-follower-drives-common-gate

Figure 20 is a source-coupled pair with the gate of `M2` held at `Vb`. `M1` (gate at `Vin`, drain at `VDD`) and `M2` (drain at `Vout` through `RD`) share a source node, biased by the current source `I1`, so `ID1 + ID2 = I1`. Razavi views it as a source follower, `M1`, driving a common-gate stage, `M2`: the input is applied to the gate of `M1`, the source of `M1` drives the source of `M2`, and the output is taken at the drain of `M2`. It is equally valid to view it as a differential pair with one input at AC ground and a single-ended output.

The circuit is not a common-source amplifier with an NMOS cascode. Neglecting `ro` and body effect, the small-signal voltage at the shared source is `gm1/(gm1 + gm2) vin`, about `vin/2` for matched devices, and the gain is non-inverting:

`Av = gm1 gm2 RD / (gm1 + gm2)`, about `gm RD/2` for matched devices.

Full-credit rule: give full credit if the answer identifies the circuit either as a source follower driving a common-gate stage or as a source-coupled differential pair with the gate of `M2` at `Vb` and the output at the drain of `M2`. The gain expression and its non-inverting sign are welcome but not required; an answer that gives an inverting gain contradicts the signal path and earns at most 3.
