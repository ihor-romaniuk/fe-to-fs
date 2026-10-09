"""Задача 2. Скрипт report.py: читання і валідація.

Запуск: python3 day1/2-report.py day1/courses.json
"""

import json
import sys

# Exit code — контракт з тим, хто запускає скрипт (shell, CI, cron):
# 0 — успіх, будь-що інше — збій, а конкретне число каже, який саме.
EXIT_OK = 0
EXIT_INVALID = 1
EXIT_BAD_INPUT = 2

# Схема запису: поле -> тип. dict зберігає порядок вставки, тому ці ключі
# водночас і список обов'язкових полів для R1, і порядок перевірок у R2.
FIELD_TYPES = {
    "id": int,
    "title": str,
    "author": str,
    "hours": int,
    "published": bool,
    "tags": list,
}

HOURS_MIN, HOURS_MAX = 1, 200
TITLE_MIN_LEN = 3


# Власний exception — звичайний клас-нащадок Exception (аналог extends Error
# у JS). Окрім тексту, він несе поля: хто ловить, бере e.rule і e.field,
# а не парсить рядок повідомлення. За PEP 8 імена винятків закінчуються на Error.
class ValidationError(Exception):
    def __init__(self, rule: str, field: str, detail: str):
        # Текст для str(e) і traceback, якщо виняток ніхто не зловить.
        super().__init__(f"rule={rule} field={field}: {detail}")
        self.rule = rule
        self.field = field
        self.detail = detail


# R1. Перевіряємо лише наявність ключів, зайві не заважають: формат може
#     розширюватися, і старий валідатор від цього не ламається.
def check_required_fields(record: dict) -> None:
    for field in FIELD_TYPES:
        if field not in record:
            raise ValidationError("required_fields", field, "missing")


# R2. Виняток із правила задачі 1: тут type(v) is T, а не isinstance. bool —
#     підклас int, тож isinstance(True, int) пропустив би "hours": true.
#     JSON дає лише точні вбудовані типи, тому type(...) is безпечний для всіх
#     полів. Приведення немає: "6" лишається str, хоч і схожий на число.
def check_types(record: dict) -> None:
    for field, expected in FIELD_TYPES.items():
        value = record[field]
        if type(value) is not expected:
            # !r — те саме, що repr(value): рядок виходить у лапках, і видно
            # різницю між "6" та 6. str(value) в обох випадках показав би 6.
            raise ValidationError(
                "types",
                field,
                f"expected {expected.__name__}, got {type(value).__name__} ({value!r})",
            )


# R3. set: in перевіряє хеш за O(1), а у списку — перебором за O(n). Аналог
#     Set.has у JS. Функція лише ЧИТАЄ seen_ids, додає туди id виклик у main.
#     record_id, а не id: id — вбудована функція, її не варто затіняти.
def check_id_unique_positive(record: dict, seen_ids: set[int]) -> None:
    record_id = record["id"]
    if record_id <= 0:
        raise ValidationError("id_unique_positive", "id", f"expected > 0, got {record_id}")
    if record_id in seen_ids:
        raise ValidationError("id_unique_positive", "id", f"duplicate id {record_id}")


# R4. Ланцюжкове порівняння: a <= h <= b означає (a <= h) and (h <= b).
#     У JS той самий запис — баг: (1 <= h) дає true, а true <= 200 завжди true.
def check_hours_range(record: dict) -> None:
    hours = record["hours"]
    if not HOURS_MIN <= hours <= HOURS_MAX:
        raise ValidationError(
            "hours_range", "hours", f"expected {HOURS_MIN}..{HOURS_MAX}, got {hours}"
        )


# R5. strip() — аналог trim(): "   " формально непорожній, але змісту не має.
#     Порожній рядок falsy, як і в JS, тому not author.strip() значить "порожньо".
#     Групувати авторів будемо за author.strip().lower(), щоб "Olena" і "olena "
#     не стали двома авторами; тут лише гарантуємо, що цей ключ непорожній.
def check_non_empty_text(record: dict) -> None:
    title = record["title"]
    if len(title.strip()) < TITLE_MIN_LEN:
        raise ValidationError(
            "non_empty_text", "title", f"expected >= {TITLE_MIN_LEN} chars, got {title!r}"
        )
    author = record["author"]
    if not author.strip():
        raise ValidationError("non_empty_text", "author", f"expected non-empty, got {author!r}")


# Порядок правил — не косметика, кожне спирається на попередні. R2 читає
# record[field] без KeyError, бо R1 гарантував ключі. R3 і R4 порівнюють
# числа, бо R2 гарантував int: "6" <= 0 у Python — TypeError, а не тихе
# приведення, як у JS. R5 викликає .strip(), бо R2 гарантував str.
# raise обриває функцію на першому порушенні, решта правил не виконується.
def validate_record(record: dict, seen_ids: set[int]) -> None:
    check_required_fields(record)
    check_types(record)
    check_id_unique_positive(record, seen_ids)
    check_hours_range(record)
    check_non_empty_text(record)


def main(argv: list[str]) -> int:
    # argv[0] — ім'я скрипта, аргументи йдуть з argv[1]
    # (як process.argv.slice(2) у Node).
    if len(argv) != 2:
        print(f"usage: python3 {argv[0]} <courses.json>", file=sys.stderr)
        return EXIT_BAD_INPUT
    path = argv[1]

    # with закриває файл навіть при винятку, як try/finally. encoding вказуємо
    # явно: дефолт залежить від локалі ОС, і на Windows це не UTF-8.
    # Ловимо лише очікувані збої вводу й перетворюємо їх на один людський рядок.
    # Баг у коді хай падає з traceback: його треба бачити, а не ховати.
    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return EXIT_BAD_INPUT
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        return EXIT_BAD_INPUT

    # set() — порожня множина. {} — це порожній dict, а не set.
    seen_ids: set[int] = set()
    rejected = 0

    # enumerate дає пари (індекс, елемент), як arr.forEach((x, i) => ...).
    for index, record in enumerate(records):
        try:
            validate_record(record, seen_ids)
        except ValidationError as e:
            rejected += 1
            # .get, а не [], бо відсутній id тут — очікуваний випадок (R1).
            # stderr — для діагностики, stdout лишаємо під дані звіту.
            # Це як console.error проти console.log.
            print(
                f"[invalid] index={index} id={record.get('id', '?')} "
                f"rule={e.rule} field={e.field}: {e.detail}",
                file=sys.stderr,
            )
        else:
            # else спрацьовує, лише якщо try пройшов без винятку. Відкинутий
            # запис для звіту не існує, тож його id не займаємо: інакше валідний
            # запис з тим самим id нижче став би "дублікатом" сміття.
            seen_ids.add(record["id"])

    if rejected:
        print(f"[invalid] summary: {rejected} of {len(records)} records rejected", file=sys.stderr)
        return EXIT_INVALID
    return EXIT_OK


# Блок виконується лише при запуску файлу як скрипта, а не при import.
# sys.exit передає код операційній системі, як process.exit(code) у Node.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
