# Golden Solution - part2-010-speed-improve-or-degrade-increase-widths-clocked

For the C2MOS divider in Figure 10, increasing the widths of the clocked transistors can improve speed initially.

If the data-driven devices are the bottleneck, stronger clocked devices reduce their on-resistance and help the latch transfer data faster. These wider clocked devices also add capacitance in the data path, so the improvement is not unlimited; after some point the added capacitance can offset the resistance reduction.

A complete answer should capture the tradeoff: larger clocked devices can initially improve speed by lowering the clocked-device resistance, but the added capacitance eventually limits or can reverse the benefit. It is fine to describe this as an optimum sizing problem.

An answer that discusses only the added-capacitance penalty and concludes that speed always degrades misses the initial-resistance benefit. An answer that discusses only resistance improvement and misses the capacitance penalty is also incomplete.

Identifying the clocked transistors and their added capacitance is only part of the answer. The key design conclusion is the initial speed improvement when the data-driven devices are the bottleneck. If the final conclusion is that speed generally or always degrades, the answer has missed Razavi's main point even if it mentions a real capacitance penalty.
