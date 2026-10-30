"""Задача 5. Пікова пам'ять: f.readlines() проти генератора iter_lines.

Запуск з теки day2: .venv/bin/python bench_mem.py
Створює big.jsonl на 200 000 рядків (у .gitignore).
"""

import tracemalloc
from collections.abc import Callable
from pathlib import Path

from reporter.reading import iter_lines

BIG = "big.jsonl"
LINES = 200_000


# tracemalloc рахує кожну алокацію Python-об'єктів між start() і stop(), а
# get_traced_memory() віддає (скільки зайнято зараз, максимум за весь час).
# Нам потрібен максимум: після виходу з fn список рядків уже звільнено.
def peak_mb(fn: Callable[[str], int], *args: str) -> float:
    tracemalloc.start()
    fn(*args)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1e6


# readlines() будує список з усіх рядків одразу: 200 000 str по ~75 байт
# плюс 8 байт на посилання в самому списку.
def count_readlines(path: str) -> int:
    with open(path, encoding="utf-8") as f:
        return len(f.readlines())


# Обгортка мусить реально пройти генератор. peak_mb(iter_lines, BIG) лише
# створив би об'єкт генератора: тіло, а з ним open() і читання, не запустилось
# би, і замір показав би нуль з неправильної причини. sum(1 for _ in ...) тягне
# рядки по одному, і в пам'яті одночасно живе лише поточний.
def count_generator(path: str) -> int:
    return sum(1 for _ in iter_lines(path))


if __name__ == "__main__":
    Path(BIG).write_text(
        "".join(f'{{"id": {i}, "hours": 5}}\n' for i in range(LINES)), encoding="utf-8"
    )

    # Нуль пам'яті ще не доводить, що генератор щось читав: недоітерований теж
    # дав би нуль. Тому спершу перевіряємо, що обидва варіанти бачать усі рядки.
    for fn in (count_readlines, count_generator):
        assert fn(BIG) == LINES, f"{fn.__name__}: expected {LINES} lines"

    readlines_mb = peak_mb(count_readlines, BIG)
    generator_mb = peak_mb(count_generator, BIG)
    print(f"readlines: peak {readlines_mb:.1f} MB")
    print(f"generator: peak {generator_mb:.1f} MB ({generator_mb * 1e3:.1f} KB)")

    assert readlines_mb > 10, f"readlines peak {readlines_mb:.1f} MB, expected > 10 MB"
    assert generator_mb < 1, f"generator peak {generator_mb:.1f} MB, expected < 1 MB"
