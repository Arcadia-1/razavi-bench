# Golden Solution - part2-019-add-ct-tail-node-as-phase-noise

Adding `CT` to the tail node has a nonmonotonic effect on phase noise.

For small or moderate `CT`, the tail-node waveform changes and the flicker noise of `M1` and `M2` can be upconverted to phase noise unless the devices follow an ideal square law. For a certain range of `CT`, the cross-coupled devices enter class-C-like switching and deliver peak tank currents larger than `ISS`, which can lower phase noise. In that mode the large currents can also push `M1` and `M2` into the triode region.

If `CT` becomes too large, the oscillator can exhibit low-frequency instability. Thus `CT` is an optimization variable, not a guaranteed phase-noise improvement.

Scoring tiers:

- 4: the effect is non-monotonic, with the class-C mechanism (peak tank currents larger than `ISS`) as the improvement and at least one of Razavi's degradations: flicker-noise upconversion of `M1` and `M2` at small `CT`, triode operation in the class-C regime, or low-frequency instability at large `CT`. Mentioning, in addition, that `CT` filters tail noise or ripple does not lower such an answer. - 3: the effect is non-monotonic, with one of Razavi's mechanisms on only one side, for example the class-C improvement with only a generic statement that too much capacitance hurts, or flicker-noise upconversion or instability with only a generic filtering improvement. - 2: the effect is non-monotonic or has an optimum, argued only generically, for example filtering versus excessive capacitance; or a monotonic degradation attributed to one of Razavi's mechanisms.
