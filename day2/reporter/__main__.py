"""Точка входу: аргументи, налаштування logging і exit codes."""

import argparse
import json
import logging
import sys

from reporter.instrument import Timer, timer
from reporter.loading import load_courses
from reporter.rendering import print_report
from reporter.validation import split_valid

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_BAD_INPUT = 2

# Під -m __name__ цього файлу — "__main__", тому в логах саме це ім'я.
logger = logging.getLogger(__name__)


# argparse — як commander або yargs у Node: сам будує usage і -h. На помилці
# аргументів друкує usage у stderr і виходить з кодом 2. Це збігається з
# EXIT_BAD_INPUT, бо 2 для "неправильний виклик" — загальна Unix-конвенція.
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python3 -m reporter")
    parser.add_argument("path", help="файл із курсами: .json (масив) або .jsonl (рядок на курс)")
    parser.add_argument("--verbose", action="store_true", help="показати рядки DEBUG")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv[1:])

    # Єдиний basicConfig у проєкті. Модулі лише беруть свій logger і пишуть у
    # нього, а куди й що виводити, вирішується тут. Без stream= basicConfig
    # вішає на кореневий логер StreamHandler у sys.stderr, тож stdout лишається
    # для звіту. Рівень — це поріг: на INFO виклики logger.debug відкидаються.
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Формат load_courses вибирає за розширенням: .jsonl читає генератором
    # iter_lines і парсить кожен рядок окремо. Помилки в обох форматів ті самі.
    try:
        records = load_courses(args.path)
    except FileNotFoundError:
        logger.error("file not found: %s", args.path)
        return EXIT_BAD_INPUT
    except json.JSONDecodeError as e:
        logger.error("%s is not valid JSON: %s", args.path, e)
        return EXIT_BAD_INPUT

    # Декоратор міряє функцію цілком, контекстний менеджер — довільний блок.
    # Обидва варіанти взаємозамінні; тут по одному, щоб кожен працював.
    with Timer("split_valid"):
        valid = split_valid(records)
    rejected = len(records) - len(valid)
    if rejected:
        # INFO, а не WARNING: попередження — по одному на кожен запис, а це підсумок.
        logger.info("[invalid] summary: %s of %s records rejected", rejected, len(records))

    with timer("print_report"):
        print_report(args.path, len(records), valid)
    return EXIT_INVALID if rejected else EXIT_OK


# python -m reporter запускає цей файл з __name__ == "__main__". Перевірка
# потрібна, щоб import reporter.__main__ (наприклад, у тестах) не запускав main.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
