# Golden Solution - part1-011-many-poles-have

The circuit has two poles in the usual small-signal model.

The capacitors are connected among two independent dynamic nodes: the input/gate-side node and the output/drain-side node. `CGD` couples these two nodes, but it does not by itself create a third independent node.

Thus the number of poles is two. More precisely, the count should be based on independent energy-storage state variables, not simply on the number of capacitors drawn.
