# Golden Solution - part1-018-find-rout

Figure 14 is a PMOS cascode current source. Both transistors are PMOS: `M2` has its source at `VDD`, its gate at `Vb2` and its drain at `X`; `M1` has its source at `X`, its gate at `Vb1` and its drain at the output, where `Rout` is measured.

Here `M1`, not `M2`, is the common-gate cascode device seen from the output port. `M2` sets the bias current; `M1`, whose gate is held at `Vb1`, sets `VX = Vb1 + |VGS1|` and shields `X` from the output voltage.

The output resistance is

`Rout = ro1 + ro2 + (gm1 + gmb1) ro1 ro2`,

which is about `gm1 ro1 ro2` when `gm1 ro1 >> 1` and `gm1 ro2 >> 1`.

Full-credit rule: give full credit if the answer identifies both devices as PMOS with `M1` as the cascode device and gives `Rout ~= gm1 ro1 ro2` or the fuller expression; body effect is optional, and either statement of the approximation condition is acceptable. An answer that identifies `M1` as the cascode device and gives this result need not restate that both devices are PMOS; only an answer that analyzes them as NMOS devices is penalized for the device type. An answer that uses `gm2` as the cascode factor assigns the cascode role to the wrong transistor and earns at most 1.
