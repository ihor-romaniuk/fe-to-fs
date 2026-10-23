"""Задача 3. logging замість print у пакеті reporter.

Запуск з теки day2:
    .venv/bin/python -m reporter courses.json
    .venv/bin/python -m reporter courses.json --verbose     # + рядки DEBUG
Перевірка:
    .venv/bin/python -m reporter courses.json 2>&1 1>/dev/null | grep -c WARNING   # 3
    .venv/bin/python -m reporter courses.json 2>/dev/null | diff -u expected_report.txt -

Тека з __init__.py — звичайний пакет: import reporter виконує цей файл.
python -m reporter шукає пакет у sys.path (туди входить поточна тека) і
запускає reporter/__main__.py — як поле "main" у package.json вказує точку входу.
"""
