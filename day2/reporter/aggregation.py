"""Групування валідних записів за автором і підрахунок агрегатів."""

import logging
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# @dataclass генерує __init__, __repr__ і __eq__ з анотованих полів — як
# TS-тип і конструктор в одному. Анотації в рантаймі НЕ перевіряються, як і
# типи TS після компіляції: AuthorStats("x", "1", ...) створиться мовчки.
@dataclass
class AuthorStats:
    author: str
    courses: int
    published: int
    total_hours: int
    avg_hours: float


# Ключ групування з R5: "Olena" і "olena " мають стати одним автором.
# У звіті показуємо саме нормалізований ключ.
def author_key(record: dict) -> str:
    return record["author"].strip().lower()


# defaultdict(list) на відсутній ключ викликає list() і кладе в словник
# порожній список — аналог (groups[k] ??= []).push(r) у JS.
# Пастка: itertools.groupby групує лише СУСІДНІ елементи.
def group_by_author(records: list[dict]) -> dict[str, list[dict]]:
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[author_key(record)].append(record)
    return groups


# Одна функція рахує і рядок автора, і TOTAL — різниця лише в наборі записів.
def make_stats(author: str, records: list[dict]) -> AuthorStats:
    courses = len(records)
    total_hours = sum(r["hours"] for r in records)
    return AuthorStats(
        author=author,
        courses=courses,
        # bool — підклас int, тож сума True — це їх кількість.
        published=sum(r["published"] for r in records),
        total_hours=total_hours,
        # Без перевірки 0 / 0 кинув би ZeroDivisionError, а не повернув NaN, як JS.
        avg_hours=total_hours / courses if courses else 0.0,
    )


# Мінус дає спадання за годинами, author — стабільний порядок при рівних годинах.
def aggregate(valid: list[dict]) -> list[AuthorStats]:
    logger.debug("aggregating %s valid records", len(valid))
    stats = [make_stats(author, records) for author, records in group_by_author(valid).items()]
    return sorted(stats, key=lambda s: (-s.total_hours, s.author))
