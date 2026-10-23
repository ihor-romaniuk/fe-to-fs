Вимоги, які отримав Claude Code для `report_ai.py`. Відтворені з Дня 1:
правила R1-R5, формат звіту, exit codes 0/1/2. Рішення `day1/3-report.py`
агентові не показували.

---

Напиши Python-скрипт `report_ai.py` (Python 3.12, лише стандартна бібліотека).

Запуск: `python3 report_ai.py <courses.json>`

Вхід — JSON-масив записів курсів, наприклад:

```json
{"id": 1, "title": "React Fundamentals", "author": "olena", "hours": 12, "published": true, "tags": ["frontend", "react"]}
```

## Валідація

Правила перевіряються по порядку R1 → R5; на першому порушенні запис відкидається.

- R1 `required_fields`: є всі ключі `id`, `title`, `author`, `hours`, `published`, `tags`; зайві ключі дозволені.
- R2 `types`: `id` — int, `title` — str, `author` — str, `hours` — int, `published` — bool, `tags` — list. Без приведення типів: `"6"` — не int, `true` — не int.
- R3 `id_unique_positive`: `id > 0` і не повторюється серед уже прийнятих записів.
- R4 `hours_range`: `1 <= hours <= 200`.
- R5 `non_empty_text`: `title` після `strip()` має щонайменше 3 символи, `author` після `strip()` непорожній.

Кожен невалідний запис — один рядок у stderr із назвою порушеного правила.

## Звіт

Друкується в stdout лише з валідних записів, навіть якщо є невалідні.
Групування за автором; сортування за `total_hours` спаданням, при рівності — за `author`.
`avg_hours = total_hours / courses`. Рядок `TOTAL` рахується по всіх валідних записах.
`source:` — шлях так, як його передали в аргументі.

Формат — байт у байт, приклад для `courses.json`:

```
=== COURSE REPORT ===
source: courses.json
records: 6 total, 3 valid, 3 invalid
author           courses published total_hours avg_hours
--------------------------------------------------------
olena                  2         1          20     10.00
petro                  1         1          20     20.00
--------------------------------------------------------
TOTAL                  3         2          40     13.33
```

## Exit codes

- `0` — усі записи валідні;
- `1` — є хоча б один невалідний запис (звіт однаково друкується);
- `2` — файл не існує або не є валідним JSON.
