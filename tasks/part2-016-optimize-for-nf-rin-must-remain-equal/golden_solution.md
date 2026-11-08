# Golden Solution - part2-016-optimize-for-nf-rin-must-remain-equal

Figure 13 is a resistive-feedback (shunt-feedback) inverter LNA: `M1` and `M2` form a CMOS inverter, `RF` connects its output to its input, and the source `Rs` drives the input through `C1`. With total transconductance `gm = gm1 + gm2` and output resistance `ro = ro1 || ro2` from channel-length modulation, the input resistance is

`Rin = (RF + ro) / (1 + gm ro)`.

If `ro` is made very large while `RF` stays finite, `Rin` approaches `1/gm`. The match then forces `gm = 1/Rs`, and the noise factor can at best approach `F = 1 + gamma` as `RF` grows. This is the answer Razavi rejects: raising the output resistance only approaches the lower bound `NF = 1 + gamma`.

With finite `ro`, channel-length modulation changes the relation between `Rin` and the noise factor. `Rin = 50 ohm` is kept by choosing `RF = Rs (1 + gm ro) - ro`, while `gm` is raised above `1/Rs`. The noise factor then falls below `1 + gamma`, and it keeps falling as `gm` increases; for a large intrinsic gain `gm ro`, it approaches `F ~= 1 + gamma/(gm Rs)`. The optimization is therefore to raise `gm` (device width and bias current) above `1/Rs` and to raise `RF` with it so that `Rin` stays at 50 ohm, at the cost of power and input capacitance. Lowering `ro` on purpose is not what helps: at a fixed `gm`, a larger `gm ro`, with `RF` re-chosen for the match, gives a lower NF. What limits the NF to `1 + gamma` is pinning `gm` at `1/Rs`.

Full-credit rule: give full credit to an answer that keeps `Rin = 50 ohm` through a relation that includes the finite output resistance, for example `Rin = (RF + ro)/(1 + gm ro)` or `(RF + RL)/(1 + gm RL)`, and explains that `gm` can then exceed `1/Rs`, with `RF` adjusted to hold the match, so that the NF can fall below `1 + gamma`. A recommendation to increase `gm` and `RF` together while maintaining the match is correct and must not be penalized.

An answer that assumes `Rin ~= 1/gm`, so that `gm` is fixed at `1/Rs`, and gives `NF -> 1 + gamma` as the best achievable value misses Razavi's point; Razavi scores that answer 1. Identifying the circuit as a shunt-feedback LNA and writing `Rin ~= RF/(1 + |Av|)` is only background unless the answer also explains how the finite output resistance lets the NF fall below `1 + gamma`.
