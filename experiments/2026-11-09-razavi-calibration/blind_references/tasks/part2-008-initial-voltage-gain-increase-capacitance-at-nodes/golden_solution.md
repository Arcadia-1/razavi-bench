# Golden Solution - part2-008-initial-voltage-gain-increase-capacitance-at-nodes

The initial voltage gain remains approximately unchanged.

The initial voltage gain is the gain accumulated across `P` and `Q` by the onset of regeneration, not the voltage difference at a fixed time. During the amplification phase the tail current discharges `P` and `Q`, and regeneration begins when their common-mode level has fallen by about `VTHN`, turning on `M3` and `M4`. A larger capacitance `CP` at each node slows this discharge, so the amplification phase lasts proportionally longer, about `2 CP VTHN/ICM`; the differential voltage builds as `gm1,2 Delta Vin t/CP` over that time. `CP` therefore cancels, and the gain is proportional to `gm1,2 VTHN/ICM`, Razavi's relation (5), which does not depend on the capacitance. Increasing the capacitance slows the comparator, but it does not change the initial gain.

A complete answer should state that increasing the capacitance at `P` and `Q` leaves the initial gain essentially unchanged; it mainly slows the transient. Either the independence of Razavi's gain expression from the capacitance or the cancellation argument above is a full justification; an answer that argues that the slower discharge lengthens the amplification phase in proportion is correct and must not be penalized. Secondary details of the phase sequence, such as exactly which devices turn on when regeneration starts, must not lower the score of an answer whose conclusion and capacitance argument are right. An answer that reaches "unchanged" through a wrong gain expression or mechanism earns 3.

If the answer says the initial gain increases because larger capacitance gives more integration time or a larger voltage difference, it contradicts the essential answer.

Likewise, saying the initial gain decreases because the larger capacitance slows the node voltage is also not the same as the initial-gain result. Larger capacitance changes the transient slope or delay, but the initial voltage gain in Razavi's expression is not a capacitance-set quantity.
