#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


NETLISTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = NETLISTS_ROOT.parent
SIMULATOR_ROOT = REPO_ROOT / "simulator"
GROUP_NAME = re.compile(r"part[12]-figure-\d+-[0-9a-f]{8}$")
BENIGN_MODEL_PLACEHOLDER = re.compile(r"<<NAN,\s*error\s*=\s*\d+>>", re.IGNORECASE)
ERROR_LINE = re.compile(r"(^|\s)(fatal|error)(:|\s)", re.IGNORECASE)
SKY130_MODEL = re.compile(r"\bsky130_fd_pr__", re.IGNORECASE)
INSTANCE = re.compile(r"^\s*x\S+", re.IGNORECASE)
GEOMETRY_VALUE = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:meg|mil|[fpnumkgt])$",
    re.IGNORECASE,
)
FORBIDDEN_REFERENCE = re.compile(r"/home/|agentic/simulator|razavi-bench-vela")


def sky130_geometry_errors(deck: Path, text: str) -> list[str]:
    errors: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.split(";", 1)[0]
        if not INSTANCE.search(line) or not SKY130_MODEL.search(line):
            continue
        for key in ("w", "l"):
            match = re.search(rf"\b{key}\s*=\s*([^\s]+)", line, re.IGNORECASE)
            if not match or not GEOMETRY_VALUE.fullmatch(match.group(1)):
                value = match.group(1) if match else "<missing>"
                example = "1.26u" if key == "w" else "0.15u"
                errors.append(
                    f"{deck.name}:{line_number}: Sky130 {key.upper()} must be a direct "
                    f"numeric value with an explicit SPICE suffix (for example "
                    f"{key}={example}); got {value}"
                )
    return errors


def source_errors(deck: Path) -> list[str]:
    text = deck.read_text(encoding="utf-8", errors="replace")
    errors = sky130_geometry_errors(deck, text)
    if FORBIDDEN_REFERENCE.search(text):
        errors.append(f"{deck.name}: contains a private or obsolete path")

    figure_number = int(deck.parent.name.split("-")[2])
    header = "\n".join(text.splitlines()[:20]).lower()
    if deck.parent.name.lower() not in header and not re.search(
        rf"\bfigure[- ]?0*{figure_number}\b", header
    ):
        errors.append(f"{deck.name}: first 20 lines do not identify the source figure")
    return errors


def run_deck(deck: Path, temp_root: Path, timeout: int) -> dict[str, Any]:
    temp_group = temp_root / "netlists" / deck.parent.name
    temp_group.mkdir(parents=True, exist_ok=True)
    temp_deck = temp_group / deck.name
    shutil.copy2(deck, temp_deck)
    log_path = temp_root / "logs" / deck.parent.name / f"{deck.stem}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        process = subprocess.run(
            ["ngspice", "-b", "-o", str(log_path), temp_deck.name],
            cwd=temp_group,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"path": deck.name, "timeout": timeout}

    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    fatal_lines = [
        line.strip()
        for line in log.splitlines()
        if ERROR_LINE.search(line) and not BENIGN_MODEL_PLACEHOLDER.search(line)
    ]
    return {
        "path": deck.name,
        "returncode": process.returncode,
        "fatal_lines": fatal_lines[:20],
    }


def validate_group(group: Path, temp_root: Path, timeout: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "group": group.name,
        "passed": False,
        "decks": [],
        "errors": [],
    }
    decks = sorted(group.glob("*.cir"))
    unexpected = sorted(path.name for path in group.iterdir() if not path.is_file() or path.suffix != ".cir")
    if unexpected:
        result["errors"].append(f"only top-level .cir files are allowed: {unexpected}")
    if not decks:
        result["errors"].append("group contains no .cir decks")

    for deck in decks:
        result["errors"].extend(source_errors(deck))
        deck_result = run_deck(deck, temp_root, timeout)
        if deck_result.get("timeout"):
            result["errors"].append(f"{deck.name}: timed out after {timeout}s")
        elif deck_result.get("returncode") != 0 or deck_result.get("fatal_lines"):
            result["errors"].append(f"{deck.name}: ngspice validation failed")
        result["decks"].append(deck_result)

    result["passed"] = not result["errors"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate curated Razavi-Bench SPICE netlists")
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if not shutil.which("ngspice"):
        raise SystemExit("ngspice is not installed or is not on PATH")
    if not SIMULATOR_ROOT.is_dir():
        raise SystemExit(f"missing simulator assets: {SIMULATOR_ROOT}")

    groups = sorted(
        path for path in NETLISTS_ROOT.iterdir() if path.is_dir() and GROUP_NAME.fullmatch(path.name)
    )
    if args.group:
        requested = set(args.group)
        groups = [group for group in groups if group.name in requested]
        missing = requested - {group.name for group in groups}
        if missing:
            raise SystemExit(f"unknown figure groups: {sorted(missing)}")

    with tempfile.TemporaryDirectory(prefix="razavi-netlists-") as temp_dir:
        temp_root = Path(temp_dir)
        (temp_root / "netlists").mkdir()
        (temp_root / "simulator").symlink_to(SIMULATOR_ROOT, target_is_directory=True)
        results = [validate_group(group, temp_root, args.timeout) for group in groups]

    for result in results:
        state = "PASS" if result["passed"] else "FAIL"
        print(f"{state}\t{result['group']}\tdecks={len(result['decks'])}")
        for error in result["errors"]:
            print(f"  {error}")

    summary = {
        "total_groups": len(results),
        "total_decks": sum(len(result["decks"]) for result in results),
        "passed_groups": sum(result["passed"] for result in results),
        "failed_groups": sum(not result["passed"] for result in results),
        "results": results,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if summary["failed_groups"] == 0 else 1)


if __name__ == "__main__":
    main()
