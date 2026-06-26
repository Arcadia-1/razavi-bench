# Golden Solution - part1-024-many-poles-have

The circuit has two independent poles in the shown small-signal model.

One pole is associated with the input/gate-side node of `M1`, which contains `CGS` and the capacitance coupled through `CGD`. The other pole is associated with the output/drain-side node, which contains the drain-bulk capacitances and the capacitances connected to the cascode/output node.

The important point is to count independent dynamic nodes, not every capacitance label as a separate pole. In particular, a `CGS2`-style capacitance should not be invented as an output-node capacitance; the figure's terminal connections determine which node each capacitance loads.
