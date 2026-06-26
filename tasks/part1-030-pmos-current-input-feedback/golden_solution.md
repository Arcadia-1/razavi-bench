# Golden Solution - part1-030-pmos-current-input-feedback

Figure 24 is a current-input feedback circuit using PMOS devices. `M1` is not an NMOS cascode; it is a PMOS device biased by `Vb` and connected between the output node and the input/summing node. `M2` forms the upper feedback-controlled device connected to `VDD`.

The input current perturbs the left summing node. Through PMOS `M1`, this perturbation changes `Vout`; the resulting `Vout` variation drives the gate of PMOS `M2`, whose drain current feeds back into the input-side node. The loop is therefore `input/summing node -> M1 -> Vout -> M2 -> input/summing node`.

The key behavior is set by this two-node feedback loop and by the PMOS polarities, not by a simple NMOS cascode interpretation. A correct small-signal analysis should write KCL at the input/summing node and at `Vout`, include the transconductances of both PMOS devices, and solve the closed-loop transimpedance from `Iin` to `Vout`.
