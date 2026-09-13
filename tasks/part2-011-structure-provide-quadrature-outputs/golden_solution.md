# Golden Solution - part2-011-structure-provide-quadrature-outputs

The structure can provide nominal quadrature outputs in an ideal logic-timing
sense, but it does not guarantee accurate 90-degree quadrature in the actual
CMOS circuit.

Ideally, the two clocked latches behave like a divide-by-two. One latch output
updates on one clock phase and the other updates on the opposite clock phase.
Since the output period is twice the input clock period, a half-input-clock
delay corresponds to 90 degrees at the divided output frequency. In this
limited sense, nodes such as `X` and `Z` can be viewed as nominal quadrature
outputs.

The practical problem is that `Z` is not a direct latch output. It is obtained
from `Y` through `Inv3`, so the path `Y -> Inv3 -> Z` adds extra inverter delay.
Thus `Z` is skewed relative to the ideal latch timing.

The two latch outputs also do not see the same capacitance. The left latch
output `X` mainly drives the next latch input, while the right latch output `Y`
also drives `Inv3`. The input capacitance of `Inv3` is not just ordinary gate
capacitance: its gate-drain capacitance can be Miller-multiplied. This makes
the `Y`/`Z` path load heavier and different from the `X` path.

Because latch propagation delay depends on load capacitance, these unequal
loads and the extra `Inv3` delay introduce quadrature phase error. Therefore a
careful answer is: the circuit provides approximate or nominal quadrature, but
not exact or robust 90-degree quadrature unless the paths are carefully matched,
buffered, or calibrated.

A complete answer should say the structure is
nominally a quadrature divide-by-two but not an accurate/robust quadrature
generator, and identifies the two main nonidealities: the extra `Inv3` delay
from `Y` to `Z`, and unequal latch loading, especially the Miller-multiplied
capacitance of `Inv3`.

An answer that only explains the ideal half-clock-period spacing and says the
circuit provides quadrature outputs is incomplete because it misses the analog
delay and loading asymmetries. An answer that says simply "no quadrature"
without recognizing the nominal divide-by-two quadrature mechanism is also
incomplete.
