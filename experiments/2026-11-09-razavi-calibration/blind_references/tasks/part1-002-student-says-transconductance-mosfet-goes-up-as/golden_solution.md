# Golden Solution - part1-002-student-says-transconductance-mosfet-goes-up-as

Student A is correct for a given transistor, that is, with `W/L` fixed.

For a long-channel MOSFET in saturation,

`gm = mu Cox (W/L) Vov = 2 ID / Vov`.

With `W/L` fixed, raising `Vov` raises `ID` as `Vov^2`, so `gm = mu Cox (W/L) Vov` increases linearly with `Vov`. Reading `gm = 2 ID / Vov` as "gm falls as Vov rises" is wrong here, because the drain current of a given device does not stay constant when its overdrive increases.

Student B's claim holds only under a different condition: if `ID` is held fixed and `W/L` is reduced to raise `Vov`, then `gm = 2 ID / Vov` decreases.

A complete answer says that Student A is correct for a fixed device size and explains why. Noting that Student B would be right at fixed `ID` is welcome but not required. An answer that says Student B is correct, or that `gm` decreases with `Vov` without stating that `ID` is held fixed, misses the central point. An answer that contradicts itself, for example by assuming `Vov` is fixed while increasing it, is at most partially correct.
