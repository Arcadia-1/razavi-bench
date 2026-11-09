# Golden Solution - part1-004-sketch-ix-versus-vx

The transistor is a diode-connected NMOS device: its gate and drain are tied to `VX`, and its source is at ground. For `0 <= VX <= VTH`, the device is off and `IX` is approximately zero (only subthreshold current flows).

For `VX > VTH`, the device operates in saturation because `VDS = VGS = VX`, so

`IX ~= (1/2) mu_n Cox (W/L) (VX - VTH)^2`

ignoring channel-length modulation. The sketch is therefore zero up to threshold and then rises quadratically with `VX`.

Negative `VX` is outside the main point of the question. Below ground, the terminal at `VX` becomes the source and the gate is tied to it, so the channel stays off; with the bulk at ground, the drain-bulk junction conducts once `VX` falls below about `-0.6 V`. Mentioning this is correct but not required.

Deriving the square law, noting saturation, or adding channel-length modulation, subthreshold conduction, or junction conduction for negative `VX` is welcome and must not lower the score. An answer that puts the device in the triode region above threshold, gives a linear rise as the main result, or misreads the connections earns at most 2.
