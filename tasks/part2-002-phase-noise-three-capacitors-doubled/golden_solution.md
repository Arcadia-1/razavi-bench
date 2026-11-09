# Golden Solution - part2-002-phase-noise-three-capacitors-doubled

Doubling all three load capacitors lowers the oscillation frequency by about a factor of two. Razavi's expression for the phase noise due to white noise in this ring oscillator scales as `(f0/Delta f)^2`, multiplied by terms (device noise currents, bias current, supply voltage) that are approximately independent of `CL`.

Therefore, at a fixed offset frequency `Delta f`, doubling `CL` halves `f0` and lowers the phase-noise spectral density by about a factor of four, i.e. about 6 dB. At a fixed relative offset `Delta f/f0`, it is unchanged.

Razavi scores 4 Gemini's answer "The phase noise falls by a factor of four," which comes with an analysis based on the edge rate.

Full-credit rule: give full credit for a decrease of about a factor of four (6 dB) at a given offset frequency, supported either by the halving of `f0` or by an equivalent edge-rate, impulse-sensitivity, charge or delay argument that implies it; stating the frequency halving explicitly is not required if the argument implies it. A bare "6 dB" or "four times lower" with no justification earns 3. An answer that says only that the phase noise falls, without the magnitude, or that gives a wrong magnitude such as 3 dB, earns at most 2. An answer that says the phase noise is unchanged, other than explicitly at a fixed relative offset `Delta f/f0`, or that it worsens contradicts the central result and earns at most 1.
