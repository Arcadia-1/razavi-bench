# Golden Solution - part1-014-cmos-inverter

Figure 11(a) is the standard CMOS inverter. `M2` is a PMOS device with its source at `VDD`, and `M1` is an NMOS device with its source at ground; both gates are tied to `Vin` and both drains to `Vout`. A low input turns `M2` on and pulls `Vout` up to `VDD`; a high input turns `M1` on and pulls `Vout` down to ground. At either logic level one device is off, so no static current flows.

Razavi scores ChatGPT's answer "This is the classic CMOS inverter" 4, commenting that it shows ChatGPT recognizes both the NMOS and the PMOS symbols. Recognizing the CMOS inverter with its complementary devices is therefore the complete answer.

Further analysis is optional. Biased near its switching point, where both devices are saturated, the inverter is a high-gain inverting amplifier with `Av ~= -(gmn + gmp)(ron || rop)`; its transfer curve, switching threshold, and the current that flows during a transition are also correct supplements.

Full-credit rule: give full credit if the answer identifies the circuit as a CMOS inverter with an NMOS pull-down and a PMOS pull-up (or otherwise shows that it reads one NMOS and one PMOS device correctly). Omitting the small-signal gain, the transfer curve, or any other analog analysis must not lower the score. Statements that one device is off and no static current flows at the logic levels are correct. Deduct only for errors that contradict the inverter's operation, such as a non-inverting gain. An answer that misreads the device types, for example as two NMOS devices, earns at most 1.
