# Golden Solution - part1-005-sketch-ix-versus-vx

In Figure 2, `VX` is applied to the gate, the source is grounded, and the drain is held at `1 V`. Thus `VGS = VX` and `VDS = 1 V`.

For `VX <= VTH`, the transistor is off and `IX ~= 0`.

For `VTH < VX < VTH + 1 V`, the condition `VDS >= VGS - VTH` is satisfied, so the device is in saturation and

`IX ~= (1/2) mu_n Cox (W/L) (VX - VTH)^2`

ignoring channel-length modulation.

For `VX >= VTH + 1 V`, the device enters the triode region because `VDS = 1 V < VGS - VTH`. The current is then

`IX ~= mu_n Cox (W/L) [(VX - VTH)(1 V) - (1/2)(1 V)^2]`.

So the sketch is zero below threshold, then quadratic in saturation, then roughly linear in `VX` after the drain-to-source voltage limits the device to the triode region.
