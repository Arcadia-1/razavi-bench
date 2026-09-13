# Golden Solution - part2-002-phase-noise-three-capacitors-doubled

Doubling all three load capacitors lowers the oscillation frequency by about a factor of two. For white-noise-induced phase noise in this ring oscillator, the relevant expression scales with `f0^2` while the other parameters are approximately independent of `CL`.

Therefore, when `CL` is doubled and `f0` is halved, the phase-noise spectral density drops by about a factor of four, i.e. about 6 dB.

A complete answer should state both the frequency scaling and the phase-noise result: doubling all three capacitors halves `f0`, and the white-noise-induced phase noise decreases by about 4x or 6 dB. Alternative edge-rate, energy, or delay-based explanations are acceptable only if they preserve this scaling. Saying the phase noise is unchanged or worsens contradicts the central result.
