"""Замір часу: декоратор @timed і контекстний менеджер у двох варіантах."""

import functools
import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import TracebackType

logger = logging.getLogger(__name__)


# [**P, R] — generic-параметри (Python 3.12), як <A extends unknown[], R> у TS:
# P запам'ятовує аргументи func, R — її результат. Тому декорована функція
# для type checker має ту саму сигнатуру, що й оригінал, а не (*Any) -> Any.
def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    # wraps копіює з func на wrapper __name__, __doc__, __module__ і додає
    # __wrapped__. Без нього load_courses.__name__ був би "wrapper".
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # perf_counter — монотонний годинник для замірів, як performance.now()
        # у JS; time.time() може стрибнути, якщо система підправить час.
        start = time.perf_counter()
        result = func(*args, **kwargs)
        logger.debug("%s took %.1f ms", func.__name__, (time.perf_counter() - start) * 1000)
        return result

    return wrapper


# with Timer("x") as t: ... — Python викликає __enter__ на вході в блок і
# __exit__ на виході з нього, навіть якщо всередині вилетів виняток.
class Timer:
    def __init__(self, name: str) -> None:
        self.name = name
        self.start = 0.0
        self.elapsed_ms = 0.0

    # Те, що повертає __enter__, потрапляє в змінну після as.
    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    # exc_type — клас винятку (ValueError), exc — сам об'єкт, tb — traceback;
    # без винятку всі троє None. Повертаємо None, тож виняток летить далі.
    # return True проковтнув би його, як порожній catch у JS.
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000
        if exc_type is None:
            logger.debug("%s took %.1f ms", self.name, self.elapsed_ms)
        else:
            logger.debug(
                "%s took %.1f ms, raised %s", self.name, self.elapsed_ms, exc_type.__name__
            )


# Той самий менеджер через генератор: код до yield — це __enter__, після — __exit__,
# а yield віддає значення для as (тут нічого). Виняток з блоку with вилітає
# з рядка yield, тому без try/finally код після yield не виконається.
@contextmanager
def timer(name: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.debug("%s took %.1f ms", name, (time.perf_counter() - start) * 1000)
