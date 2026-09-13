# Golden Solution - part2-009-increase-widths-m5-and-m6-speed-improve

Increasing the widths of `M5` and `M6` initially improves speed.

`M5` and `M6` are the cross-coupled PMOS regenerative devices. Making them wider increases their transconductance and pull-up/regenerative strength, so the latch regeneration becomes faster. Although their parasitic capacitances at nodes `X` and `Y` also increase, those added capacitances are not initially the dominant capacitances at `X` and `Y`; other device and wiring capacitances dominate first. Therefore, the stronger regenerative action wins over a useful initial sizing range.

The improvement is not unlimited. Once the parasitic capacitance of `M5` and `M6` becomes a significant part of the node capacitance, further widening gives diminishing returns and can eventually degrade speed. Thus the correct design conclusion is: speed improves initially, up to an optimum width.

A complete answer should state that speed initially improves, or improves up to an optimum, and explain that wider `M5`/`M6` strengthen regeneration or pull-up action while added capacitance eventually limits the benefit. The answer need not explicitly say that other capacitances at `X` and `Y` dominate initially if it clearly states that the regeneration benefit dominates over added capacitance in the initial range.

If the answer's final conclusion is that speed degrades because wider `M5`/`M6` add parasitic capacitance, it has identified a real limiting mechanism but gets the initial trend and design conclusion wrong.

An answer that says widening always improves speed with no capacitance or optimum-width caveat is mostly correct on the initial trend but incomplete, because it misses the sizing limit.
