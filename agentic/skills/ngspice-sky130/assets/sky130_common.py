#!/usr/bin/env python3
"""Small helpers for Razavi-Bench Sky130 ngspice probes."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path


ASSET_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = ASSET_DIR / "templates"
NETLIST_DIR = ASSET_DIR / "netlist"
OUTPUT_DIR = Path(os.environ.get("SKY130_NGSPICE_OUTPUT_DIR", Path.cwd() / "ngspice_outputs")).resolve()
LOG_DIR = OUTPUT_DIR
for _directory in (LOG_DIR, OUTPUT_DIR):
    _directory.mkdir(parents=True, exist_ok=True)


def find_ngspice_root() -> Path:
    env = os.environ.get("SKY130_NGSPICE_ROOT")
    if env:
        root = Path(env).resolve()
        if (root / "models" / "sky130.lib.spice").exists():
            return root

    candidates = [
        Path("/tools/ngspice-sky130"),
        Path.cwd(),
        *Path(__file__).resolve().parents,
    ]
    for candidate in candidates:
        if (candidate / "models" / "sky130.lib.spice").exists():
            return candidate
        checkout_models = candidate / "eval" / "ngspice-sky130"
        if (checkout_models / "models" / "sky130.lib.spice").exists():
            return checkout_models
    raise FileNotFoundError("could not find models/sky130.lib.spice")


def model_include() -> Path:
    return find_ngspice_root() / "models" / "sky130.lib.spice"


def check_ngspice() -> str:
    exe = shutil.which("ngspice")
    if not exe:
        raise FileNotFoundError("ngspice is not on PATH")
    return exe


def _template_path(template_name: str) -> Path:
    choices = [TEMPLATE_DIR / f"{template_name}.cir.tmpl", NETLIST_DIR / f"{template_name}.cir.tmpl"]
    for template in choices:
        if template.exists():
            return template
    names = sorted(
        path.name.removesuffix(".cir.tmpl")
        for root in (TEMPLATE_DIR, NETLIST_DIR)
        for path in root.glob("*.cir.tmpl")
    )
    raise FileNotFoundError(f"unknown template {template_name!r}; choices: {', '.join(names)}")


def render_template(template_name: str, output: Path, **kwargs: str) -> Path:
    template = _template_path(template_name)
    if not template.exists():
        raise FileNotFoundError(f"unknown template {template_name!r}")
    for key in ("w", "l", "wn", "wp"):
        value = kwargs.get(key)
        if value is not None and not re.fullmatch(r"[-+0-9.eE]+(?:m|u|n|p|f)", value, re.IGNORECASE):
            raise ValueError(f"{key} must carry an explicit SPICE unit suffix, got {value!r}")
    text = template.read_text(encoding="utf-8").format(
        sky130_lib=str(model_include()).replace("\\", "/"),
        **kwargs,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    return output


def run_ngspice(netlist: Path, log: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    check_ngspice()
    if log is None:
        log = netlist.with_suffix(".log")
    with log.open("w", encoding="utf-8", errors="replace") as fp:
        proc = subprocess.run(
            ["ngspice", "-b", str(netlist)],
            stdout=fp,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    return proc


def parse_prints(log: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    pattern = re.compile(r"^\s*([a-z_][A-Za-z0-9_()]*)\s*=\s*([-+0-9.eE]+)")
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            try:
                values[match.group(1)] = float(match.group(2))
            except ValueError:
                pass
    return values


def parse_numeric_rows(log: Path, min_cols: int = 2) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.strip().replace(",", " ").split()
        if len(parts) < min_cols + 1 or not parts[0].isdigit():
            continue
        try:
            rows.append([float(part) for part in parts[1:]])
        except ValueError:
            continue
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    netlist = render_template(args.template, args.out)
    log = netlist.with_suffix(".log")
    proc = run_ngspice(netlist, log)
    print(f"netlist: {netlist}")
    print(f"log: {log}")
    print(f"exit_code: {proc.returncode}")
    for key, value in sorted(parse_prints(log).items()):
        print(f"{key} = {value:.6g}")


if __name__ == "__main__":
    main()
