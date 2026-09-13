# Golden Solution - part1-029-feedback-transimpedance-amplifier

Figure 23 is a feedback transimpedance-style amplifier. `M1` is a common-gate input device: its gate is fixed at `Vb`, the input current enters its source node, and its drain voltage appears at node `X` through `RD1`. Node `X` drives the gate of `M2`, which is a common-source second stage with load `RD2`.

The resistor `RF` returns a fraction of the output signal to the input/source node, so the input node, node `X`, and `Vout` are coupled by feedback. A positive input current produces a voltage at the input node, is conveyed by the common-gate device to `X`, is amplified by `M2`, and is fed back through `RF`.

The correct analysis is therefore a two-stage current-to-voltage amplifier with resistive feedback. `M2` is not a common-source amplifier with a fixed gate voltage; its gate is driven by node `X`.
