"""Задача 4. Декоратор @timed і контекстний менеджер (копія задачі 3).

Запуск з теки day2/4-instrument:
    .venv/bin/python -m reporter courses.json --verbose     # рядки "... took N ms"
Перевірка:
    .venv/bin/python -c "from reporter.loading import load_courses; print(load_courses.__name__)"
    .venv/bin/python experiments.py                          # передбачення з NOTES.md

Тека з __init__.py — звичайний пакет: import reporter виконує цей файл.
python -m reporter шукає пакет у sys.path (туди входить поточна тека) і
запускає reporter/__main__.py — як поле "main" у package.json вказує точку входу.
"""
