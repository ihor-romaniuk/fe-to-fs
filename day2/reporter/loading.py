"""Читання вхідного файлу."""

import json
import logging

from reporter.instrument import timed
from reporter.reading import iter_lines

logger = logging.getLogger(__name__)


# Читання окремо від політики: функція лише відкриває й парсить файл, а що
# робити з помилкою (який текст, який exit code) вирішує __main__.
# with закриває файл навіть при винятку, як try/finally.
@timed
def load_courses(path: str) -> list:
    """Прочитати курси з JSON-масиву або з JSONL (один об'єкт на рядок)."""
    logger.debug("reading %s", path)
    if path.endswith(".jsonl"):
        return load_jsonl(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# Генератор віддає по рядку, тож файл цілком у пам'яті не лежить. Список
# записів однаково збираємо: звіту потрібні len(records) і всі валідні записи.
# Зламаний рядок кидає той самий json.JSONDecodeError, що й json.load, тому
# __main__ обробляє обидва формати одним except. Але "line 1" у тексті помилки
# рахується всередині рядка, а не у файлі: json.loads бачить лише один рядок.
def load_jsonl(path: str) -> list:
    return [json.loads(line) for line in iter_lines(path)]
