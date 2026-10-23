"""Правила R1-R5 і відбір валідних записів. Пояснення до правил — у day1/2-report.py."""

import logging

from reporter.errors import ValidationError

logger = logging.getLogger(__name__)

FIELD_TYPES = {
    "id": int,
    "title": str,
    "author": str,
    "hours": int,
    "published": bool,
    "tags": list,
}

HOURS_MIN, HOURS_MAX = 1, 200
TITLE_MIN_LEN = 3


# R1. Ключі на місці, зайві не заважають.
def check_required_fields(record: dict) -> None:
    for field in FIELD_TYPES:
        if field not in record:
            raise ValidationError("required_fields", field, "missing")


# R2. Точний тип без приведення: type(...) is, бо bool — підклас int.
def check_types(record: dict) -> None:
    for field, expected in FIELD_TYPES.items():
        value = record[field]
        if type(value) is not expected:
            raise ValidationError(
                "types",
                field,
                f"expected {expected.__name__}, got {type(value).__name__} ({value!r})",
            )


# R3. id > 0 і не повторюється; seen_ids лише читаємо.
def check_id_unique_positive(record: dict, seen_ids: set[int]) -> None:
    record_id = record["id"]
    if record_id <= 0:
        raise ValidationError("id_unique_positive", "id", f"expected > 0, got {record_id}")
    if record_id in seen_ids:
        raise ValidationError("id_unique_positive", "id", f"duplicate id {record_id}")


# R4. 1 <= hours <= 200.
def check_hours_range(record: dict) -> None:
    hours = record["hours"]
    if not HOURS_MIN <= hours <= HOURS_MAX:
        raise ValidationError(
            "hours_range", "hours", f"expected {HOURS_MIN}..{HOURS_MAX}, got {hours}"
        )


# R5. Після strip() у назві >= 3 символи, автор непорожній.
def check_non_empty_text(record: dict) -> None:
    title = record["title"]
    if len(title.strip()) < TITLE_MIN_LEN:
        raise ValidationError(
            "non_empty_text", "title", f"expected >= {TITLE_MIN_LEN} chars, got {title!r}"
        )
    author = record["author"]
    if not author.strip():
        raise ValidationError("non_empty_text", "author", f"expected non-empty, got {author!r}")


def validate_course(record: dict, seen_ids: set[int]) -> None:
    check_required_fields(record)
    check_types(record)
    check_id_unique_positive(record, seen_ids)
    check_hours_range(record)
    check_non_empty_text(record)


# Цикл повернувся сюди з __main__. У задачі 2 він друкував у stderr, а це справа
# CLI. logger.warning не знає, куди піде рядок: це вирішує basicConfig у __main__.
def split_valid(records: list) -> list[dict]:
    seen_ids: set[int] = set()
    valid = []
    for index, record in enumerate(records):
        try:
            validate_course(record, seen_ids)
        except ValidationError as e:
            # Аргументи окремо, а не f-string: logging підставляє їх у %s, лише
            # коли рядок справді йде у вивід. f-string зібрався б завжди, навіть
            # якщо рівень логера його відкине. Ruff ловить f-string у logging (G004).
            logger.warning(
                "[invalid] index=%s id=%s rule=%s field=%s: %s",
                index,
                record.get("id", "?"),
                e.rule,
                e.field,
                e.detail,
            )
        else:
            seen_ids.add(record["id"])
            valid.append(record)
    return valid
