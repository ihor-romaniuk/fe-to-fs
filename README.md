# fe-to-fs

Як перевірити результати. Одна задача — один коміт: `git log --oneline`.

## День 1

```bash
cd day1
python3 1-repl-warmup.py  # 1. вирази і результати; очікуване — у коментарях скрипта
bash 5-checks.sh          # 2, 3, 5. exit codes, diff звіту, дубль id; кінець: "усі перевірки пройшли"
python3 4-bench.py        # 4. list проти set, кілька хвилин: list росте ~x100 на кожні x10, set ~x10
```

## День 2

```bash
cd day2
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # один раз
source .venv/bin/activate

# 1. Мій звіт і звіт Claude Code: stdout однаковий (порожній diff); деталі — 1-ai-comparison/NOTES.md
diff <(python3 ../day1/3-report.py ../day1/courses.json 2>/dev/null) \
     <(python3 1-ai-comparison/report_ai.py ../day1/courses.json 2>/dev/null)

# 2. Пакет reporter: звіт байт у байт (порожній diff), exit 1, ruff без зауважень
python3 -m reporter courses.json 2>/dev/null | diff expected_report.txt -
python3 -m reporter courses.json >/dev/null 2>&1; echo $?            # 1
ruff check . && ruff format --check .

# 3. logging: у stderr рівно 3 WARNING
python3 -m reporter courses.json 2>&1 >/dev/null | grep -c WARNING   # 3

# 4. @timed і Timer: рядки "... took N ms"; передбачення з NOTES.md
python3 -m reporter courses.json --verbose 2>&1 >/dev/null | grep took
python3 experiments.py

# 5. Генератор: звіти .json і .jsonl різняться лише рядком source:
diff <(python3 -m reporter courses.json 2>/dev/null) <(python3 -m reporter courses.jsonl 2>/dev/null)
python3 bench_mem.py                                                 # readlines > 10 MB, генератор < 1 MB

# 6. pdb: breakpoint() прибрано (порожній вивід); сесії, `w`, порядок виконання — NOTES.md
grep -rn 'breakpoint()' reporter/
```

## День 3

```bash
cd day3
python3 -m venv .venv && .venv/bin/pip install -r reviewhub/requirements.txt   # один раз
source .venv/bin/activate
cd reviewhub
printf 'DJANGO_SECRET_KEY=%s\nDJANGO_DEBUG=1\n' \
  "$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')" > .env    # один раз
set -a; . ./.env; set +a                                             # у кожному новому терміналі
python3 manage.py migrate
python3 manage.py runserver & sleep 2                      # для curl нижче; наприкінці kill %1

# 1. Каркас reviewhub, settings з env; незрозумілі блоки settings.py — ../NOTES.md
python3 manage.py check                                    # System check identified no issues
env -u DJANGO_SECRET_KEY python3 manage.py check; echo $?  # ImproperlyConfigured …, 1
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/reviews/   # 200
grep -rn 'django-insecure' .                               # порожньо

# 2. Список на шаблонах; {% empty %} і TemplateDoesNotExist — ../NOTES.md
curl -s http://127.0.0.1:8000/reviews/ | grep -o '<li>' | wc -l   # 4 = len(REVIEWS); з REVIEWS = [] — 1
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/static/reviews/app.css   # 200, лише з DJANGO_DEBUG=1

kill %1
```
