"""Задача 4. Бенчмарк: list проти set.

Запуск: python3 day1/4-bench.py
Триває кілька хвилин: один прогін list-варіанта на 100 000 — десятки секунд.
"""

import timeit

SIZES = (1_000, 10_000, 100_000)  # _ у числах — роздільник розрядів, як і в JS
REPEAT = 3


# Дані детерміновані: b зсунутий на n // 2, тому перетин — рівно n // 2
# елементів, і кожен запуск міряє ту саму роботу.
def make_data(n: int) -> tuple[list[int], list[int]]:
    a = list(range(n))
    b = list(range(n // 2, n + n // 2))
    return a, b


# 1. x in list — перебір зліва направо, O(len(b)), як arr.includes у JS. Усередині
#    циклу по a це O(n²): ×10 до n дає ×100 часу.
def intersect_list(a: list[int], b: list[int]) -> list[int]:
    return [x for x in a if x in b]


# 2. Обидва set будуються всередині заміру (O(n) кожен), сам перетин — по хешах.
#    Разом O(n): ×10 до n дає ×~10 часу.
def intersect_sets(a: list[int], b: list[int]) -> list[int]:
    return list(set(a) & set(b))


# 3. Той самий comprehension, що й у варіанті 1, але x in set — пошук за хешем,
#    O(1) в середньому, як Set.has у JS. Різниця лише в типі b, і саме вона
#    дає тисячі разів. Так працює seen_ids у задачі 2: set будується один раз,
#    а перевірок на ньому багато.
def intersect_prebuilt_set(a: list[int], b_set: set[int]) -> list[int]:
    return [x for x in a if x in b_set]


# *args збирає решту аргументів у кортеж, як ...args у JS.
def measure(n: int, fn, *args) -> float:
    # Спершу коректність: швидкий неправильний алгоритм не рахується.
    # assert зникає при python -O, тому годиться для бенчмарків і тестів,
    # але не для перевірки вхідних даних — там винятки, як у задачі 2.
    result = fn(*args)
    assert len(result) == n // 2, f"{fn.__name__}: expected {n // 2}, got {len(result)}"

    # timeit приймає функцію без аргументів, тому загортаємо виклик у lambda.
    # Дані вже побудовані поза нею, тож замір бачить лише сам алгоритм.
    # number=1 обов'язковий: дефолт — мільйон прогонів на кожен repeat.
    # min, а не середнє: шум (інші процеси, кеш) лише ДОДАЄ час і ніколи не
    # віднімає, тому мінімум найближчий до справжньої вартості коду.
    return min(timeit.repeat(lambda: fn(*args), number=1, repeat=REPEAT))


def bench(n: int) -> tuple[float, float, float]:
    a, b = make_data(n)
    # set будуємо до заміру: варіант 3 міряє лише пошук. Саме тут легко
    # помилитися — якщо b перезаписати на set(b), варіант 1 теж стане швидким.
    b_set = set(b)
    return (
        measure(n, intersect_list, a, b),
        measure(n, intersect_sets, a, b),
        measure(n, intersect_prebuilt_set, a, b_set),
    )


def fmt_time(seconds: float) -> str:
    if seconds >= 1:
        return f"{seconds:.2f} s"
    if seconds >= 1e-3:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds * 1e6:.1f} µs"


def main() -> None:
    # list/set — у скільки разів варіант 1 повільніший за варіант 2.
    # list x і set x — ріст часу відносно попереднього n (у 10 разів меншого).
    print(f"{'n':>9}{'list':>12}{'set & set':>12}{'in set':>12}{'list/set':>10}{'list x':>8}{'set x':>8}")
    prev = None
    for n in SIZES:
        # n друкуємо одразу, а решту рядка — після замірів, щоб довгий прогін
        # не виглядав як зависання. flush=True виштовхує текст без "\n":
        # print буферизує stdout і без нього чекав би кінця рядка.
        print(f"{n:>9,}", end="", flush=True)
        t_list, t_sets, t_prebuilt = bench(n)
        growth = (
            f"{t_list / prev[0]:>7.0f}x{t_sets / prev[1]:>7.0f}x" if prev else f"{'—':>8}{'—':>8}"
        )
        print(
            f"{fmt_time(t_list):>12}{fmt_time(t_sets):>12}{fmt_time(t_prebuilt):>12}"
            f"{t_list / t_sets:>9.0f}x{growth}"
        )
        prev = (t_list, t_sets)


if __name__ == "__main__":
    main()
