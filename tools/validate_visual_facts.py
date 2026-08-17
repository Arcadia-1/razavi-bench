#!/usr/bin/env python3
"""Validate the repository's human-reviewed visual-facts dataset."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any


TOOLS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_ROOT.parent
DATA_PATH = REPO_ROOT / "data" / "visual_facts.jsonl"
EXPECTED_UNITS = 41
EXPECTED_ASSOCIATIONS = 47
EXPECTED_FIGURE_TASKS = 46
EXPECTED_TEXT_TASKS = 4
EXPECTED_SOURCE_HASHES = 38
REQUIRED_FIELDS = {
    "benchmark",
    "schema_version",
    "reference_scope",
    "visual_unit_id",
    "part",
    "figure_number",
    "subfigure",
    "figure_label",
    "source_figure_path",
    "source_figure_sha256",
    "crop_box",
    "task_mappings",
    "netlist_paths",
    "visual_annotation_zh",
    "visual_annotation_en",
    "annotation_sha256",
    "translation_status",
    "review_status",
    "reviewed_at",
}
FORBIDDEN_FIELDS = {
    "image_path",
    "image_sha256",
    "cdl_spice",
    "description_zh",
    "description_en",
    "other_visual_information_zh",
    "other_visual_information_en",
    "facts_sha256",
    "translations_sha256",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotation_sha256(row: dict[str, Any]) -> str:
    payload = {
        "visual_annotation_en": row["visual_annotation_en"],
        "visual_annotation_zh": row["visual_annotation_zh"],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if (
        len(header) != 24
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
    ):
        raise ValueError("not a PNG with an IHDR header")
    return struct.unpack(">II", header[16:24])


def repository_path(raw_path: Any, label: str, errors: list[str]) -> Path | None:
    relative = Path(str(raw_path))
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{label}: path must stay inside the repository: {relative}")
        return None
    resolved = (REPO_ROOT / relative).resolve()
    if resolved != REPO_ROOT and REPO_ROOT not in resolved.parents:
        errors.append(f"{label}: path escapes the repository: {relative}")
        return None
    return resolved


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise SystemExit(f"{path}:{line_number}: row must be an object")
            rows.append(row)
    return rows


def validate_row(row: dict[str, Any], line_number: int) -> list[str]:
    label = f"line {line_number} ({row.get('visual_unit_id', '<missing>')})"
    errors: list[str] = []
    forbidden = FORBIDDEN_FIELDS & set(row)
    if forbidden:
        errors.append(f"{label}: forbidden duplicate-data fields {sorted(forbidden)}")
    missing = REQUIRED_FIELDS - set(row)
    if missing:
        errors.append(f"{label}: missing fields {sorted(missing)}")
        return errors
    unexpected = set(row) - REQUIRED_FIELDS
    if unexpected:
        errors.append(f"{label}: unexpected fields {sorted(unexpected)}")

    if row["benchmark"] != "razavi-bench":
        errors.append(f"{label}: benchmark must be razavi-bench")
    if row["schema_version"] != 3:
        errors.append(f"{label}: schema_version must be 3")
    if row["reference_scope"] != "visual-only-annotations":
        errors.append(f"{label}: unexpected reference_scope")
    if row["part"] not in {"part1", "part2"}:
        errors.append(f"{label}: invalid part")
    if not isinstance(row["figure_number"], int) or row["figure_number"] < 1:
        errors.append(f"{label}: figure_number must be a positive integer")
    if not re.fullmatch(r"part[12]-figure-\d{2}(?:-[a-z0-9]+)?", str(row["visual_unit_id"])):
        errors.append(f"{label}: invalid visual_unit_id")
    if not re.fullmatch(r"[0-9a-f]{64}", str(row["source_figure_sha256"])):
        errors.append(f"{label}: source_figure_sha256 must be lowercase SHA-256")
    if row["review_status"] != "human-reviewed":
        errors.append(f"{label}: review_status must be human-reviewed")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row["reviewed_at"])):
        errors.append(f"{label}: reviewed_at must use YYYY-MM-DD")
    if not isinstance(row["visual_annotation_zh"], str):
        errors.append(f"{label}: visual_annotation_zh must be a string")
    if not isinstance(row["visual_annotation_en"], str):
        errors.append(f"{label}: visual_annotation_en must be a string")
    if bool(str(row["visual_annotation_zh"]).strip()) != bool(
        str(row["visual_annotation_en"]).strip()
    ):
        errors.append(f"{label}: visual annotations must be empty in both languages or neither")
    if row["annotation_sha256"] != annotation_sha256(row):
        errors.append(f"{label}: annotation_sha256 mismatch")
    if row["translation_status"] != "model-translated-and-cross-checked":
        errors.append(f"{label}: unexpected translation_status")
    english = str(row["visual_annotation_en"])
    if re.search(r"[\u3400-\u9fff]", english):
        errors.append(f"{label}: CJK text remains in English translation fields")
    source_tokens = set(
        re.findall(
            r"[A-Za-z][A-Za-z0-9_]*",
            str(row["visual_annotation_zh"]),
        )
    )
    english_tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", english))
    if source_tokens - english_tokens:
        errors.append(
            f"{label}: English translation loses circuit identifiers "
            f"{sorted(source_tokens - english_tokens)}"
        )

    source_path = repository_path(row["source_figure_path"], label, errors)
    source_dimensions: tuple[int, int] | None = None
    if source_path is not None:
        source_relative = source_path.relative_to(REPO_ROOT).as_posix()
        if not source_relative.startswith("tasks/"):
            errors.append(f"{label}: source figure must be under tasks/")
        if not source_path.is_file():
            errors.append(f"{label}: missing source figure {source_relative}")
        else:
            if sha256_file(source_path) != row["source_figure_sha256"]:
                errors.append(f"{label}: source figure hash mismatch")
            try:
                source_dimensions = png_size(source_path)
            except ValueError as exc:
                errors.append(f"{label}: source figure {exc}")

    crop = row["crop_box"]
    if not (
        isinstance(crop, list)
        and len(crop) == 4
        and all(isinstance(value, int) and not isinstance(value, bool) for value in crop)
    ):
        errors.append(f"{label}: crop_box must contain four integers")
    elif source_dimensions is not None:
        source_width, source_height = source_dimensions
        left, top, right, bottom = crop
        if not (
            0 <= left < right <= source_width
            and 0 <= top < bottom <= source_height
        ):
            errors.append(
                f"{label}: crop_box {crop} exceeds source image "
                f"{source_width}x{source_height}"
            )

    netlist_paths = row["netlist_paths"]
    if not isinstance(netlist_paths, list) or not netlist_paths:
        errors.append(f"{label}: netlist_paths must be a non-empty list")
    elif not all(isinstance(path, str) and path for path in netlist_paths):
        errors.append(f"{label}: every netlist path must be a non-empty string")
    elif netlist_paths != sorted(set(netlist_paths)):
        errors.append(f"{label}: netlist_paths must be unique and sorted")
    else:
        expected_netlist_prefix = (
            f"netlists/{row['part']}-figure-{row['figure_number']:02d}-"
            f"{row['source_figure_sha256'][:8]}/"
        )
        for raw_netlist_path in netlist_paths:
            netlist_path = repository_path(raw_netlist_path, label, errors)
            netlist_relative = str(raw_netlist_path).replace("\\", "/")
            if not netlist_relative.startswith("netlists/") or not netlist_relative.endswith(
                ".cir"
            ):
                errors.append(
                    f"{label}: executable netlist must be a .cir file under netlists/: "
                    f"{raw_netlist_path}"
                )
            elif not netlist_relative.startswith(expected_netlist_prefix):
                errors.append(
                    f"{label}: netlist path does not match the source figure hash: "
                    f"{raw_netlist_path}"
                )
            elif netlist_path is None or not netlist_path.is_file():
                errors.append(f"{label}: missing executable netlist {raw_netlist_path}")

    mappings = row["task_mappings"]
    if not isinstance(mappings, list) or not mappings:
        errors.append(f"{label}: task_mappings must be a non-empty list")
    else:
        seen: set[tuple[str, int]] = set()
        for mapping in mappings:
            if not isinstance(mapping, dict):
                errors.append(f"{label}: task mapping must be an object")
                continue
            task_path = str(mapping.get("task_path") or "")
            question_number = mapping.get("question_number")
            if not isinstance(question_number, int) or isinstance(question_number, bool):
                errors.append(f"{label}: question_number must be an integer")
                continue
            key = (task_path, question_number)
            if key in seen:
                errors.append(f"{label}: duplicate task mapping {key}")
            seen.add(key)
            task = repository_path(task_path, label, errors)
            if not task_path.startswith("tasks/") or task is None or not task.is_dir():
                errors.append(f"{label}: invalid task path {task_path}")
            else:
                match = re.match(r"part[12]-(\d{3})-", task.name)
                if not match or int(match.group(1)) != question_number:
                    errors.append(
                        f"{label}: question_number does not match task path {task_path}"
                    )
                elif source_path is not None and source_path.is_file():
                    task_figure_hashes = {
                        sha256_file(path) for path in task.glob("*.png") if path.is_file()
                    }
                    if row["source_figure_sha256"] not in task_figure_hashes:
                        errors.append(
                            f"{label}: mapped task does not contain the referenced figure "
                            f"content: {task_path}"
                        )
    return errors


def main() -> None:
    rows = load_rows(DATA_PATH)
    errors: list[str] = []
    identifiers: set[str] = set()
    mapped_tasks: set[str] = set()
    associations: set[tuple[str, str]] = set()
    source_hashes: set[str] = set()
    netlist_paths: set[str] = set()

    for line_number, row in enumerate(rows, 1):
        unit_id = str(row.get("visual_unit_id") or "")
        if not unit_id:
            errors.append(f"line {line_number}: empty visual_unit_id")
        elif unit_id in identifiers:
            errors.append(f"line {line_number}: duplicate visual_unit_id {unit_id}")
        identifiers.add(unit_id)
        errors.extend(validate_row(row, line_number))
        source_hashes.add(str(row.get("source_figure_sha256") or ""))
        raw_netlist_paths = row.get("netlist_paths")
        if isinstance(raw_netlist_paths, list):
            netlist_paths.update(str(path) for path in raw_netlist_paths)
        mappings = row.get("task_mappings")
        if isinstance(mappings, list):
            for mapping in mappings:
                if not isinstance(mapping, dict) or not mapping.get("task_path"):
                    continue
                task_path = str(mapping["task_path"])
                association = (unit_id, task_path)
                if association in associations:
                    errors.append(f"line {line_number}: duplicate association {association}")
                associations.add(association)
                mapped_tasks.add(task_path)

    task_dirs = sorted(path for path in (REPO_ROOT / "tasks").iterdir() if path.is_dir())
    figure_tasks = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in task_dirs
        if any(path.glob("*.png"))
    }
    text_tasks = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in task_dirs
        if not any(path.glob("*.png"))
    }

    expected_counts = [
        ("rows", len(rows), EXPECTED_UNITS),
        ("task mappings", len(associations), EXPECTED_ASSOCIATIONS),
        ("figure tasks", len(figure_tasks), EXPECTED_FIGURE_TASKS),
        ("text-only tasks", len(text_tasks), EXPECTED_TEXT_TASKS),
        ("source hashes", len(source_hashes), EXPECTED_SOURCE_HASHES),
    ]
    for name, actual, expected in expected_counts:
        if actual != expected:
            errors.append(f"expected {expected} {name}, found {actual}")
    if len(task_dirs) != EXPECTED_FIGURE_TASKS + EXPECTED_TEXT_TASKS:
        errors.append(f"expected 50 total tasks, found {len(task_dirs)}")
    if mapped_tasks != figure_tasks:
        errors.append(
            "mapped task coverage differs from figure tasks: "
            f"missing={sorted(figure_tasks - mapped_tasks)}, "
            f"extra={sorted(mapped_tasks - figure_tasks)}"
        )
    legacy_directory = REPO_ROOT / "reviewed_visual_facts"
    if legacy_directory.exists():
        errors.append(
            "legacy reviewed_visual_facts/ directory must be removed; source figures "
            "are reused from tasks/"
        )

    if errors:
        for error in errors:
            print(f"FAIL\t{error}")
        raise SystemExit(1)
    print(
        "PASS\t"
        f"units={len(rows)} source_figures={len(source_hashes)} "
        f"associations={len(associations)} figure_tasks={len(mapped_tasks)} "
        f"text_only_tasks={len(text_tasks)} netlists={len(netlist_paths)}"
    )


if __name__ == "__main__":
    main()
