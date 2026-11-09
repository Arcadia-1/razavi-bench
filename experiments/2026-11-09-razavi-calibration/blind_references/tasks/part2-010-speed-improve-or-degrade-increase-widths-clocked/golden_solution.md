# Golden Solution - part2-010-speed-improve-or-degrade-increase-widths-clocked

For the C2MOS divider in Figure 10, increasing the widths of the clocked transistors improves the speed initially.

In each latch, a clocked transistor sits in series with a data-driven transistor between each supply and the latch output (`X` or `Y`). Widening the clocked transistors lowers their own on-resistance, and with it the total resistance that charges and discharges `X` and `Y`. Their drain capacitance, which they add at `X` and `Y`, is at first small compared with the other capacitance at those nodes, so the delay falls. Beyond some width, the added capacitance in the data path becomes significant and the improvement levels off or reverses: there is an optimum width.

It is not a condition that an answer must state, and an answer need not discuss which devices are the bottleneck.

Full-credit rule: give full credit if the answer concludes that the speed improves initially, or up to an optimum width, because the clocked transistors' on-resistance falls, and recognizes that their added capacitance at the latch nodes eventually limits or reverses the benefit. An answer that concludes the speed improves, for the right reason, but never mentions the capacitance penalty or the optimum earns 3. An answer that says the speed improves at first, or for small widths, and then degrades past an optimum, but adds that the net effect for a given design depends on the actual sizes, has given this trend and earns full credit. Only an answer that gives no trend at all, for example "it depends on which effect dominates" without saying that widening helps at first, earns at most 2. An answer that misreads which transistors are clocked or how the latches are connected earns at most 1.
