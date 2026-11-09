# Golden Solution - part1-019-ensure-m2-saturation

Both transistors in Figure 14 are PMOS devices. `M2` has its source at `VDD`, its gate at `Vb2` and its drain at `X`; `M1` has its source at `X`, its gate at `Vb1` and its drain at the output. `M2` is in saturation if its source-drain voltage is at least its overdrive voltage:

`VDD - VX >= VDD - Vb2 - |VTH2|`, that is, `VX <= Vb2 + |VTH2|`.

The essential point, Razavi's, is that `VX` is set mainly by `Vb1`, not by `Vb2`. `M1` carries the current of `M2`, so `VX = Vb1 + |VGS1|`, and the saturation of `M2` becomes a condition on `Vb1`:

`Vb1 <= Vb2 + |VTH2| - |VGS1|`,

or, measured down from `VDD`, `VDD - Vb1 >= (|VGS2| - |VTH2|) + |VGS1|`. With equal thresholds this is `Vb2 - Vb1 >= |VGS1| - |VTH1|`, the overdrive of `M1`. Razavi writes the condition as `Vb1 < VGS2 - VTH2 + VGS1`; that form takes the PMOS quantities as positive and measures `Vb1` down from `VDD`, so it is the same condition.

Razavi scores 1 ChatGPT's answer, which treats `M2` as a PMOS device with its source at `VDD` and chooses `Vb2` so that `X` never rises above `Vb2 + VT2`, because it does not realize that `VX` is primarily controlled by `Vb1`.

Full-credit rule: give full credit if the answer treats both devices as PMOS, states the saturation condition of `M2`, and relates `VX` to `Vb1` (`VX = Vb1 + |VGS1|`) to give a condition on `Vb1` in any equivalent form: with absolute values, with signed PMOS quantities, referred to `VDD`, or as `Vb2 - Vb1` at least the overdrive of `M1`. Do not deduct for writing the condition in a form different from Razavi's printed one. An answer that writes `VX = Vb1 + |VGS1|` (or an equivalent relation) together with the saturation condition on `VX` has given the condition on `Vb1`, even if it does not combine the two into one inequality, and earns full credit. An answer that says only qualitatively that `Vb1` sets `VX`, without that relation or a condition on `Vb1`, earns 3. An answer that gives the condition only in terms of `VX` and `Vb2`, and treats `Vb2` as the control, earns 1 (Razavi's score). An answer that analyzes the devices as NMOS earns at most 1.
