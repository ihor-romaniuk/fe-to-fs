#!/usr/bin/env python3
"""Validate course records from a JSON file and print a per-author report.

Usage: python3 report_ai.py <courses.json>

Every invalid record is reported on stderr with the name of the first rule it
breaks (R1 -> R5); the report on stdout is built from the valid records only.

Exit codes: 0 all records valid, 1 at least one invalid record (the report is
still printed), 2 the file is missing, unreadable or not valid JSON.
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

EXIT_OK = 0
EXIT_INVALID_RECORDS = 1
EXIT_BAD_INPUT = 2

# Exact types: bool is a subclass of int, so `true` must not pass as an int.
FIELD_TYPES: dict[str, type] = {
    "id": int,
    "title": str,
    "author": str,
    "hours": int,
    "published": bool,
    "tags": list,
}
HOURS_MIN, HOURS_MAX = 1, 200
TITLE_MIN_LEN = 3

ROW = "{:<16} {:>7} {:>9} {:>11} {:>9}"
HEADER = ROW.format("author", "courses", "published", "total_hours", "avg_hours")
RULE_LINE = "-" * len(HEADER)


class InputError(Exception):
    """The input file cannot be used at all."""


@dataclass(frozen=True)
class Violation:
    position: int  # 1-based position of the record in the input array
    record: Any
    rule: str
    detail: str

    def __str__(self) -> str:
        where = f"#{self.position}"
        if isinstance(self.record, dict) and "id" in self.record:
            where += f" (id={json.dumps(self.record['id'])})"
        return f"invalid record {where}: {self.rule}: {self.detail}"


@dataclass
class AuthorStats:
    courses: int = 0
    published: int = 0
    total_hours: int = 0

    def add(self, record: dict) -> None:
        self.courses += 1
        self.published += record["published"]
        self.total_hours += record["hours"]

    @property
    def avg_hours(self) -> float:
        return self.total_hours / self.courses if self.courses else 0.0


def type_name(value: Any) -> str:
    return "null" if value is None else type(value).__name__


# Each rule returns None when the record passes, or a human-readable reason.
# Rules run in order, so later rules may rely on what earlier ones checked.
Rule = Callable[[Any, set[int]], str | None]


def check_required_fields(record: Any, accepted_ids: set[int]) -> str | None:
    if not isinstance(record, dict):
        return f"expected an object, got {type_name(record)}"
    missing = [field for field in FIELD_TYPES if field not in record]
    return f"missing {', '.join(missing)}" if missing else None


def check_types(record: dict, accepted_ids: set[int]) -> str | None:
    for field, expected in FIELD_TYPES.items():
        value = record[field]
        if type(value) is not expected:
            return f"{field} must be {expected.__name__}, got {type_name(value)}"
    return None


def check_id_unique_positive(record: dict, accepted_ids: set[int]) -> str | None:
    record_id = record["id"]
    if record_id <= 0:
        return f"id must be > 0, got {record_id}"
    if record_id in accepted_ids:
        return f"id {record_id} is already used by a valid record"
    return None


def check_hours_range(record: dict, accepted_ids: set[int]) -> str | None:
    hours = record["hours"]
    if not HOURS_MIN <= hours <= HOURS_MAX:
        return f"hours must be between {HOURS_MIN} and {HOURS_MAX}, got {hours}"
    return None


def check_non_empty_text(record: dict, accepted_ids: set[int]) -> str | None:
    if len(record["title"].strip()) < TITLE_MIN_LEN:
        return f"title must have at least {TITLE_MIN_LEN} non-blank characters"
    if not record["author"].strip():
        return "author must not be blank"
    return None


RULES: list[tuple[str, Rule]] = [
    ("required_fields", check_required_fields),
    ("types", check_types),
    ("id_unique_positive", check_id_unique_positive),
    ("hours_range", check_hours_range),
    ("non_empty_text", check_non_empty_text),
]


def load_records(path: str) -> list:
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise InputError(f"file not found: {path}") from None
    except OSError as error:
        raise InputError(f"cannot read {path}: {error.strerror}") from None
    except ValueError as error:  # JSONDecodeError and UnicodeDecodeError
        raise InputError(f"invalid JSON in {path}: {error}") from None
    if not isinstance(data, list):
        raise InputError(f"invalid input in {path}: expected a JSON array, got {type_name(data)}")
    return data


def validate(records: list) -> tuple[list[dict], list[Violation]]:
    valid: list[dict] = []
    violations: list[Violation] = []
    accepted_ids: set[int] = set()
    for position, record in enumerate(records, start=1):
        for rule_name, rule in RULES:
            detail = rule(record, accepted_ids)
            if detail is not None:
                violations.append(Violation(position, record, rule_name, detail))
                break
        else:
            valid.append(record)
            accepted_ids.add(record["id"])
    return valid, violations


def format_row(label: str, stats: AuthorStats) -> str:
    return ROW.format(label, stats.courses, stats.published, stats.total_hours, f"{stats.avg_hours:.2f}")


def render_report(source: str, total_records: int, valid: list[dict]) -> str:
    by_author: dict[str, AuthorStats] = {}
    overall = AuthorStats()
    for record in valid:
        by_author.setdefault(record["author"], AuthorStats()).add(record)
        overall.add(record)

    ranked = sorted(by_author.items(), key=lambda item: (-item[1].total_hours, item[0]))
    invalid_count = total_records - len(valid)

    lines = [
        "=== COURSE REPORT ===",
        f"source: {source}",
        f"records: {total_records} total, {len(valid)} valid, {invalid_count} invalid",
        HEADER,
        RULE_LINE,
        *(format_row(author, stats) for author, stats in ranked),
        RULE_LINE,
        format_row("TOTAL", overall),
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate course records and print a per-author report.")
    parser.add_argument("path", help="path to a JSON array of course records")
    args = parser.parse_args(argv)

    try:
        records = load_records(args.path)
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_BAD_INPUT

    valid, violations = validate(records)
    for violation in violations:
        print(violation, file=sys.stderr)
    sys.stdout.write(render_report(args.path, len(records), valid))

    return EXIT_INVALID_RECORDS if violations else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
