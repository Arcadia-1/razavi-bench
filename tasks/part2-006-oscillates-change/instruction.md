# part2-006-oscillates-change

## Question

For the ring oscillator in Figure 8, consider the small-signal resistance `RX`
seen looking into the supply node.

Use `CL` for the effective load capacitance at each internal oscillator node,
`f0` for the oscillation frequency, and `TD` for the delay of one inverter stage.

From the dynamic charging and discharging of the three load capacitances, one
can write

```text
RX ~= 1 / (3 f0 CL)
```

Somebody then argues that, because the circuit is oscillating, the path from
`VDD` to ground through the transistors is off for much of the cycle, so the
average resistance should be much higher than the MOS on-resistance or inverse
transconductance scale.

Do you agree with this argument?

## Figures

![Figure 8](figure-08.png)
