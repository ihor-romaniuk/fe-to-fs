"""Звіт для stdout."""

from reporter.aggregation import AuthorStats, aggregate, make_stats

# Формат таблиці взятий готовим із завдання: пробіли значущі, їх звіряє diff.
# {x:<16} — вліво в полі ширини 16, {x:>8} — вправо (як padEnd/padStart у JS),
# .2f — два знаки після коми (як toFixed(2)).
HEADER = f"{'author':<16}{'courses':>8}{'published':>10}{'total_hours':>12}{'avg_hours':>10}"
SEP = "-" * 56


def render_row(s: AuthorStats) -> str:
    return f"{s.author:<16}{s.courses:>8}{s.published:>10}{s.total_hours:>12}{s.avg_hours:>10.2f}"


def render_report(source: str, total: int, valid: list[dict]) -> str:
    # TOTAL рахуємо по сирих записах, а не по рядках авторів: 40 / 3 = 13.33,
    # а не середнє авторських середніх (10 + 20) / 2 = 15.00.
    lines = [
        "=== COURSE REPORT ===",
        f"source: {source}",
        f"records: {total} total, {len(valid)} valid, {total - len(valid)} invalid",
        HEADER,
        SEP,
        *(render_row(s) for s in aggregate(valid)),
        SEP,
        render_row(make_stats("TOTAL", valid)),
    ]
    return "\n".join(lines)


# Єдиний print у пакеті. Таблиця — це дані, результат програми: її
# перенаправляють у файл або diff. Лог — розповідь про те, як програма
# працювала; він іде в stderr через logging, тому 2>/dev/null лишає рівно звіт.
def print_report(source: str, total: int, valid: list[dict]) -> None:
    print(render_report(source, total, valid))
