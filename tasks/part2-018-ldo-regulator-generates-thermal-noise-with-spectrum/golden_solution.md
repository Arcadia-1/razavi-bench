# Golden Solution - part2-018-ldo-regulator-generates-thermal-noise-with-spectrum

The LDO output noise modulates the VCO frequency through the supply-pushing gain. First determine the pushing gain

`Kpush = d fosc / d Vout`

usually by simulation or perturbation analysis. Then convert the LDO noise spectrum `Sth` to phase noise through frequency modulation. In the notation of the article, the single-sideband phase noise is proportional to

`L(Delta f) ~= 10 log10( Kpush^2 Sth / (2 Delta f^2) )`.

Because the supply perturbation appears directly on the varactors in this circuit, `Kpush` is closely related to `KVCO`. A design with lower `KVCO` also reduces this supply-noise-to-phase-noise conversion.

A complete answer should identify supply pushing, use `Kpush` or an equivalent `df/dVout` sensitivity to convert the LDO noise to frequency noise, and then apply FM-to-PM conversion with a `1/Delta f^2` dependence. It should also note the design insight from this circuit: the supply perturbation appears directly on the varactors, so `Kpush` is closely related to `KVCO` and reducing `KVCO` reduces this noise conversion.

Exact factors of `2`, `2pi`, log notation, or whether the spectrum is written as phase-noise density versus single-sideband phase noise are secondary if the proportionality is correct.
