# Golden Solution - part1-019-ensure-m2-saturation

To keep `M2` in saturation, the drain-source voltage of `M2` must exceed its overdrive voltage. In the stack of Figure 14 this condition is controlled mainly by the intermediate node `X`, which is set by the lower bias `Vb1` and the current through `M1`.

The bias must leave enough voltage across `M2`. Razavi's condition can be expressed as choosing `Vb1` low enough that

`Vb1 < VGS2 - VTH2 + VGS1`

using the article's sign convention. The essential point is that saturation of the upper device is not set only by `Vb2`; it depends on the internal node voltage established by the lower device and bias.
