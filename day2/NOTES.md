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

# Задача 6. Дебагер: breakpoint() і pdb

Тимчасові `breakpoint()` стояли в трьох місцях, у коміті їх немає:

- `reporter/instrument.py`, `wrapper` у `@timed` — перед `result = func(*args, **kwargs)`;
- `reporter/instrument.py`, `Timer.__exit__` — першим рядком;
- `reporter/reading.py`, `iter_lines` — перед `with open(...)`.

Номери рядків у виводі нижче — разом із цими вставками: в `instrument.py` і `reading.py`
вони на 1–2 більші, ніж у коді зараз, в інших файлах збігаються. Шляхи скорочено до `reporter/...`. Команди йшли в stdin, як у сніпеті
(`printf 'w\nl\n...' | python3 -m reporter courses.json`); у транскриптах кожну
команду дописано після її `(Pdb)`.

## Порядок виконання (факт)

**wrapper до → тіло функції → wrapper після:**

```
> reporter/instrument.py(25)wrapper()
-> result = func(*args, **kwargs)              # wrapper до: start уже порахований
(Pdb) s
--Call--
> reporter/loading.py(15)load_courses()
-> @timed                                      # тіло функції
(Pdb) n                                        # ... (18) logger.debug, (19) if, (21) with,
                                               # (22) return json.load(f), знову (21) with
--Return--
> reporter/loading.py(21)load_courses()->[{'author': 'olena', 'hours': 12, ...}, ...]
(Pdb) n
> reporter/instrument.py(26)wrapper()
-> logger.debug("%s took %.1f ms", ...)        # wrapper після
(Pdb) p result[0]["title"]
'React Fundamentals'
```

**`__enter__` → тіло with → `__exit__`** (точку в `__enter__` поставлено командою
`b Timer.__enter__` з першої зупинки, без правки коду):

```
> reporter/instrument.py(42)__enter__()
-> self.start = time.perf_counter()
(Pdb) pp vars(self)
{'elapsed_ms': 0.0, 'name': 'split_valid', 'start': 0.0}
(Pdb) c
WARNING reporter.validation: [invalid] index=3 id=4 rule=types ...   # тіло with: split_valid
WARNING reporter.validation: [invalid] index=4 id=5 rule=required_fields ...
WARNING reporter.validation: [invalid] index=5 id=6 rule=hours_range ...
> reporter/instrument.py(55)__exit__()
-> self.elapsed_ms = (time.perf_counter() - self.start) * 1000
(Pdb) p exc_type
None
(Pdb) pp vars(self)
{'elapsed_ms': 0.0, 'name': 'split_valid', 'start': 258630.131603375}
(Pdb) n
> reporter/instrument.py(56)__exit__()
-> if exc_type is None:
(Pdb) p self.elapsed_ms
0.6875410035718232
(Pdb) n
> reporter/instrument.py(57)__exit__()
-> logger.debug("%s took %.1f ms", self.name, self.elapsed_ms)
(Pdb) n
--Return--
> reporter/instrument.py(57)__exit__()->None
(Pdb) s
> reporter/__main__.py(58)main()
-> rejected = len(records) - len(valid)        # перший рядок після блока with
```

Усі зупинки за один запуск на `courses.jsonl`: wrapper (`load_courses`) → `iter_lines` →
`__exit__` (`split_valid`) → wrapper (`aggregate`).

## `w` у декораторі

Перша зупинка, `load_courses`:

```
(Pdb) w
  <frozen runpy>(198)_run_module_as_main()
  <frozen runpy>(88)_run_code()
  reporter/__main__.py(71)<module>()
-> sys.exit(main(sys.argv))
  reporter/__main__.py(46)main()
-> records = load_courses(args.path)
> reporter/instrument.py(25)wrapper()
-> result = func(*args, **kwargs)
```

Друга, `aggregate`: та сама верхівка, далі
`__main__.py(64) main` → `rendering.py(36) print_report` → `rendering.py(25) render_report` →
`instrument.py(25) wrapper`.

