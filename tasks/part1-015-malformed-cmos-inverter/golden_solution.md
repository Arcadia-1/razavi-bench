# Golden Solution - part1-015-malformed-cmos-inverter

Figure 11(b) is not a proper CMOS inverter. The transistors are arranged with the wrong source/drain supply orientation for a normal complementary pull-up/pull-down inverter.

Although both gates are driven by `Vin`, the topology does not provide the standard PMOS pull-up to `VDD` and NMOS pull-down to ground. Instead, each device is effectively source-follower/pass-device-like over part of the swing: one side can pass a degraded high level and the other can pass a degraded low level, with threshold-voltage loss and body-effect dependence.

Thus the circuit may move `Vout` in response to `Vin`, but it does not regenerate logic levels, does not provide the usual inverting CMOS transfer characteristic, and is not a useful logic inverter topology.
