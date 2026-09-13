#!/usr/bin/env python3
"""Run standard Sky130 ngspice sanity-check examples."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from sky130_common import OUTPUT_DIR, parse_numeric_rows, render_template, run_ngspice


EXAMPLES = ("rc_tran", "rc_ac", "nmos_iv", "cs_ac", "current_mirror", "tgate_ron")


def _run(template: str, name: str, **kwargs: str) -> tuple[Path, Path, int]:
    netlist = render_template(template, OUTPUT_DIR / f"{name}.cir", **kwargs)
    log = OUTPUT_DIR / f"{name}.log"
    return netlist, log, run_ngspice(netlist, log)


def run_rc_tran() -> None:
    netlist, log, proc = _run(
        "tran_rc_charging",
        "tran_rc_charging",
        vin="1",
        r="10k",
        c="1p",
        tstep="0.05n",
        tstop="80n",
    )
    rows = parse_numeric_rows(log, min_cols=3)
    final_v = rows[-1][1] if rows else float("nan")
    print(f"rc_tran: exit={proc.returncode} final_v={final_v:.4g} netlist={netlist} log={log}")


def run_rc_ac() -> None:
    netlist, log, proc = _run(
        "ac_rc_filter",
        "ac_rc_filter",
        r="10k",
        c="1p",
        fstart="100k",
        fstop="10G",
    )
    print(f"rc_ac: exit={proc.returncode} expected_fc={1/(2*math.pi*10e3*1e-12):.4g}Hz netlist={netlist} log={log}")


def run_nmos_iv() -> None:
    for vgs in ("0.6", "0.9", "1.2"):
        name = f"dc_nmos_iv_vgs_{vgs.replace('.', 'p')}"
        netlist, log, proc = _run(
            "dc_nmos_iv",
            name,
            vgs=vgs,
            w="1.26u",
            l="0.15u",
            vds_stop="1.8",
            vds_step="0.02",
        )
        rows = parse_numeric_rows(log, min_cols=2)
        id_abs = abs(rows[-1][1]) if rows else float("nan")
        print(f"nmos_iv: vgs={vgs} exit={proc.returncode} id_at_1p8={id_abs:.4g}A netlist={netlist} log={log}")


def run_cs_ac() -> None:
    netlist, log, proc = _run(
        "ac_cs_amp",
        "ac_cs_amp",
        vdd="1.8",
        vgs_bias="0.9",
        rd="20k",
        w="1.26u",
        l="0.15u",
        cl="1p",
        fstart="1k",
        fstop="100G",
    )
    print(f"cs_ac: exit={proc.returncode} netlist={netlist} log={log}")


def run_current_mirror() -> None:
    netlist, log, proc = _run(
        "dc_current_mirror",
        "dc_current_mirror",
        vdd="1.8",
        iref="50u",
        w="2.0u",
        l="0.5u",
        vout_stop="1.8",
        vout_step="0.02",
    )
    print(f"current_mirror: exit={proc.returncode} netlist={netlist} log={log}")


def run_tgate_ron() -> None:
    netlist, log, proc = _run(
        "dc_tgate_ron",
        "dc_tgate_ron",
        vdd="1.8",
        vtest="0.01",
        wn="2.0u",
        wp="4.0u",
        l="0.15u",
        vstep="0.02",
    )
    rows = parse_numeric_rows(log, min_cols=2)
    current = abs(rows[len(rows) // 2][1]) if rows else float("nan")
    ron = 0.01 / current if current > 0 else float("nan")
    print(f"tgate_ron: exit={proc.returncode} mid_ron={ron:.4g}ohm netlist={netlist} log={log}")


RUNNERS = {
    "rc_tran": run_rc_tran,
    "rc_ac": run_rc_ac,
    "nmos_iv": run_nmos_iv,
    "cs_ac": run_cs_ac,
    "current_mirror": run_current_mirror,
    "tgate_ron": run_tgate_ron,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--example", choices=("all", *EXAMPLES), default="all")
    args = parser.parse_args()
    names = EXAMPLES if args.example == "all" else (args.example,)
    for name in names:
        RUNNERS[name]()


if __name__ == "__main__":
    main()
