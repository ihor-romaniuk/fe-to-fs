# Задача 1. PostgreSQL у Docker

Код далі живе в `day3/reviewhub`, тут лише нотатки Дня 4.

## Що зроблено

- `day3/reviewhub/docker-compose.yml` — сервіс `db` зі сніпета (`postgres:16`). Контейнер
  `reviewhub-db-1`, том `reviewhub_pgdata`.
- `requirements.txt`: `psycopg[binary]==3.3.9`, який тягне `psycopg-binary` і `typing_extensions`.
- `DATABASES` (`reviewhub/settings.py:81`): `ENGINE` тепер `django.db.backends.postgresql`.
  `NAME`/`USER`/`PASSWORD`/`HOST`/`PORT` беруться з `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`. Дефолти ті самі, що в compose:
  `reviewhub` ×3, `127.0.0.1`, `5432`. Назви змінних такі самі, як у самого образу `postgres`.
- `migrate` на порожній базі створив ті самі 10 таблиць, що були в SQLite (`\dt`).
  Суперюзер `admin` створений заново. `olena` і група `reviewers` з Дня 3 не переїхали, тому
  перевірка 4 Дня 3 тепер друкує 1, а не 2.
- `db.sqlite3` видалено з проєкту.

## `manage.py dbshell`

Не працює: `CommandError: You appear not to have the 'psql' program installed or on your path.`,
exit 1. `dbshell` сам до бази не підключається. Він запускає локальний клієнт `psql`
(`django/db/backends/postgresql/client.py:7`) з параметрами з `DATABASES`, а `FileNotFoundError`
перетворює на `CommandError` (`django/core/management/commands/dbshell.py:32`). На цій машині
`psql` немає (`which psql` порожньо), тому в базу ходимо через контейнер:

```bash
docker compose exec db psql -U reviewhub -d reviewhub
```

Пароль там не питають: усередині контейнера `psql` іде через unix-сокет, а для нього в
`pg_hba.conf` стоїть `trust`. Django підключається з хоста через проброшений порт. Для
контейнера це з'єднання приходить з docker-мережі й потрапляє під правило
`host all all all scram-sha-256`, тож пароль потрібен: з `POSTGRES_PASSWORD=nope` маємо
`FATAL: password authentication failed for user "reviewhub"`.

## Змінні середовища на чистій машині

| Змінна | Обов'язкова | Дефолт | Примітка |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | так | — | без неї будь-яка команда дає `ImproperlyConfigured` |
| `DJANGO_DEBUG` | ні | `0` | `1` — debug-сторінки і статика через `runserver` |
| `DJANGO_ALLOWED_HOSTS` | ні | `127.0.0.1,localhost` | порожнє значення не пускає нікого (День 3) |
| `POSTGRES_DB` | ні | `reviewhub` | |
| `POSTGRES_USER` | ні | `reviewhub` | |
| `POSTGRES_PASSWORD` | ні | `reviewhub` | |
| `POSTGRES_HOST` | ні | `127.0.0.1` | порожнє значення ламає підключення, див. нижче |
| `POSTGRES_PORT` | ні | `5432` | |

Обов'язкова лише `DJANGO_SECRET_KEY`, але за умови, що Postgres з цього compose слухає
`127.0.0.1:5432`. Якщо база інша (інший хост, CI, прод), задати треба всі п'ять `POSTGRES_*`,
і пароль має бути не дефолтний. Крім змінних, на чистій машині потрібні Docker і такий порядок
команд: `pip install -r requirements.txt` → `docker compose up -d db` → дочекатися
`pg_isready` → `migrate` → `createsuperuser`.

Перевірено через `env -i`, тобто без жодної змінної з оточення:

- лише `DJANGO_SECRET_KEY`: `showmigrations` бачить базу, усі міграції `[X]`;
- без змінних: `ImproperlyConfigured: DJANGO_SECRET_KEY is not set`;
- `POSTGRES_PORT=5433`: `check` проходить (`System check identified no issues`), бо в базу не
  ходить. `migrate` падає з `OperationalError: … port 5433 failed: … Connection refused`.
  `runserver` порт не відкриває: `check_migrations()` читає `django_migrations` раніше, ніж
  сервер почне слухати порт (`django/core/management/commands/runserver.py:137`, а `run(` — на
  `:144`). З autoreload процес лишається живим, але `curl` дає `000`;
- `POSTGRES_HOST=` (порожнє): `connection to server on socket "/tmp/.s.PGSQL.5432" failed`.
  `os.environ.get` повертає `""`, а не дефолт, і libpq сприймає порожній host як unix-сокет.
  Порожній `POSTGRES_PORT=` натомість працює, бо libpq бере 5432. Це та сама пастка, що з
  `DJANGO_ALLOWED_HOSTS` у Дні 3. Тому в `.env.example` значення `POSTGRES_*` заповнені.

Із документації образу `postgres`: `POSTGRES_DB`/`USER`/`PASSWORD` у compose застосовуються
лише при першій ініціалізації порожнього тому `pgdata`. Якщо змінити їх після першого `up`,
пароль у базі лишиться старим, доки не зробити `docker compose down -v`, а це стирає дані.

Питання 1 з Дня 3 закрите частково: `ENGINE` — `postgresql`, облікові дані — окремими
змінними. Для одного `DATABASE_URL` потрібен сторонній пакет (`dj-database-url`), бо Django
сам його не розбирає. `CONN_MAX_AGE` і `CONN_HEALTH_CHECKS` лишаються відкритими.
