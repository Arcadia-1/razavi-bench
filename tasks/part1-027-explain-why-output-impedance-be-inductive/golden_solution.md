# Golden Solution - part1-027-explain-why-output-impedance-be-inductive

The output impedance can look inductive because the impedance seen at the output changes from one real resistance at low frequency to another at high frequency with a phase lead over the transition.

At very low frequency, `CGS1` is open and the output impedance is approximately `1/gm1`. At very high frequency, `CGS1` shorts the gate and source of `M1`, so the effective impedance approaches `RS`. The frequency-dependent transition caused by `CGS1` and `RS` can produce a positive imaginary component, equivalent to an inductive output impedance over a frequency range.
