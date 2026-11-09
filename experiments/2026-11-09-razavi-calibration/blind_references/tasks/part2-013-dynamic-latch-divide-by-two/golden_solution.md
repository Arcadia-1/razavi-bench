# Golden Solution - part2-013-dynamic-latch-divide-by-two

Figure 12(a) is a divide-by-two circuit built from dynamic latches.

The clocked latches alternately sample and hold, so the output frequency is one half of the input clock frequency. Equivalently, the divided output completes one full cycle every two input clock periods. The dynamic nature means stored charge and leakage matter, but the intended function is a frequency divider by two.

A complete answer should identify the circuit as a dynamic-latch or master-slave divide-by-two circuit and explain that alternate sampling/holding or feedback toggling produces an output at half the input clock frequency.

The exact internal signal naming or inverter path is secondary if the divide-by-two function and dynamic-latch operation are correctly described.
