# Golden Solution - part1-013-source-follower-current-source-load

Figure 10 is a source follower, not a common-source amplifier with an active load. `M1` is an NMOS device with its drain at `VDD`, its gate at `Vin` and its source at `Vout`; `M2`, an NMOS device biased by `Vb`, is a current source from `Vout` to ground that sets the bias current.

The small-signal voltage gain is positive and less than unity. With `R = ro1 || ro2`,

`Av = gm1 R / [1 + (gm1 + gmb1) R]`,

which is about `gm1/(gm1 + gmb1)`, slightly below one because of body effect, and tends to one with no body effect and an ideal current source. The output resistance is low: `Rout ~= (1/(gm1 + gmb1)) || ro1 || ro2`.

Full-credit rule: give full credit if the answer identifies `M1` as a source follower with `M2` as its current-source load and gives a positive gain at or slightly below one; an expression is welcome. Saying that the gain is about unity is correct in the ideal model. Including body effect or `ro` is a welcome refinement. An answer that calls the circuit a source follower but places the output elsewhere than the source of `M1`, or gives an inverting gain, is inconsistent with that identification and earns at most 2.
