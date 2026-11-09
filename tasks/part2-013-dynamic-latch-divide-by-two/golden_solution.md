# Golden Solution - part2-013-dynamic-latch-divide-by-two

Figure 12(a) is a divide-by-two circuit built from dynamic latches.

The clocked latches alternately sample and hold, so the output frequency is one half of the input clock frequency. Equivalently, the divided output completes one full cycle every two input clock periods. The dynamic nature means stored charge and leakage matter, but the intended function is a frequency divider by two.

Razavi scores 4 Gemini's answer "This is a divide-by-two circuit using dynamic latches."

Full-credit rule: an answer that correctly identifies the circuit as a divide-by-two built from dynamic latches (or a dynamic master-slave divider) earns full credit; explaining that alternate sampling/holding or feedback toggling produces an output at half the input clock frequency is welcome but not required.

The exact internal signal naming or inverter path is secondary if the divide-by-two function and dynamic-latch operation are correctly described.
