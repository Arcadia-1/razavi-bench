# Golden Solution - part1-024-many-poles-have

The circuit has two poles.

Figure 18 is a common-source NMOS stage, `M1`, driven through `RS`, with a PMOS current-source load, `M2`, whose source and gate are both at AC ground. There are two nodes with capacitance:

- the gate of `M1`, with `CGS` to ground;
- the output, with `CDB` (of `M1`) and `CDB2` to AC ground, and `CGD2`, which is also to AC ground because the gate of `M2` is at AC ground.

`CGD` (of `M1`) connects the two nodes. It does not add a third pole: `CGS`, `CGD` and `CDB` form a loop through ground, so only two of their voltages are independent. `CGD` couples the two nodes (the Miller effect) and adds a zero. There is no cascode device and no `CGS2` at the output.

Full-credit rule: give full credit for two poles with a correct justification: the two nodes (the gate of `M1` and the output) or two independent capacitor voltages, with the capacitors assigned to the right nodes. An answer need not list every capacitor or discuss how `CGD` loads each node. An answer that counts one pole per capacitor, or gives a number of poles other than two, earns at most 1.
