# Golden Solution - part1-015-malformed-cmos-inverter

Figure 11(b) has two NMOS devices, not a complementary CMOS pair. The upper device `M1`, with its drain at `VDD` and source at `Vout`, acts as a source-follower pull-up. The lower device `M2`, with its drain at `Vout` and source at ground, acts as a common-source pull-down. Both gates are driven by `Vin`.

For low `Vin`, both devices can be off and `Vout` is not actively driven. When they conduct, `M1` pulls up while `M2` pulls down, so `Vout` is set by their current balance. The circuit therefore does not provide the regenerative, rail-to-rail transfer characteristic of a CMOS inverter.
