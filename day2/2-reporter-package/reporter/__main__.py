"""Точка входу: аргументи, діагностика в stderr і exit codes."""

import json
import sys

from reporter.errors import ReporterError
from reporter.loading import load_courses
from reporter.rendering import render_report
from reporter.validation import validate_course

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_BAD_INPUT = 2


# Цикл живе тут, а не у validation.py, бо друкує в stderr, а діагностика — справа
# CLI. Ловимо базовий ReporterError: except ловить і нащадків, тож сюди потрапляє
# ValidationError. Текст "rule=... field=...: ..." дає його __str__.
def split_valid(records: list) -> list[dict]:
    seen_ids: set[int] = set()
    valid = []
    for index, record in enumerate(records):
        try:
            validate_course(record, seen_ids)
        except ReporterError as e:
            print(f"[invalid] index={index} id={record.get('id', '?')} {e}", file=sys.stderr)
        else:
            seen_ids.add(record["id"])
            valid.append(record)
    return valid


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        # З -m argv[0] — повний шлях до __main__.py, тому команду пишемо явно.
        print("usage: python3 -m reporter <courses.json>", file=sys.stderr)
        return EXIT_BAD_INPUT
    path = argv[1]

    try:
        records = load_courses(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return EXIT_BAD_INPUT
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        return EXIT_BAD_INPUT

    valid = split_valid(records)
    rejected = len(records) - len(valid)
    if rejected:
        print(f"[invalid] summary: {rejected} of {len(records)} records rejected", file=sys.stderr)

    # Звіт друкуємо й тоді, коли є невалідні записи: діагностика вже пішла в
    # stderr, а stdout отримує лише звіт.
    print(render_report(path, len(records), valid))
    return EXIT_INVALID if rejected else EXIT_OK


# python -m reporter запускає цей файл з __name__ == "__main__". Перевірка
# потрібна, щоб import reporter.__main__ (наприклад, у тестах) не запускав main.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
