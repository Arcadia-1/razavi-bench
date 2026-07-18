#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

for netlist in "$root"/examples/*.cir; do
  name="$(basename "$netlist")"
  echo "running ${name}"
  ngspice -b -o "$workdir/${name%.cir}.log" "$netlist"
done

echo "ngspice examples passed"
