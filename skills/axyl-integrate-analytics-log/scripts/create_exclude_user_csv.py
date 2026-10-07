#!/usr/bin/env python3
"""Create an analytics exclude-user CSV from the skill asset template."""

import argparse
import csv
import os
import unicodedata
from pathlib import Path


EXPECTED_HEADER = ["title", "appIdGroup", "identifier", "identifierValue"]
FORMULA_PREFIXES = ("=", "+", "-", "@")
MAX_CELL_LENGTH = 512


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--appid-group", required=True)
    parser.add_argument("--identifier", required=True, choices=("userId", "deviceId"))
    parser.add_argument("--identifier-value", required=True)
    return parser.parse_args()


def validate_csv_cell(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty")
    if len(normalized) > MAX_CELL_LENGTH:
        raise ValueError(f"{label} must be at most {MAX_CELL_LENGTH} characters")
    if normalized.startswith(FORMULA_PREFIXES):
        raise ValueError(f"{label} must not start with a spreadsheet formula prefix")
    if any(unicodedata.category(character) == "Cc" for character in normalized):
        raise ValueError(f"{label} must not contain control characters")
    return normalized


def resolve_output(output: Path) -> Path:
    output_root = Path.cwd().resolve()
    resolved = (output_root / output).resolve() if not output.is_absolute() else output.resolve()
    if resolved.suffix.lower() != ".csv":
        raise ValueError("output must use the .csv extension")
    if resolved == output_root or output_root not in resolved.parents:
        raise ValueError("output must stay within the current working directory")
    return resolved


def main() -> None:
    args = parse_args()
    output = resolve_output(args.output)
    template = Path(__file__).resolve().parent.parent / "assets" / "exclude_user_template.csv"

    with template.open("r", encoding="utf-8-sig", newline="") as template_file:
        header = next(csv.reader(template_file), None)
    if header != EXPECTED_HEADER:
        raise ValueError(f"unexpected template header: {header}")

    row = [
        validate_csv_cell("title", args.title),
        validate_csv_cell("appid-group", args.appid_group),
        args.identifier,
        validate_csv_cell("identifier-value", args.identifier_value),
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(output, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.writer(output_file, lineterminator="\r\n")
        writer.writerow(EXPECTED_HEADER)
        writer.writerow(row)


if __name__ == "__main__":
    main()
