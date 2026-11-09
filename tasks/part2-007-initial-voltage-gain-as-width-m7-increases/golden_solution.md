# Golden Solution - part2-007-initial-voltage-gain-as-width-m7-increases

As the width of tail transistor `M7` increases, the initial voltage gain decreases.

The initial voltage gain is the gain that the input pair builds up across `P` and `Q` during the amplification (integration) phase, before the cross-coupled devices turn on and regeneration begins. A wider `M7` increases the tail current `ICM` that flows in that phase. In the StrongARM comparator relation cited by Razavi, the initial gain scales roughly like

`Av ~= gm1,2 VTHN / ICM`,

where `ICM` is the current through `M7`. Since `gm1,2` grows only as the square root of the current, increasing `M7` lowers the initial gain.

Razavi scores 4 Gemini's answer "As this width increases, the gain drops," which cites this relation and notes that `gm1,2` is proportional to the square root of `ICM`.

A complete answer should give the correct trend, namely that the initial gain decreases as `M7` becomes wider, together with a physically consistent explanation that a wider `M7` increases tail/common-mode current and the relevant gain factor such as `gm/ICM`, integration gain, or `gm/ID` decreases. The exact formula above is not required.

If the answer says the initial gain increases as `M7` width increases, it contradicts the essential answer even if some device-level discussion is present.
