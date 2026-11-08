# Golden Solution - part1-015-malformed-cmos-inverter

Figure 11(b) has two NMOS devices, not a complementary CMOS pair. The upper device `M1`, with its drain at `VDD` and source at `Vout`, acts as a source-follower pull-up. The lower device `M2`, with its drain at `Vout` and source at ground, is a pull-down whose gate is also driven by `Vin`.

The two devices act in opposite directions at the output, and the output is set by current balance. Because the source of `M1` sits at `Vout`, its overdrive is `Vin - Vout - VTH`, while that of `M2` is `Vin - VTH`. When both conduct, `Vout` settles below `Vin - VTH`, so `M2` operates in the triode region as a gate-controlled resistor. With square-law devices and no body effect or channel-length modulation, equating the two currents gives

`Vout ~= (Vin - VTH) [1 - sqrt(K2/(K1 + K2))]`,

where `K1` and `K2` are the devices' `(1/2) mu_n Cox W/L`. Once `Vin` exceeds `VTH`, the output therefore follows the input with a positive gain smaller than one: the circuit is a non-inverting attenuator, a source follower loaded by a triode device, not an inverter. Body effect and channel-length modulation change the gain somewhat but not its sign. For `Vin` below `VTH`, both devices are off and `Vout` is not driven.

Razavi's point is conceptual: a circuit whose two gates are tied to the input is not automatically a CMOS inverter, and this structure is not a useful one.

Scoring gate: the device-type identification is non-negotiable for this task. If an answer misidentifies either transistor type, assign 0. If an answer analyzes the circuit as a complementary push-pull stage or as an ordinary CMOS inverter, assign 0. Only answers that correctly identify both devices as NMOS may receive a nonzero score.

Full-credit rule: give full credit if the answer identifies both devices as NMOS, recognizes the upper source-follower and lower pull-down actions, and concludes that this is not a normal CMOS inverter. A gain formula, operating-region proof, or simulation is not required.
