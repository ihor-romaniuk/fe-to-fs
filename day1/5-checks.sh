#!/usr/bin/env bash
# Задача 5. Прогін перевірок для report.py (у цьому репо — 3-report.py).
#
# Запуск: bash day1/5-checks.sh
# Exit code 0 — усі перевірки пройшли, інакше — кількість провалених.

# -u: неоголошена змінна — помилка, а не тихий порожній рядок.
# -e НЕ вмикаємо: ненульові exit codes тут очікувані, ми їх перевіряємо.
set -u

# Переходимо в теку скрипта, щоб відносні шляхи до json працювали
# незалежно від того, звідки його запустили.
cd "$(dirname "$0")"

REPORT=3-report.py
failed=0

ok()   { echo "  OK    $1"; }
fail() { echo "  FAIL  $1"; failed=$((failed + 1)); }


# 1. Exit codes — контракт скрипта з shell і CI.
#    $? — код останньої команди. Читати одразу: наступна команда його перезапише.
echo "1) exit codes"
expect_exit() {
    python3 "$REPORT" "$1" >/dev/null 2>&1
    local code=$?
    if [ "$code" -eq "$2" ]; then ok "$1 -> $code"; else fail "$1 -> $code, expected $2"; fi
}
expect_exit courses.json 1
expect_exit courses_valid.json 0
expect_exit broken.json 2


# 2. Звіт із задачі 3 байт у байт. Exit code конвеєра — це код ОСТАННЬОЇ
#    команди, тобто diff: 0 — файли однакові.
echo "2) diff звіту"
if out=$(python3 "$REPORT" courses.json 2>/dev/null | diff -u expected_report.txt -); then
    ok "stdout == expected_report.txt"
else
    fail "stdout != expected_report.txt"
    echo "$out"
fi


# 3. Жодних "ловлю все". except: і except Exception ковтають і баги в коді
#    (KeyError, TypeError) — скрипт мовчки бреше замість впасти. Голий
#    except: ще й ловить Ctrl+C. grep повертає 1, коли збігів немає, — тут
#    це і є успіх.
echo "3) немає except: / except Exception"
if matches=$(grep -n 'except Exception\|except:' "$REPORT"); then
    fail "знайдено:"
    echo "$matches"
else
    ok "grep порожній"
fi


# 4. Анотація результату (->) у ключових функціях. Перевірка грепом
#    розрахована на однорядкові сигнатури — у цьому файлі вони всі такі.
echo "4) -> у сигнатурах"
for fn in load_courses validate_course aggregate render_report; do
    line=$(grep -E "^def $fn\(" "$REPORT")
    if [ -z "$line" ]; then
        fail "$fn: не знайдено"
    elif [[ "$line" == *"->"* ]]; then
        ok "$line"
    else
        fail "$fn: немає ->"
    fi
done


# 5. Дубль id=1 в кінці courses_dup.json. Сам запис валідний за R1, R2, R4 і R5,
#    тому падає саме на R3 і не потрапляє в агрегати.
#    2>&1 >/dev/null — лише stderr: спершу stderr іде туди, куди зараз stdout
#    (у змінну), потім stdout — у /dev/null. Навпаки сховали б обидва.
echo "5) courses_dup.json"
err_base=$(python3 "$REPORT" courses.json 2>&1 >/dev/null)
err_dup=$(python3 "$REPORT" courses_dup.json 2>&1 >/dev/null)
# grep -c друкує 0 і повертає 1, коли збігів немає; || true гасить цей код.
dup_base=$(echo "$err_base" | grep -c 'rule=id_unique_positive' || true)
dup_new=$(echo "$err_dup" | grep -c 'rule=id_unique_positive' || true)
if [ $((dup_new - dup_base)) -eq 1 ]; then
    ok "рівно один новий рядок: $(echo "$err_dup" | grep 'rule=id_unique_positive')"
else
    fail "нових рядків rule=id_unique_positive: $((dup_new - dup_base)), expected 1"
fi

# Рядок source: відрізняється за визначенням — це інший файл, тому його
# прибираємо з обох звітів. Решта різниці має бути лише в records:.
# <(...) — підстановка процесу: diff бачить вивід команди як файл.
report_diff=$(diff \
    <(python3 "$REPORT" courses.json 2>/dev/null | grep -v '^source:') \
    <(python3 "$REPORT" courses_dup.json 2>/dev/null | grep -v '^source:'))
changed=$(echo "$report_diff" | grep '^[<>]')
if [ -n "$changed" ] && ! echo "$changed" | grep -qv '^[<>] records:'; then
    ok "у звіті змінився лише records:"
    echo "$changed" | sed 's/^/          /'
else
    fail "звіт змінився не лише в records:"
    echo "$report_diff"
fi


echo
if [ "$failed" -eq 0 ]; then echo "усі перевірки пройшли"; else echo "провалено: $failed"; fi
exit "$failed"
