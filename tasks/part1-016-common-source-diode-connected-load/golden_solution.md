# Golden Solution - part1-016-common-source-diode-connected-load

Figure 12 is a common-source NMOS stage with a diode-connected PMOS load. `M1` is the input transistor, with its gate at `Vin` and its source at ground; `M2` is a PMOS device with its source at `VDD` and its gate tied to its drain at `Vout`, providing a nonlinear active load.

The output is at the drain of `M1`, so the stage is inverting. Neglecting channel-length modulation for both devices,

`Av ~= -gm1/gm2`,

which for square-law devices is `-sqrt(mu_n (W/L)1 / (mu_p (W/L)2))`. Including channel-length modulation for both devices,

`Av ~= -gm1 (1/gm2 || ro1 || ro2)`.

Both forms are correct. Because the load is diode-connected, the gain is modest, set mainly by `gm1/gm2`.

Razavi scores 3 ChatGPT's answer "a common-source stage with a diode-connected load, Av = -gm1/(gm2 + 1/ro2)", commenting that it is correct but includes channel-length modulation for `M2` and not for `M1`.

Large-signal remarks are optional. With `M1` off, `Vout` rises toward `VDD - |VTHP|` and, through the subthreshold conduction of `M2`, slowly closer to `VDD`; do not penalize either statement.

Full-credit rule: give full credit if the answer identifies the common-source NMOS stage with a diode-connected PMOS load and gives an inverting gain of `-gm1/gm2`, `-gm1 (1/gm2 || ro1 || ro2)`, or an equivalent form that treats channel-length modulation consistently. An answer that includes `ro` for one device but not the other, as ChatGPT's did, earns 3. An answer that misreads `M2` as a current-source load or the device types earns at most 1.
