# Golden Solution - part1-015-malformed-cmos-inverter

Figure 11(b) has two NMOS devices, not a complementary CMOS pair. The upper device `M1`, with its drain at `VDD` and source at `Vout`, acts as a source-follower pull-up. The lower device `M2`, with its drain at `Vout` and source at ground, acts as a common-source pull-down. Both gates are driven by `Vin`.

For low `Vin`, both devices can be off and `Vout` is not actively driven. When the devices conduct, `M1` tries to raise `Vout` as a source follower while `M2` pulls `Vout` toward ground, so the output is set by current balance rather than by complementary pull-up/pull-down switching.

Thus this circuit is not a useful logic inverter and should not be treated as a standard analog gain stage. Its low-input state is floating or load-dependent, and its conducting-state output depends strongly on bias, sizing, body effect, and load. It does not provide the regenerative, rail-to-rail transfer characteristic of a CMOS inverter.
