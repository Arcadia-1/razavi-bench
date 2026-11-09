# Golden Solution - part1-011-many-poles-have

The circuit has two poles.

In Figure 8, `M1` is a common-source NMOS stage driven through `RS`, with load `RD`, and four capacitors: `CGS` from the gate to ground, `CGD` from the gate to the drain, `CDB` from the drain to ground, and `CSB` from the source to ground. Because the source is grounded, both terminals of `CSB` are at ground: it stores no energy and contributes nothing. `CGS`, `CGD` and `CDB` form a loop through ground, so only two of their three voltages are independent. The circuit therefore has two state variables and two poles; `CGD` also introduces a zero.

Razavi scores 3 ChatGPT's answer "There are two independent energy-storing nodes. Thus, the circuit has two poles," commenting that the answer is correct but that energy storage should be attributed to devices rather than to nodes.

Full-credit rule: give full credit for two poles with a justification that accounts for the capacitors themselves, for example by noting that `CSB` is shorted out because both its terminals are grounded, or that `CGS`, `CGD` and `CDB` form a capacitor loop so that only two capacitor voltages are independent, or by deriving a transfer function with a second-order denominator. An answer that gives two poles justified only by counting two energy-storing nodes, as ChatGPT did, earns 3 (Razavi's score). A bare "two" with no justification earns at most 3. A count other than two, or one pole per capacitor, earns at most 1.
