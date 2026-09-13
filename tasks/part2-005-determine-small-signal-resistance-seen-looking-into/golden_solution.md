# Golden Solution - part2-005-determine-small-signal-resistance-seen-looking-into

The resistance seen looking into the supply node of the oscillating ring is not simply the static resistance of diode-connected inverter devices. Oscillation matters because the supply current charges and discharges the three load capacitances each cycle.

Here, `CL` is the effective load capacitance at each internal oscillator node, and `f0` is the oscillation frequency. For a three-stage ring, the equivalent resistance is approximately

`RX ~= 1 / (3 f0 CL)`.

This can also be derived from power: `P = 3 f0 CL VDD^2 = VDD IDD`, so the incremental supply conductance is on the order of `3 f0 CL`.

A complete answer must identify the oscillation-driven dynamic charging/discharging mechanism and give `RX ~= 1/(3 f0 CL)` or an equivalent charge-per-cycle or power derivation.

An answer that analyzes the metastable/static small-signal operating point and derives a `gm`-based resistance such as `(1/3)(1/gmp + 1/gmn)` or `2/(3gm)` is analyzing a different, non-oscillating operating condition. Even if that static derivation is internally consistent, it misses the dominant mechanism.

Static small-signal models, symmetry, or diode-connected inverter intuition describe the wrong operating condition for this question. Such a `gm`-based answer may recognize the three-inverter topology or a possible static/metastable model, but it is not a partially correct derivation of the oscillating supply resistance.

Thus, mentioning the three inverters, symmetry, or a plausible static resistance only provides background. Without the dynamic `CL` charging/discharging or power argument and the `1/(3 f0 CL)` dependence, the answer has missed the point of the question.
