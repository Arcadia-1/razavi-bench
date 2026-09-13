# Golden Solution - part1-002-student-says-transconductance-mosfet-goes-up-as

Both statements can be true, depending on what is held fixed.

For a long-channel MOSFET in saturation,

`gm = mu Cox (W/L) Vov = 2 ID / Vov`.

If `W/L` is fixed and `Vov` is increased, then `ID` rises as `Vov^2` and `gm` increases linearly with `Vov`; Student A is correct under this condition. If instead `ID` is fixed, then `gm = 2 ID / Vov`, so increasing `Vov` reduces `gm`; Student B is correct under this different condition.

The usual interpretation of the question is fixed device size, so increasing overdrive increases `gm`.
