# Golden Solution - part1-026-source-follower-drives-common-gate

Figure 20 can be viewed as a source follower `M1` driving a common-gate stage `M2`. The input is applied to the gate of `M1`; the source of `M1` drives the source of `M2`; the output is taken at the drain of `M2` through `RD`.

Thus the circuit is not a common-source amplifier with an NMOS cascode. The signal first appears as a source-follower voltage/current at the intermediate node and is then conveyed by the common-gate device to the output load.
