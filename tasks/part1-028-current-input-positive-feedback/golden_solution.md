# Golden Solution - part1-028-current-input-positive-feedback

Figure 22 is a current-input circuit with positive feedback. The input current is injected into node `X`, which drives the gate of `M1`. `M1` is a common-source device with load `RD1`, so an increase in `X` lowers `Vout`. The gate of `M2` is tied to `Vout`, not to its drain at `X`.

This creates positive feedback at the input node: if `X` rises, `Vout` falls, the current pulled by `M2` from node `X` decreases, and `X` rises further. In small signal, the input conductance at `X` contains a negative feedback-created term, roughly of the form

`Gin ~= gds2 - gm1 gm2 RD1`

when `RD1` dominates the output load. Thus the input resistance can become very large or even negative if the loop gain is high. The circuit must therefore be analyzed as a feedback structure, not as a simple common-source device with a diode-connected load.
