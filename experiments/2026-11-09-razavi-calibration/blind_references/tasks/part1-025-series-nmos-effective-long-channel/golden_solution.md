# Golden Solution - part1-025-series-nmos-effective-long-channel

Figure 19 shows two series NMOS devices whose gates are tied together and driven by the same input, with a resistive load at the top. The source of `M2` is at `Vin - VGS2`, below `Vin - VTH`, so the lower device `M1` operates in the triode region while `M2` is saturated.

The essential answer is that the two devices behave approximately like one NMOS with a longer effective channel. For equal widths,

`L_eff ≈ L1 + L2`.

Equivalently, for unequal widths,

`(W/L)_eff = 1 / (L1/W1 + L2/W2)`.

Award full credit for answers that identify the two series NMOS devices with common gate drive and conclude that the effective channel length is approximately the sum of the two channel lengths. It is acceptable to describe the lower device as acting like a triode-region channel extension of the upper device, or to call the overall stage a common-source amplifier with a resistive load, as long as the longer-effective-channel conclusion is clear.

With `M1` in the triode region acting as a resistance `ron1` below `M2`, the output resistance is `ro2 + ron1 (1 + gm2 ro2)`, about `2 ro2` for identical devices: the `ro` of a single device of twice the length, since `lambda` scales as `1/L`. This modest increase, unlike a cascode's `gm ro` multiplication, is correct.

The names "self-cascode", "composite transistor" and "stacked transistor" are standard for this structure and are acceptable if the answer has `M1` in the triode region and reaches the longer-effective-channel conclusion.

Do not give full credit to answers that analyze the circuit as a true cascode with both devices saturated or with a cascode output resistance such as `gm2 ro1 ro2`, or as a gain-boosted stage, differential half-circuit or diode-connected load, or that otherwise miss the longer-effective-channel mechanism.
