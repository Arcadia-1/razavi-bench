# Golden Solution - part1-004-sketch-ix-versus-vx

The transistor is diode-connected with its gate and drain tied to `VX`, source at ground. For `VX <= VTH`, the device is off and `IX` is approximately zero.

For `VX > VTH`, the device operates in saturation because `VDS = VGS = VX`, so

`IX ~= (1/2) mu Cox (W/L) (VX - VTH)^2`

ignoring channel-length modulation. The sketch is therefore zero up to threshold and then rises quadratically with `VX`.
