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
diff <(python ../day1/3-report.py ../day1/courses.json 2>/dev/null) \
     <(python 1-ai-comparison/report_ai.py ../day1/courses.json 2>/dev/null)

# 2. Пакет reporter: звіт байт у байт (порожній diff), exit 1, ruff без зауважень
python -m reporter courses.json 2>/dev/null | diff expected_report.txt -
python -m reporter courses.json >/dev/null 2>&1; echo $?            # 1
ruff check . && ruff format --check .

# 3. logging: у stderr рівно 3 WARNING
python -m reporter courses.json 2>&1 >/dev/null | grep -c WARNING   # 3

# 4. @timed і Timer: рядки "... took N ms"; передбачення з NOTES.md
python -m reporter courses.json --verbose 2>&1 >/dev/null | grep took
python experiments.py

# 5. Генератор: звіти .json і .jsonl різняться лише рядком source:
diff <(python -m reporter courses.json 2>/dev/null) <(python -m reporter courses.jsonl 2>/dev/null)
python bench_mem.py                                                 # readlines > 10 MB, генератор < 1 MB
```
