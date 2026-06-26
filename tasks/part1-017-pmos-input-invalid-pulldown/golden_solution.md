# Golden Solution - part1-017-pmos-input-invalid-pulldown

Figure 13 has two PMOS devices, not a PMOS stacked on an NMOS. The input `Vin` is applied to the gate of the upper PMOS `M2`, and the output is the common node between `M2` and the lower PMOS `M1`.

The lower device `M1` has its gate and lower terminal tied to ground. With PMOS source-at-higher-potential convention, its source is the output node when `Vout` is high, and its gate/drain are effectively at ground. It is therefore a diode-connected PMOS load to ground, not a grounded-gate NMOS that is simply off.

The signal transconductance comes from `M2`: decreasing `Vin` turns `M2` on harder and raises `Vout`; increasing `Vin` weakens `M2` and lets the diode-connected PMOS load pull `Vout` lower. The topology is therefore a PMOS common-source stage with a diode-connected PMOS load, not the NMOS-pulldown interpretation.
