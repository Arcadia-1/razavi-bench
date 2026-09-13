# Golden Solution - part1-016-common-source-diode-connected-load

Figure 12 is a common-source NMOS stage with a diode-connected PMOS load. `M1` is the input transistor and `M2` is diode-connected to `VDD`, providing a nonlinear active load.

The output is at the drain of `M1`, so the stage is inverting. The small-signal load resistance of the diode-connected PMOS is approximately `1/gm2 || ro2`, and the gain is roughly

`Av ~= -gm1 (ro1 || ro2 || 1/gm2)`.

Because the load is diode-connected, the gain is typically modest.
