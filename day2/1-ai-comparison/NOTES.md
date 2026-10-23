# День 2

## Задача 1. Свій report.py проти варіанта Claude Code

Мій варіант — `day1/3-report.py`, варіант Claude Code — `day2/1-ai-comparison/report_ai.py`.
Вимоги, які він отримав, лежать у `day2/1-ai-comparison/ai-prompt.md`; мого коду він не бачив.

1. **Структура функцій.** report_ai зберігає правила як дані: таблиця `RULES`
   (day2/1-ai-comparison/report_ai.py:123-129) і цикл `for … else` по ній (day2/1-ai-comparison/report_ai.py:151-159).
   Через це всі п'ять перевірок мають однакову сигнатуру `(record, accepted_ids)`, і
   чотири з них приймають `accepted_ids`, хоча не використовують його
   (day2/1-ai-comparison/report_ai.py:84, 91, 108, 115). У мене `validate_course` викликає перевірки
   явно (day1/3-report.py:112-117), і `seen_ids` отримує лише R3 (day1/3-report.py:83).
   Агрегацію report_ai робить усередині `render_report` (day2/1-ai-comparison/report_ai.py:167-174), а
   в мене вона винесена в `make_stats`/`aggregate` (day1/3-report.py:160-185), і
   `render_report` лише форматує.

2. **Обробка помилок.** У report_ai невалідний запис — це значення, яке повертає функція:
   правило повертає `str | None`, а цикл збирає `Violation` у список
   (day2/1-ai-comparison/report_ai.py:46-56, 153-155). У мене правило кидає `ValidationError` з
   `rule`/`field`/`detail`, а `split_valid` його ловить (day1/3-report.py:55-60, 126-133).
   Помилки файлу report_ai зводить до одного `InputError` прямо в `load_records`:
   зокрема `OSError` і JSON, який не є масивом (day2/1-ai-comparison/report_ai.py:132-144). У мене
   `main` ловить лише `FileNotFoundError` і `JSONDecodeError` (day1/3-report.py:221-228).
   Тому тека або JSON-об'єкт замість масиву дають у мене traceback і exit 1 (той самий
   код, що й «є невалідні записи»), а в report_ai — повідомлення і exit 2.

3. **Типи.** У report_ai вхід до R1 позначений `Any` (day2/1-ai-comparison/report_ai.py:48, 84),
   `check_required_fields` спершу перевіряє `isinstance(record, dict)`
   (day2/1-ai-comparison/report_ai.py:85), а аліас `Rule` фіксує сигнатуру всіх правил
   (day2/1-ai-comparison/report_ai.py:81). У мене `record: dict` з першої перевірки
   (day1/3-report.py:64), хоча JSON може дати що завгодно, а `FIELD_TYPES` без анотації
   (day1/3-report.py:16). `AuthorStats` у report_ai — змінний накопичувач з методом
   `add` і `avg_hours` як `@property` (day2/1-ai-comparison/report_ai.py:59-72). У мене це готовий
   знімок, де `avg_hours` уже пораховано і збережено в полі (day1/3-report.py:41-47).

4. **Де report_ai гірший: автор не нормалізується при групуванні.**
   `by_author.setdefault(record["author"], …)` групує за сирим рядком
   (day2/1-ai-comparison/report_ai.py:171), хоча R5 у тому самому файлі вважає пробіли незначущими
   (`record["author"].strip()`, day2/1-ai-comparison/report_ai.py:118). Тому `"olena"` і `"Olena "`
   тихо стають двома авторами: два рядки у звіті, exit 0, жодного слова в stderr.
   У мене ключ групування — `author_key` зі `strip().lower()`
   (day1/3-report.py:142-143, 155), і ці записи зливаються в один рядок `olena`.
   На courses.json різниці не видно, бо там автори вже чисті.

### Прогін на courses.json

```
$ cd day1
$ diff <(python3 3-report.py courses.json 2>&1) <(python3 ../day2/1-ai-comparison/report_ai.py courses.json 2>&1)
1,4c1,3
< [invalid] index=3 id=4 rule=types field=hours: expected int, got str ('6')
< [invalid] index=4 id=5 rule=required_fields field=author: missing
< [invalid] index=5 id=6 rule=hours_range field=hours: expected 1..200, got -4
< [invalid] summary: 3 of 6 records rejected
---
> invalid record #4 (id=4): types: hours must be int, got str
> invalid record #5 (id=5): required_fields: missing author
> invalid record #6 (id=6): hours_range: hours must be between 1 and 200, got -4
```

stdout однаковий байт у байт, exit code 1 в обох. Відрізняється лише stderr: у мене
індекс рахується з 0, формат `key=value`, значення виводиться через `repr` (`'6'`) і є
підсумковий рядок. У report_ai позиція рахується з 1 (`#4`), немає `field=`, самого
значення і підсумку, тож `grep 'rule=id_unique_positive'` з `day1/5-checks.sh` на ньому
нічого б не знайшов. Exit codes збігаються також на courses_valid.json (0),
courses_dup.json (1), broken.json (2) і неіснуючому файлі (2).