- Нагорі найстаріший кадр, внизу зі стрілкою `>` поточний — як у traceback і навпаки
  до Call Stack у DevTools. Два кадри `runpy` — це `python -m`, який запускає `__main__.py`.
- Кадр зветься `wrapper()`, хоча `functools.wraps` на місці. `wraps` копіює `__name__` і
  `__doc__` на об'єкт функції, а pdb і traceback беруть ім'я з об'єкта коду:
  `load_courses.__name__ == "load_courses"`, але `load_courses.__code__.co_name == "wrapper"`.
  Уточнення до задачі 4: traceback показує кадри `wrapper` і `load_courses` однаково з
  `wraps` і без нього. `wraps` потрібен для `__name__`, `__doc__`, `help()` і `__wrapped__`.
- `s` у декоровану функцію зупиняється на рядку `@timed`, а не на `def`: першим рядком
  функції вважається її перший декоратор.
- `n` з `return json.load(f)` повертається на рядок `with`: перед виходом відпрацьовує
  `__exit__` файлу.

Про `__exit__`: у `w` викликач — рядок `with Timer("split_valid"):` (`__main__.py:56`), а не
останній рядок тіла. `--Return--` з `->None` — це «виняток не ковтати».

## Генератор

```
(Pdb) w
  ...
  reporter/__main__.py(46)main()
  reporter/instrument.py(25)wrapper()
  reporter/loading.py(20)load_courses()
  reporter/loading.py(31)load_jsonl()
-> return [json.loads(line) for line in iter_lines(path)]
> reporter/reading.py(19)iter_lines()
-> with open(path, encoding="utf-8") as f:
```

- Кадру `<listcomp>` немає: з Python 3.12 list comprehension вбудовується у функцію
  (PEP 709), тож генератор тягне сам `load_jsonl`.
- `n` на `yield stripped` не виходить у `load_jsonl`: наступна зупинка — `for line in f` того
  ж генератора, а `json.loads` викликача відпрацьовує між ними непомітно.
- `s` на `yield` показує передачу значення: `--Return--` з `iter_lines()->'{"id": 1, ...}'`,
  наступний `s` — уже `json/__init__.py loads()`.

## Сніпет: генератор не заходить у pdb до next()

```
$ printf 'c\nq\n' | python3 -c 'from reporter.reading import iter_lines
g = iter_lines("courses.jsonl"); print("created"); print(next(g))'
created
> reporter/reading.py(19)iter_lines()
-> with open(path, encoding="utf-8") as f:
(Pdb) {"id": 1, "title": "React Fundamentals", ...}
```

`created` іде раніше за `(Pdb)`: `iter_lines(...)` лише створив генератор, а `breakpoint()` у
тілі спрацював на `next(g)`. Після `(Pdb)` — вивід `print(next(g))`: команду `c` не видно,
бо вона прийшла з пайпа. Після `c` програма завершилась з exit 0, і `q` ніхто не прочитав.

## PYTHONBREAKPOINT=0

`breakpoint()` викликає `sys.breakpointhook()`, а той читає `PYTHONBREAKPOINT`: `0` — нічого
не робити, порожньо — `pdb.set_trace`, `module.func` — свій дебагер (наприклад `ipdb.set_trace`).

З усіма трьома `breakpoint()` у коді `PYTHONBREAKPOINT=0 python3 -m reporter courses.json`
(і `courses.jsonl`) не дав жодного `(Pdb)`: звіт той самий, exit 1. Без змінної pdb
зупинявся на першій точці. Після цього `breakpoint()` прибрано:
`grep -rn 'breakpoint()' reporter/` порожній.

## Інше

`q` — не тихий вихід: pdb кидає `bdb.BdbQuit`, програма падає з traceback і exit 1. Це той
самий код, що `EXIT_INVALID`, тож скрипт, перерваний `q`, для shell виглядає як «є невалідні
записи». Щоб дограти до кінця, потрібен `c`.
