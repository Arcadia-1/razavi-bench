# Golden Solution - part2-005-determine-small-signal-resistance-seen-looking-into

The resistance seen looking into the supply node of the oscillating ring is set by the charging and discharging of the load capacitances, not by the static resistance of diode-connected inverter devices.

Here, `CL` is the effective load capacitance at each internal oscillator node, and `f0` is the oscillation frequency. In every cycle, each of the three nodes is charged from the supply and then discharged, so each node draws a charge of about `CL VDD` per period, like a switched-capacitor resistor of value `1/(f0 CL)`. The three nodes together give

`RX ~= 1 / (3 f0 CL)`.

Equivalently, from power: `P = 3 f0 CL VDD^2 = VDD IDD`, so `IDD = 3 f0 CL VDD` and, with `f0` held constant, `dIDD/dVDD = 3 f0 CL`.

This is Razavi's answer, and it treats `f0` as fixed. In a real ring, `f0` also rises with `VDD`, so the true incremental resistance is lower: if `f0` is taken as roughly proportional to `VDD`, then `IDD` is proportional to `VDD^2` and `RX ~= 1/(6 f0 CL)`. Answers that use the charging/discharging argument and then include the dependence of `f0` on `VDD`, for example giving `RX ~= 1/(6 f0 CL)`, are also correct.

Full-credit rule: give full credit to an answer that identifies the oscillation-driven charging and discharging of `CL`, or the equivalent power argument, as the mechanism and gives `RX ~= 1/(3 f0 CL)` or a result of the same form refined for the dependence of `f0` on `VDD`, such as `1/(6 f0 CL)`.

An answer that analyzes only the static, non-oscillating operating point and derives a `gm`-based resistance such as `(1/3)(1/gmn + 1/gmp)` or `2/(3 gm)`, from symmetry or diode-connected inverter intuition, ignores the oscillation and misses the dominant mechanism. Razavi scores exactly this answer 1, so such an answer should receive 1 if its static derivation is internally consistent. Mentioning the three inverters or the symmetry alone is only background.
