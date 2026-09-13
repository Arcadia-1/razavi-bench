# Golden Solution - part1-006-device-act-as-current-source

No. The device is diode-connected, so it presents a low small-signal resistance of roughly `1/gm` rather than a high output resistance.

A good current source should maintain nearly constant current while its terminal voltage changes. Here the current is strongly set by the terminal voltage through the diode-connected MOSFET, so it behaves more like a nonlinear resistor/current-setting element than an ideal current source.
