# Golden Solution - part1-017-pmos-input-invalid-pulldown

Figure 13 has two PMOS devices, not a PMOS stacked on an NMOS. The input `Vin` is applied to the gate of the upper PMOS `M2`, and the output is the common node between `M2` and the lower PMOS `M1`.

The lower device `M1` has its gate and lower terminal tied to ground. With PMOS source-at-higher-potential convention, its source is the output node when `Vout` is high, and its gate/drain are effectively at ground. It is therefore a diode-connected PMOS load to ground, not a grounded-gate NMOS that is simply off.

The main mental model is a PMOS common-source input device with a diode-connected PMOS load. In small signal, `M2` supplies the input transconductance and the diode-connected `M1` supplies the load transconductance, so the voltage gain is approximately

```text
Av = vout/vin ~= -gm2/gm1
```

ignoring body effect and finite output resistance. Equivalently, this is a `gm/gm` amplifier. Decreasing `Vin` turns `M2` on harder and raises `Vout`; increasing `Vin` weakens `M2` and lets the diode-connected PMOS load pull `Vout` lower.

Full-credit rule: give full credit if the answer identifies both transistors as PMOS, recognizes `M2` as the common-source input device, recognizes `M1` as a diode-connected PMOS load with gate/drain tied to ground, and gives the `gm/gm` gain `Av ~= -gm2/gm1` or an equivalent current-balance explanation. It is acceptable to also mention that, from a logic-gate perspective, the lower PMOS is a poor pull-down and cannot pull `Vout` all the way to ground. Do not penalize that framing unless it replaces the diode-connected PMOS load interpretation with the wrong NMOS-off/floating-output interpretation.
