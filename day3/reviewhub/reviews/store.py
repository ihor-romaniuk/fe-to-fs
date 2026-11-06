from datetime import UTC, datetime

# Тимчасове сховище в пам'яті процесу, до моделей (День 4). Кожен процес сервера
# має свою копію, а після перезапуску все повертається до цього списку.
REVIEWS = [
    {
        "title": "Two Scoops of Django",
        "author": "olena",
        "rating": 5,
        "body": (
            "Practical, opinionated and still relevant. The chapters on settings "
            "and project layout alone saved me a week of trial and error."
        ),
        "created_at": datetime(2026, 11, 3, 9, 30, tzinfo=UTC),
    },
    {
        "title": "Fluent Python",
        "author": "taras",
        "rating": 4,
        "body": (
            "Dense, but every chapter changes how you read Python code. The data "
            "model and iterators parts are the best explanation I have seen."
        ),
        "created_at": datetime(2026, 11, 4, 14, 5, tzinfo=UTC),
    },
    {
        "title": "Architecture Patterns with Python",
        "author": "iryna",
        "rating": 3,
        "body": "Good ideas, but the examples feel heavy for a small project.",
        "created_at": datetime(2026, 11, 5, 18, 45, tzinfo=UTC),
    },
    {
        "title": "Django for Beginners",
        "author": "andrii",
        "rating": 4,
        "body": (
            "A gentle start: builds several small apps end to end, explains each "
            "settings change and does not skip deployment."
        ),
        "created_at": datetime(2026, 11, 6, 8, 15, tzinfo=UTC),
    },
]
