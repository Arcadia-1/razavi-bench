# Golden Solution - part1-027-explain-why-output-impedance-be-inductive

In Figure 21, `M1` is a source follower: its gate is driven from `Vin` through `RS`, its drain is at `VDD`, and its source is the output. `M2`, biased by `Vb`, is a current source to ground. For the output impedance, `Vin` is at AC ground. Looking into the source of `M1`, and neglecting `ro`, body effect and other capacitances,

`Zout = (1 + s RS CGS1) / (gm1 + s CGS1)`.

At very low frequencies `CGS1` is open and `Zout ~= 1/gm1`. At very high frequencies `CGS1` shorts the gate to the source, so `Zout ~= RS`. If `RS > 1/gm1`, the zero at `1/(RS CGS1)` comes before the pole at `gm1/CGS1`, so the impedance rises with frequency: over that range it behaves as `1/gm1` in series with an inductance of about `CGS1 (RS - 1/gm1)/gm1`. If `RS < 1/gm1`, the impedance falls with frequency and is capacitive instead.

His comment gives the intuition: `Zout` is equal to `1/gm1` at very low frequencies and `RS` at very high frequencies, as `CGS1` shorts the gate and the source.

Full-credit rule: give full credit if the answer explains that `Zout` moves from about `1/gm1` at low frequencies to about `RS` at high frequencies because `CGS1` shorts the gate and source, so that it rises with frequency, that is, is inductive, when `RS > 1/gm1`; the `Zout` expression is welcome. An answer that gives this transition and concludes that `Zout` rises with frequency earns full credit even if it does not state `RS > 1/gm1` explicitly. An answer that requires `RS < 1/gm1` for inductive behavior contradicts the mechanism and earns at most 2.
