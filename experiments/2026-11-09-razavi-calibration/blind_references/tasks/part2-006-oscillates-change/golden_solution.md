# Golden Solution - part2-006-oscillates-change

No. Oscillation does not make the effective supply resistance much higher than the MOS on-resistance or inverse-transconductance scale.

Here, `CL` is the effective load capacitance at each internal oscillator node, `f0` is the oscillation frequency, and `TD` is the delay of one inverter stage. From the dynamic-power result,

`RX ~= 1/(3 f0 CL)`.

Using `f0 = 1/(6 TD)` for a three-stage ring, this can also be written as

`RX ~= 2 TD / CL`.

Since the delay `TD` is roughly `Req CL`, this gives `RX` on the order of the MOS on-resistance or inverse transconductance. Thus the static diode-connected answer is not the correct derivation or primary expression, but the dynamic result is not much larger merely because individual devices are off for part of the cycle.

Full-credit rule: give full credit if the answer rejects the claim that oscillation makes `RX` much higher and shows that `RX` stays on the order of the MOS on-resistance or inverse transconductance. Razavi's route, writing `f0 = 1/(6 TD)` so that `RX ~= 2 TD/CL` and then `TD ~= Req CL`, is one way; any equivalent argument earns full credit, for example that `f0` is proportional to `1/(Req CL)` so that `RX = 1/(3 f0 CL)` is proportional to `Req`. An answer that also refines `RX` for the dependence of `f0` on `VDD`, for example to about `1/(6 f0 CL)`, reaches the same conclusion and is correct.

A generic statement that oscillation invalidates DC or small-signal analysis, without addressing whether `RX` becomes much higher, misses the question. An answer that says `RX` becomes much higher because the devices are off for much of the cycle repeats the specific misconception being tested.
