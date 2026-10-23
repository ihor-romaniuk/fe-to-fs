"""Задача 4. Звірка передбачень із NOTES.md з фактом.

Запуск з теки day2/4-instrument: .venv/bin/python experiments.py
"""

import logging
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from types import TracebackType
from typing import TextIO

from reporter.instrument import Timer, timer
from reporter.loading import load_courses

# У stdout, а не в stderr: так рядки логу й print ідуть у тому порядку, в якому
# їх викликали, навіть коли вивід перенаправлено у файл.
logging.basicConfig(level=logging.DEBUG, format="  log> %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("experiments")


# 1. Що лишається від функції після декоратора. Запускається двічі: як є і з
#    тимчасово прибраним @functools.wraps у reporter/instrument.py.
def check_wraps() -> None:
    print("1) @timed на load_courses")
    print(f"   __name__    = {load_courses.__name__!r}")
    print(f"   __doc__     = {load_courses.__doc__!r}")
    print(f"   __wrapped__ = {hasattr(load_courses, '__wrapped__')}")
    load_courses("courses.json")


# Timer, який ще й друкує, що саме Python передав у __exit__.
class SpyTimer(Timer):
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        print(f"   __exit__: exc_type={exc_type!r}")
        print(f"             exc={exc!r}, tb={type(tb).__name__}")
        super().__exit__(exc_type, exc, tb)


def check_timer_class() -> None:
    print("2) ValueError усередині with Timer")
    t = SpyTimer("demo")
    try:
        with t as entered:
            print(f"   as дає той самий об'єкт: {entered is t}")
            raise ValueError("boom")
    except ValueError as e:
        print(f"   назовні долетів {e!r}, elapsed_ms заповнено: {t.elapsed_ms > 0}")


def check_timer_generator() -> None:
    print("3) ValueError усередині with timer (try/finally)")
    try:
        with timer("demo"):
            raise ValueError("boom")
    except ValueError as e:
        print(f"   назовні долетів {e!r}")


# Навмисно зламаний варіант: той самий генератор, але без try/finally. Ресурс —
# відкритий файл; open() поза with тут і є експериментом, тому noqa.
@contextmanager
def opened_without_finally(path: str) -> Iterator[TextIO]:
    start = time.perf_counter()
    f = open(path, encoding="utf-8")  # noqa: SIM115
    yield f
    f.close()
    logger.debug("%s took %.1f ms", path, (time.perf_counter() - start) * 1000)


@contextmanager
def opened_with_finally(path: str) -> Iterator[TextIO]:
    start = time.perf_counter()
    f = open(path, encoding="utf-8")  # noqa: SIM115
    try:
        yield f
    finally:
        f.close()
        logger.debug("%s took %.1f ms", path, (time.perf_counter() - start) * 1000)


def check_without_finally() -> None:
    for manager in (opened_without_finally, opened_with_finally):
        print(f"4) ValueError усередині with {manager.__name__}")
        try:
            with manager(os.devnull) as f:
                raise ValueError("boom")
        except ValueError as e:
            print(f"   назовні долетів {e!r}, f.closed = {f.closed}")


if __name__ == "__main__":
    check_wraps()
    check_timer_class()
    check_timer_generator()
    check_without_finally()
