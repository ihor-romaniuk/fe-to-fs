"""Задача 2. Пакет reporter: report.py з Дня 1 (day1/3-report.py), розкладений на модулі.

Запуск з теки day2/2-reporter-package:
    .venv/bin/python -m reporter courses.json
Перевірка:
    .venv/bin/python -m reporter courses.json | diff -u expected_report.txt -

Тека з __init__.py — звичайний пакет: import reporter виконує цей файл.
python -m reporter шукає пакет у sys.path (туди входить поточна тека) і
запускає reporter/__main__.py — як поле "main" у package.json вказує точку входу.
"""
