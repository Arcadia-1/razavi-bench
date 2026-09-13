# Golden Solution - part1-025-series-nmos-effective-long-channel

Figure 19 shows two series NMOS devices whose gates are tied together and
driven by the same input, with a resistive load at the top.

The essential answer is that the two devices behave approximately like one NMOS
with a longer effective channel. For equal widths,

`L_eff ≈ L1 + L2`.

Equivalently, for unequal widths,

`(W/L)_eff = 1 / (L1/W1 + L2/W2)`.

Award full credit for answers that identify the two series NMOS devices with
common gate drive and conclude that the effective channel length is
approximately the sum of the two channel lengths. It is acceptable to describe
the lower device as acting like a triode-region channel extension of the upper
device, or to call the overall stage a common-source amplifier with a resistive
load, as long as the longer-effective-channel conclusion is clear.

Do not give full credit to answers that classify the circuit as a cascode,
gain-boosted stage, differential half-circuit, diode-connected load, or
otherwise miss the longer-effective-channel mechanism.
