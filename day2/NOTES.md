# Задача 4. @timed і контекстний менеджер

## Передбачення (записані до експериментів)

1. **Без `functools.wraps`.** `load_courses.__name__` стане `wrapper`, `__doc__` —
   `None`, атрибута `__wrapped__` не буде. Рядок `load_courses took … ms` у лозі
   лишиться правильним: всередині `wrapper` змінна `func` — це оригінальна функція.
2. **`ValueError` усередині `with Timer(...)`.** `__exit__` отримає
   `exc_type = ValueError` (клас, не екземпляр), `exc` — сам виняток з текстом,
   `tb` — traceback. Тривалість залогується з позначкою `raised ValueError`, а
   виняток полетить далі, бо `__exit__` повертає `None`.
3. **`ValueError` усередині `with timer(...)` (генератор із `try/finally`).**
   Виняток вилетить з `yield`, `finally` відпрацює, тривалість залогується,
   виняток полетить далі.
4. **Генератор без `finally`.** Виняток вилетить з `yield`, і код після нього не
   виконається: рядка з тривалістю не буде, файл, відкритий до `yield`,
   лишиться відкритим (`f.closed == False`). Виняток полетить далі.

## Факт

Усі чотири передбачення підтвердились. Відтворити: `.venv/bin/python experiments.py`.

1. Проблему створено навмисно: `@functools.wraps(func)` у reporter/instrument.py:19
   тимчасово закоментовано, потім файл відновлено з копії.

   ```
   $ .venv/bin/python -c "from reporter.loading import load_courses; print(load_courses.__name__)"
   wrapper                       # з wraps: load_courses
   __doc__     = None            # з wraps: 'Прочитати JSON-файл із курсами.'
   __wrapped__ = False           # з wraps: True
   log> reporter.instrument: load_courses took 0.1 ms
   ```

   Лог правильний і без `wraps`: він бере `func.__name__` із замикання. Ламається
   лише те, що бачать інші: `help()`, traceback, `__name__` у тестах і логерах.

2. ```
   __exit__: exc_type=<class 'ValueError'>
             exc=ValueError('boom'), tb=traceback
   log> reporter.instrument: demo took 0.0 ms, raised ValueError
   назовні долетів ValueError('boom'), elapsed_ms заповнено: True
   ```

   `exc_type` — саме клас. `__exit__` відпрацював раніше за `except` назовні, і
   виняток пройшов далі, бо `__exit__` повернув `None`.

3. Рядок `demo took 0.0 ms` є, `ValueError('boom')` долетів назовні: `finally`
   спрацював і не проковтнув виняток.

4. ```
   ValueError усередині with opened_without_finally
      назовні долетів ValueError('boom'), f.closed = False
   ValueError усередині with opened_with_finally
     log> experiments: /dev/null took 0.0 ms
      назовні долетів ValueError('boom'), f.closed = True
   ```

   Без `finally` код після `yield` не виконався зовсім: ні `f.close()`, ні лог.
   Файл закриється лише тоді, коли збирач сміття прибере об'єкт, і коли саме — невідомо.

Побічне спостереження: у `@timed` немає `try/finally`, тому коли `load_courses`
кидає `FileNotFoundError`, рядка `load_courses took` у `--verbose` немає. Механізм
той самий, що в п. 4: код після виклику, що впав, не виконується.
