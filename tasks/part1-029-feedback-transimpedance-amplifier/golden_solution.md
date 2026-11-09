# Golden Solution - part1-029-feedback-transimpedance-amplifier

Figure 23 is a two-stage transimpedance amplifier with resistive feedback. `M1` is a common-gate NMOS input device: its gate is fixed at `Vb`, the input current `Iin` enters its source node, and its drain at `X` is loaded by `RD1`. Node `X` drives the gate of `M2`, a common-source second stage with load `RD2` whose drain is `Vout`. `RF` connects `Vout` back to the input (source) node; it returns a current, `iRF`, to that node.

The loop is negative (shunt-shunt) feedback. A positive `Iin` raises the input node, which reduces the current of `M1`; `X` rises, `M2` conducts more and `Vout` falls, so `RF` draws more current from the input node and opposes the original change. For high loop gain the transimpedance approaches `vout/iin ~= -RF`, and the input resistance is low: the open-loop input resistance divided by one plus the loop gain.

Razavi scores 2 ChatGPT's answer, which places the gate of `M1` at `X` and calls `M2` a common-source amplifier with a fixed gate bias `Vb`, commenting that ChatGPT is confused about the connections of `M1` and `M2` and that the latter statement is self-contradictory.

Full-credit rule: give full credit if the answer identifies `M1` as the common-gate input device (gate at `Vb`, input at its source), `M2` as a common-source stage driven by `X`, and `RF` as feedback from `Vout` to the input node, forming a current-to-voltage amplifier. The negative-feedback sign, the `-RF` transimpedance and the low input resistance are welcome but not required. An answer that calls the feedback positive contradicts the mechanism and earns at most 2. An answer that misreads the connections of `M1` or `M2`, as ChatGPT did, earns at most 2.
