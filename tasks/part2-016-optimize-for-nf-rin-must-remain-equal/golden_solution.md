# Golden Solution - part2-016-optimize-for-nf-rin-must-remain-equal

The circuit should be optimized by using channel-length modulation and feedback together, not by simply making the load resistance as large as possible.

With `Rin` constrained to 50 ohm, the design variables must be chosen so that the input match is maintained while the noise contribution of the active devices and feedback network is minimized. Razavi notes that channel-length modulation changes the relation between `Rin` and noise factor, making it possible to obtain `NF < 1 + gamma`. Thus the optimum is not the limiting case of very large output resistance and `NF = 1 + gamma`; it requires finite output resistance/device sizing chosen jointly with `RF` and transconductance.

A complete answer must say that the 50-ohm input match must be preserved while jointly choosing `RF`, transconductance, and finite output resistance/channel-length modulation to minimize noise. It should recognize that the optimum can have `NF < 1 + gamma` and is not simply the large-`RF` or infinite-output-resistance limit.

An answer that only says to maximize `RF`, maximize gain/transconductance, or approach `NF = 1 + gamma` while keeping `Rin = 50 ohm` misses the key Razavi point, even if it describes the shunt-feedback input match correctly.

Identifying the circuit as a shunt-feedback LNA and writing an input-match relation such as `Rin ~= RF/(1 + |Av|)` is only background. It does not answer the optimization question unless the answer also explains how finite output resistance/channel-length modulation changes the noise-factor optimum. In particular, a recommendation to make `RF`, `gm`, loop gain, or output resistance as large as possible is the naive design direction that Razavi rejects.
