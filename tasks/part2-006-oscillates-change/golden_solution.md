# Golden Solution - part2-006-oscillates-change

The static answer `RX ~= (1/3)(1/gmn + 1/gmp)` treats each inverter as two diode-connected devices, which an oscillating ring is not. Once the circuit oscillates, the supply current is set by the charging and discharging of the load capacitances: each of the three nodes draws a charge of about `CL VDD` per period, so

`RX ~= 1/(3 f0 CL)`,

where `CL` is the effective load capacitance at each internal oscillator node and `f0` is the oscillation frequency. The question does not name these quantities, so any symbols for them are equally correct.

The derivation changes, but the magnitude does not change much. Using `f0 = 1/(6 TD)` for a three-stage ring, where `TD` is the delay of one inverter stage, this can be written as

`RX ~= 2 TD / CL`.

Since `TD` is roughly `Req CL`, where `Req` is on the order of the MOS on-resistance and hence comparable to the inverse transconductances, `RX` is on the order of `Req`: not much higher than the static estimate. Oscillation does not make the supply resistance much higher merely because individual devices are off for part of the cycle.

Razavi scores 1 Gemini's answer "Yes, it does. The average resistance is now much higher because the path from VDD to ground through the transistors is off most of the time."

Full-credit rule: give full credit if the answer shows that, with oscillation, `RX` is set by the charging and discharging of the node capacitances (about `1/(3 f0 CL)` or an equivalent form, such as from the dynamic power `3 f0 CL VDD^2`) and that `RX` nonetheless stays on the order of the MOS on-resistance or inverse transconductance, not much higher than the static estimate. Razavi's route, writing `f0 = 1/(6 TD)` so that `RX ~= 2 TD/CL` and then `TD ~= Req CL`, is one way; any equivalent argument earns full credit, for example that `f0` is proportional to `1/(Req CL)` so that `RX = 1/(3 f0 CL)` is proportional to `Req`. An answer that also refines `RX` for the dependence of `f0` on `VDD`, for example to about `1/(6 f0 CL)`, reaches the same conclusion and is correct.

Partial credit:
- 3: the capacitive mechanism and the conclusion that `RX` stays on the order of `Req` or `1/gm`, with a minor error; or that conclusion with a sound argument other than the capacitive mechanism.
- 2: the capacitive result `RX ~= 1/(3 f0 CL)` or an equivalent, without comparing its magnitude with the static estimate or the on-resistance; or a statement that the static result still holds, without the capacitive mechanism.
- 1: an answer that agrees that `RX` becomes much higher, for example because the devices are off for much of the cycle (Razavi's score for Gemini); or one that says only that oscillation invalidates DC or small-signal analysis.
