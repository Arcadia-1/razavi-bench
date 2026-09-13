# Golden Solution - part2-008-initial-voltage-gain-increase-capacitance-at-nodes

The initial voltage gain remains approximately unchanged.

The initial gain expression depends mainly on the transconductance of the input pair and the common-mode/tail current, not directly on the capacitance at nodes `P` and `Q`. Increasing those capacitances slows the transient response, but it does not change the initial gain set by the device currents and transconductances.

A complete answer should state that increasing the capacitance at `P` and `Q` does not materially increase the initial gain; it mainly slows the transient or regeneration.

If the answer says the initial gain increases because larger capacitance gives more integration time or a larger voltage difference, it contradicts the essential answer.

Likewise, saying the initial gain decreases because the larger capacitance slows the node voltage is also not the same as the initial-gain result. Larger capacitance changes the transient slope or delay, but the initial voltage gain in Razavi's expression is not a capacitance-set quantity.
