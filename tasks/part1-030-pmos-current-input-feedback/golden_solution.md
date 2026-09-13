# Golden Solution - part1-030-pmos-current-input-feedback

Figure 24 is a current-input feedback circuit using a common-gate NMOS input device and a PMOS feedback device. `M1` is an NMOS biased by `Vb`, with its source connected to the input/summing node and its drain connected to `Vout`. `M2` is the upper PMOS device connected to `VDD`, with its gate driven by `Vout` and its drain connected to the input/summing node.

The main signal path is `Iin -> input/summing node -> M1 -> Vout`: the input current perturbs the source of the common-gate NMOS `M1`, and this perturbation is transferred to the output node. The resulting `Vout` variation drives the gate of PMOS `M2`, whose drain current feeds back into the input-side node. The feedback loop is therefore `input/summing node -> M1 -> Vout -> M2 -> input/summing node`. Equivalently, this can be viewed as a current buffer or as a shunt-shunt transimpedance feedback stage.

The key behavior is set by this two-node current-feedback loop, not by a two-PMOS interpretation. The input resistance is very low, approximately

```text
Rin ~= 1/(gm1 gm2 ro1)
```

under the usual high-gain assumptions, and the closed-loop transimpedance and output resistance are on the order of

```text
vout/iin ~= 1/gm2
Rout ~= 1/gm2
```

up to sign convention and finite-output-resistance corrections. With ideal bias current sources treated as small-signal open circuits, it is acceptable to write the `Vout`-node KCL as zero small-signal current through `M1`,

```text
-gm1 vx + (vout - vx)/ro1 = 0
```

which gives `vout = (1 + gm1 ro1) vx`; this is a valid route to the low input-resistance result.

Full-credit rule: give full credit if the answer identifies `M1` as the common-gate NMOS input device, identifies `M2` as the PMOS feedback device driven by `Vout`, describes the feedback path back to the input node, and states that the circuit has very low input resistance with `vout/iin ~= 1/gm2`, `Rout ~= 1/gm2`, or an equivalent current-buffer/transimpedance interpretation. Calling the circuit a current buffer, current-input feedback stage, or shunt-shunt transimpedance amplifier is acceptable.

Zero-credit rule: if the answer explicitly analyzes `M1` as a PMOS device, for example by saying both transistors are PMOS or by using PMOS source-gate behavior for `M1`, assign score 0 unless it is clearly an isolated typo and the rest of the analysis unambiguously treats `M1` as an NMOS common-gate transistor.
