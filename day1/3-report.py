"""Задача 3. Групування, агрегати і звіт.

Запуск:    python3 day1/3-report.py day1/courses.json
Перевірка: cd day1 && python3 3-report.py courses.json 2>/dev/null | diff -u expected_report.txt -
"""

import json
import sys
from collections import defaultdict
from dataclasses import dataclass

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_BAD_INPUT = 2

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

# Формат таблиці взятий готовим із завдання: пробіли значущі, їх звіряє diff.
# {x:<16} — вліво в полі ширини 16, {x:>8} — вправо (як padEnd/padStart у JS),
# .2f — два знаки після коми (як toFixed(2)), "-" * 56 — як "-".repeat(56).
# Ширина — це мінімум, а не обрізання: довше ім'я автора зсуне колонки.
HEADER = f"{'author':<16}{'courses':>8}{'published':>10}{'total_hours':>12}{'avg_hours':>10}"
SEP = "-" * 56


# @dataclass генерує __init__, __repr__ і __eq__ з анотованих полів — як
# TS-тип і конструктор в одному. На відміну від dict, помилка в імені поля
# (s.total_hour) падає одразу, а редактор підказує поля. Анотації в рантаймі
# НЕ перевіряються, як і типи TS після компіляції: AuthorStats("x", "1", ...)
# створиться мовчки.
@dataclass
class AuthorStats:
    author: str
    courses: int
    published: int
    total_hours: int
    avg_hours: float


def render_row(s: AuthorStats) -> str:
    return f"{s.author:<16}{s.courses:>8}{s.published:>10}{s.total_hours:>12}{s.avg_hours:>10.2f}"


# Валідація — без змін із задачі 2, докладні пояснення в 2-report.py.
class ValidationError(Exception):
    def __init__(self, rule: str, field: str, detail: str):
        super().__init__(f"rule={rule} field={field}: {detail}")
        self.rule = rule
        self.field = field
        self.detail = detail


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


def validate_record(record: dict, seen_ids: set[int]) -> None:
    check_required_fields(record)
    check_types(record)
    check_id_unique_positive(record, seen_ids)
    check_hours_range(record)
    check_non_empty_text(record)


# Цикл із main задачі 2 винесено у функцію: тепер він ще й збирає валідні
# записи, бо звіт будується лише з них.
def split_valid(records: list) -> list[dict]:
    seen_ids: set[int] = set()
    valid = []
    for index, record in enumerate(records):
        try:
            validate_record(record, seen_ids)
        except ValidationError as e:
            print(
                f"[invalid] index={index} id={record.get('id', '?')} "
                f"rule={e.rule} field={e.field}: {e.detail}",
                file=sys.stderr,
            )
        else:
            seen_ids.add(record["id"])
            valid.append(record)
    return valid


# Ключ групування з R5: "Olena" і "olena " мають стати одним автором.
# У звіті показуємо саме нормалізований ключ.
def author_key(record: dict) -> str:
    return record["author"].strip().lower()


# defaultdict(list) на відсутній ключ викликає list() і кладе в словник
# порожній список, тому append працює без перевірки "чи є вже такий ключ".
# Аналог у JS: (groups[k] ??= []).push(r) або Object.groupBy.
# Передаємо саму функцію list, а не [] — її викличуть окремо для кожного ключа.
# Пастка: itertools.groupby звучить схоже, але групує лише СУСІДНІ елементи,
# тому на невідсортованих даних один автор розпадеться на кілька груп.
def group_by_author(records: list[dict]) -> dict[str, list[dict]]:
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[author_key(record)].append(record)
    return groups


# Одна функція рахує і рядок автора, і TOTAL — різниця лише в наборі записів.
def make_stats(author: str, records: list[dict]) -> AuthorStats:
    courses = len(records)
    # sum(... for ...) — генератор: як reduce((a, r) => a + r.hours, 0), але
    # без проміжного списку. На порожньому вході sum дає 0, а reduce у JS без
    # початкового значення кидає TypeError.
    total_hours = sum(r["hours"] for r in records)
    return AuthorStats(
        author=author,
        courses=courses,
        # bool — підклас int (задача 1, п. 1), тож сума True — це їх кількість.
        published=sum(r["published"] for r in records),
        total_hours=total_hours,
        # / у Python 3 завжди дає float (ціле ділення — це //). x if c else y —
        # тернарний оператор, як c ? x : y. Без перевірки 0 / 0 кинув би
        # ZeroDivisionError, а не повернув NaN, як JS.
        avg_hours=total_hours / courses if courses else 0.0,
    )


# Сортування з задачі 1, п. 8: мінус дає спадання за годинами, author —
# стабільний порядок при рівних годинах. Без другого ключа порядок залежав
# би від порядку рядків у файлі, і звіт "змінювався" б на тих самих даних.
def build_author_stats(valid: list[dict]) -> list[AuthorStats]:
    # list comprehension — аналог map; .items() — як Object.entries.
    stats = [make_stats(author, records) for author, records in group_by_author(valid).items()]
    return sorted(stats, key=lambda s: (-s.total_hours, s.author))


def render_report(source: str, total: int, valid: list[dict]) -> str:
    # TOTAL рахуємо по сирих записах, а не по рядках авторів: 40 / 3 = 13.33.
    # Середнє авторських середніх, (10 + 20) / 2 = 15.00, дає кожному автору
    # однакову вагу незалежно від кількості курсів. Та сама пастка чекає з
    # Avg() над згрупованим queryset на Дні 4.
    lines = [
        "=== COURSE REPORT ===",
        f"source: {source}",
        f"records: {total} total, {len(valid)} valid, {total - len(valid)} invalid",
        HEADER,
        SEP,
        # * розпаковує генератор у список, як spread ...arr у JS.
        *(render_row(s) for s in build_author_stats(valid)),
        SEP,
        render_row(make_stats("TOTAL", valid)),
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: python3 {argv[0]} <courses.json>", file=sys.stderr)
        return EXIT_BAD_INPUT
    path = argv[1]

    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
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

    # Звіт друкуємо й тоді, коли є невалідні записи: діагностика вже пішла у
    # stderr, а stdout отримує лише звіт. Тому 2>/dev/null лишає рівно його,
    # і результат можна звіряти через diff або перенаправити у файл.
    print(render_report(path, len(records), valid))
    return EXIT_INVALID if rejected else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
