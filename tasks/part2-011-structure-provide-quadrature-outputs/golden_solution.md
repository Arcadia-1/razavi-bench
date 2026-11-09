# Golden Solution - part2-011-structure-provide-quadrature-outputs

Nominally yes, but not accurately.

Figure 10 is a C2MOS divide-by-two. The left latch takes `Z` as its data input and produces `X`; the right latch takes `X` and, clocked on the opposite phase, produces `Y`; `Inv3` inverts `Y` to give `Z`, which closes the loop. Each node toggles at half the clock frequency, and the two latches change state on opposite clock edges, half an input clock period apart, which is 90 degrees at the output frequency. Ideally, therefore, `X` and `Y` are in quadrature, and `Z`, the inverse of `Y`, is also nominally in quadrature with `X`.

Razavi scores 2 Gemini's answer "Yes, it does. The output at Y or Z is in quadrature with respect to that at X", and names two departures from exact quadrature:

- the delay through `Inv3` causes a skew in `Z`;
- it is difficult to ensure equal load capacitances seen by the two latches. `X` drives the data transistors of the second latch, whereas `Y` drives `Inv3`; for example, the gate-drain capacitances within `Inv3` experience Miller multiplication, but those within the second latch do not. Unequal loads give unequal latch delays, so even `X` and `Y` are not exactly 90 degrees apart.

Full-credit rule: give full credit if the answer says the circuit provides nominal or approximate quadrature (a divide-by-two whose two latches switch half an input period apart) and explains why it is not exact, giving both the `Inv3` delay that skews `Z` and the unequal loading of the two latches. Miller multiplication within `Inv3` is Razavi's example of the unequal loading, not a separate requirement; any correct account of the load mismatch between the two latch outputs is sufficient. Naming `X` and `Y`, or `X` and `Z`, as the nominal quadrature pair is acceptable. A headline "yes" followed by these caveats is acceptable.

An answer that gives the nominal quadrature and only one of the two departures earns 3. An answer that says "yes" with only the ideal half-period argument earns 2 (Razavi's score for Gemini). An answer that says "no" because of a real asymmetry, without recognizing the nominal divide-by-two quadrature, earns 2; one that says "no" for a wrong reason earns at most 1.
