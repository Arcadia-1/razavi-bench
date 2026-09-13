# Golden Solution - part1-024-many-poles-have

The circuit has two independent poles in the shown small-signal model.

One pole is associated with the input/gate-side node of `M1`, which contains `CGS` and the input-side effect of `CGD`. The other pole is associated with the output/cascode node, which contains `CDB`, `CDB2`, and the output-side effects of the capacitances connected across nodes.

The important point is to count independent dynamic nodes, not every capacitance label as a separate pole. In particular, `CGD` connects the input node to the output node, so through Miller equivalence it contributes on both sides; it should not be counted only as an input-node capacitance. Also, a `CGS2`-style output capacitance should not be invented if it is not present in the figure; the figure's terminal connections determine which node each capacitance loads.
