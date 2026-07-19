# Golden Solution - part1-015-malformed-cmos-inverter

Figure 11(b) has two NMOS devices, not a complementary CMOS pair. The upper device `M1`, with its drain at `VDD` and source at `Vout`, acts as a source-follower pull-up. The lower device `M2`, with its drain at `Vout` and source at ground, acts as a common-source pull-down. Both gates are driven by `Vin`.

The two devices act in opposite directions at the output. As `Vin` rises, `M1` tends to raise `Vout`, while `M2` draws more pull-down current and tends to lower it. The output is therefore set by current balance. At a particular bias the two incremental effects may cancel, which is the qualitative connection to a zero-gain amplifier.

The circuit as drawn has no independent biasing to enforce that cancellation, so any zero-gain point is bias- and process-dependent. For low `Vin`, both devices can be off and `Vout` is determined by leakage and load. It is therefore neither a useful rail-to-rail logic inverter nor a robust zero-gain amplifier as drawn.

Scoring gate: the device-type identification is non-negotiable for this task. If an answer misidentifies either transistor type, assign 0. If an answer analyzes the circuit as a complementary push-pull stage or as an ordinary CMOS inverter, assign 0. Only answers that correctly identify both devices as NMOS may receive a nonzero score.

Full-credit rule: give full credit if the answer identifies both devices as NMOS, recognizes the upper source-follower and lower pull-down actions, and concludes that this is not a normal CMOS inverter. A gain formula, `gm`-matching derivation, operating-region proof, simulation, or explicit zero-gain observation is not required.
