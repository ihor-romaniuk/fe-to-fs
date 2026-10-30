"""Задача 5. Генератор iter_lines і читання .jsonl.

Запуск з теки day2:
    .venv/bin/python -m reporter courses.jsonl
Перевірка:
    diff <(.venv/bin/python -m reporter courses.json 2>/dev/null) \\
         <(.venv/bin/python -m reporter courses.jsonl 2>/dev/null)   # лише рядок source:
    .venv/bin/python bench_mem.py                 # peak readlines > 10 MB, генератора < 1 MB

Тека з __init__.py — звичайний пакет: import reporter виконує цей файл.
python -m reporter шукає пакет у sys.path (туди входить поточна тека) і
запускає reporter/__main__.py — як поле "main" у package.json вказує точку входу.
"""
