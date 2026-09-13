# Golden Solution - part2-019-add-ct-tail-node-as-phase-noise

Adding `CT` to the tail node has a nonmonotonic effect on phase noise.

For small or moderate `CT`, the tail-node waveform changes and the flicker noise of `M1` and `M2` can be upconverted to phase noise unless the devices follow an ideal square law. For a certain range of `CT`, the cross-coupled devices enter class-C-like switching and deliver peak tank currents larger than `ISS`, which can lower phase noise. In that mode the large currents can also push `M1` and `M2` into the triode region.

If `CT` becomes too large, the oscillator can exhibit low-frequency instability. Thus `CT` is an optimization variable, not a guaranteed phase-noise improvement.

A complete answer should state that the effect of `CT` is not monotonic and must be optimized; it can improve phase noise in one range but can also worsen phase noise or cause instability in another range. The answer does not need to mention every supporting mechanism above.

An answer that gives only one side of the tradeoff, such as "`CT` improves phase noise by filtering the tail node" or "`CT` degrades phase noise by adding capacitance or noise conversion," is incomplete. A strictly monotonic conclusion misses the central point even if it contains a plausible mechanism.

Filtering tail-current ripple or noise is not by itself the Razavi answer. A useful answer must recognize that different `CT` ranges lead to different mechanisms: possible flicker-noise upconversion at small or moderate `CT`, possible class-C-like improvement in an intermediate range, and possible low-frequency instability when `CT` is too large. An "optimum" answer is only complete if it reflects this nonmonotonic mechanism rather than merely saying that more capacitance is eventually too much.
