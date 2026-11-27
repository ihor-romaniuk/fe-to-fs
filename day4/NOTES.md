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

# Задача 2. Моделі ReviewRequest і Comment

## Що зроблено

- `reviews/models.py`: `ReviewRequest` (`author`, `reviewer`, `title`, `course_url`, `description`,
  `status`, `created_at`) з `UniqueConstraint` `uniq_review_request_author_title`, і `Comment`
  (`review_request`, `author`, `body`, `created_at`). Задача назвала лише статус `OPEN`, решту
  (`in_review`, `closed`) я додав сам; змінимо, коли День 8 і День 10 задасть свої статуси.
- Admin: обидві моделі; для `ReviewRequest` є колонки, фільтр за статусом і пошук за `title`.
- `reviews/migrations/0001_initial.py`. `seed.py` створює 5 користувачів, 60 запитів і 300
  коментарів через `bulk_create`. Повторний запуск спершу видаляє всі запити, тож результат
  щоразу той самий.

## on_delete: по рядку на FK

- `ReviewRequest.author` → `PROTECT`: запит без автора не має сенсу, а стерти чужі запити разом з
  акаунтом означає втратити дані. Видалити користувача, у якого є запити, не можна: буде
  `ProtectedError` (у `user0` 72 захищені об'єкти: 12 запитів і 60 коментарів). Спершу треба
  прибрати його запити або передати іншому.
- `ReviewRequest.reviewer` → `SET_NULL`: рев'юер — лише тимчасове призначення. Якщо його видалити,
  Django робить `UPDATE … SET reviewer_id = NULL`, і запит живе далі без рев'юера. `status` при
  цьому не змінюється: запит у `in_review` залишиться без рев'юера, це треба врахувати на Дні 10.
- `Comment.review_request` → `CASCADE`: коментар без свого запиту нікому не потрібен. Видалення
  запиту видаляє і його коментарі: `(6, {'reviews.Comment': 5, 'reviews.ReviewRequest': 1})`.
- `Comment.author` → `PROTECT`: та сама причина, що й для автора запиту, бо обговорення не має
  зникати разом з акаунтом. Користувача, у якого є лише коментарі, теж не видалити:
  `ProtectedError` через `'Comment.author'`.

## Хто виконує on_delete

У базі FK створені як `FOREIGN KEY … DEFERRABLE INITIALLY DEFERRED`, без `ON DELETE`
(`sqlmigrate reviews 0001`). Правило виконує сам Django: перед `DELETE` він збирає залежні
об'єкти. SQL, перехоплений через `CaptureQueriesContext`:

- `CASCADE`: спершу `DELETE FROM "reviews_comment" WHERE "review_request_id" IN (…)`, потім
  `DELETE FROM "reviews_reviewrequest" …`;
- `SET_NULL`: `UPDATE "reviews_reviewrequest" SET "reviewer_id" = NULL WHERE "reviewer_id" IN (…)`
  перед `DELETE FROM "auth_user"`;
- `PROTECT`: лише `SELECT` і виняток, жодного `DELETE`.

Тому видалення в обхід ORM правил не знає. `DELETE FROM reviews_reviewrequest …` у `psql`
закінчується помилкою `violates foreign key constraint "reviews_comment_review_request_id_…"`.
У Django 6.1 є `DB_CASCADE` і `DB_SET_NULL` (`django/db/models/deletion.py:99`), які записують
правило в саму базу як `ON DELETE`. Тут їх не пробували.

## Індекси (`sqlmigrate reviews 0001`)

- Для кожного FK (`author_id`, `reviewer_id`, `review_request_id`, `Comment.author_id`) Django сам
  створює `CREATE INDEX`, тому `db_index=True` на `reviewer` не потрібен.
- `status` з `db_index=True` на Postgres отримує два індекси: звичайний і `_like` з
  `varchar_pattern_ops`. Другий потрібен для `LIKE 'abc%'`, тобто для `startswith`.
- `UniqueConstraint` перетворюється на `UNIQUE ("author_id", "title")`, і це теж індекс. Він
  починається з `author_id`, тож окремий індекс на `author_id` дублює його. Поки не чіпали.

## Питання 2 з Дня 3

`id` у нових таблицях має тип `bigint`, бо `DEFAULT_AUTO_FIELD` у Django 6.1 за замовчуванням
`BigAutoField` (`django/conf/global_settings.py:451`). Але `author_id` має тип `integer`. Причина:
`auth` задає власний `default_auto_field = "django.db.models.AutoField"`
(`django/contrib/auth/apps.py:14`), тому `auth_user.id` — `integer`, а FK повторює тип ключа, на
який посилається.

# Задача 3. 0001_initial і sqlmigrate

## Розбіжність з перевіркою задачі

Задача чекає 5 `CREATE INDEX` і 4 `ADD CONSTRAINT`, а у нас 6 і 5. Зайве в обох лічильниках
дає FK `Comment.author` (`PROTECT`), якого вимагає Задача 2: це індекс
`reviews_comment_author_id_536ef402` і констрейнт
`reviews_comment_author_id_536ef402_fk_auth_user_id`. Числа задачі пасують до трьох FK, а
моделі з Задачі 2 мають чотири. Модель не міняли.

## Операції в `0001_initial.py` у порядку виконання

0. `dependencies = [swappable_dependency(AUTH_USER_MODEL)]`: спершу має бути застосована
   міграція, яка створює модель користувача, бо на її таблицю посилаються FK.
1. `CreateModel ReviewRequest`: `id`, `title`, `course_url`, `description`, `status`, `created_at`,
   `author`, `reviewer`.
2. `CreateModel Comment`: `id`, `body`, `created_at`, `author`, `review_request`.
3. `AddConstraint uniq_review_request_author_title` на `reviewrequest`.

FK-поля опинилися в кінці списку, ще й за абеткою. Наприклад, у `Comment` поле `author` стоїть
перед `review_request`, хоча в `models.py` порядок навпаки. Причина така: autodetector спершу
створює модель без зв'язків, а кожен зв'язок додає окремим `AddField`, відсортувавши за
іменем (`django/db/migrations/autodetector.py:740`, `:764`). Потім оптимізатор вливає ці
`AddField` у `CreateModel`, дописуючи їх у кінець полів
(`django/db/migrations/operations/models.py:230`). Тому й у таблиці колонки `author_id` і
`reviewer_id` останні.

## Що в SQL і чому в такому порядку

- `BEGIN;` … `COMMIT;`: міграція атомарна, а Postgres уміє відкочувати DDL
  (`can_rollback_ddl = True`, `django/db/backends/postgresql/features.py:32`). `sqlmigrate`
  друкує ці рядки лише в такому разі (`django/core/management/commands/sqlmigrate.py:74`). Якщо
  міграція впаде посередині, не залишиться ні таблиць, ні індексів.
- Два `CREATE TABLE` виконуються одразу, кожен у своєму `CreateModel`.
- `ADD CONSTRAINT "uniq_review_request_author_title" UNIQUE ("author_id", "title")`: `AddConstraint`
  теж виконується одразу (`django/db/backends/base/schema.py:602`).
- 4 × `ADD CONSTRAINT … FOREIGN KEY … DEFERRABLE INITIALLY DEFERRED` і 6 × `CREATE INDEX`
  потрапляють у `deferred_sql`. Django накопичує їх під час `CreateModel` (FK у
  `base/schema.py:252`, індекси в `:544`) і виконує на виході зі schema editor, тобто
  наприкінці міграції (`base/schema.py:173`). Через це `UNIQUE` з останньої операції стоїть у
  SQL раніше за FK та індекси з першої. Вбудованого FK усередині `CREATE TABLE` бекенд Postgres у
  Django не використовує (`sql_create_inline_fk = None`), тож таблиці можуть посилатися одна на
  одну в будь-якому порядку створення.

## Індекси: ім'я і причина появи

Шаблон імені: `<таблиця>_<колонки>_<8 hex>` плюс суфікс. Хеш рахується від імен таблиці й
колонок (`base/schema.py:1543`), щоб ім'я було унікальним і вміщалося в 63 символи Postgres.

| # | Індекс | Колонка | Причина |
|---|---|---|---|
| 1 | `reviews_reviewrequest_status_63d3e3fd` | `status` | замовлений явно: `db_index=True` |
| 2 | `reviews_reviewrequest_status_63d3e3fd_like` | `status varchar_pattern_ops` | побічний: бекенд Postgres додає його для кожного `varchar`/`text` з `db_index` або `unique` (`django/db/backends/postgresql/schema.py:61`, `:83`) |
| 3 | `reviews_reviewrequest_author_id_2ea7bdf1` | `author_id` | побічний: у `ForeignKey` за замовчуванням `db_index=True` (`django/db/models/fields/related.py:1039`) |
| 4 | `reviews_reviewrequest_reviewer_id_0f796ec4` | `reviewer_id` | побічний: FK, як № 3 |
| 5 | `reviews_comment_author_id_536ef402` | `author_id` | побічний: FK, як № 3 |
| 6 | `reviews_comment_review_request_id_a40001e9` | `review_request_id` | побічний: FK, як № 3 |

**Навіщо два індекси на `status`.** Звичайний btree порівнює рядки за collation бази
(`en_US.utf8`) і годиться для `=`, `IN`, діапазонів і `ORDER BY` (документація Postgres). Для
`LIKE 'op%'` за не-C collation він не годиться. Перевірено: `status__startswith="op"` Django
перетворює на `"status"::text LIKE 'op%'`. Із `SET LOCAL enable_seqscan = off` Postgres бере
`Bitmap Index Scan on reviews_reviewrequest_status_63d3e3fd_like` з умовою
`status ~>=~ 'op' AND status ~<~ 'oq'`. Якщо в транзакції, яку потім відкотили, зробити
`DROP INDEX …_like`, план стає `Seq Scan`, хоча seq scan вимкнено. Отже, звичайний індекс для
`LIKE` не підходить.

**Навіщо індекси на FK.** Для PK і `UNIQUE` Postgres створює індекс сам, а для колонки, яка
посилається на іншу таблицю, — ні. Django створює його сам, бо за FK-колонками роблять JOIN і
фільтрують (`?review_request=<id>` на Дні 5). Крім того, `CASCADE`/`PROTECT`/`SET_NULL` шукають
саме за ними: `DELETE FROM reviews_comment WHERE review_request_id IN (…)` із Задачі 2. Тому
`db_index=True` на FK зайвий, це вже дефолт. Вимкнути індекс можна через `db_index=False`.

## Скільки індексів замовлено явно

- Серед 6 `CREATE INDEX` явно замовлений 1 (`db_index=True` на `status`). Ще 5 — побічний ефект
  типів полів: `_like` через `CharField` на Postgres і 4 FK.
- У самій базі на цих двох таблицях 9 індексів (`pg_indexes`). До шести з SQL додаються
  `uniq_review_request_author_title` (Postgres тримає `UNIQUE`-констрейнт як унікальний індекс;
  замовлений явно через `UniqueConstraint`, але це не `CREATE INDEX`) і два `_pkey` (побічний
  ефект автоматичного `id`). Разом: явно 2, побічно 7.

## `DEFERRABLE INITIALLY DEFERRED`: коли Postgres перевіряє FK

Так оголошені всі 4 FK, і Django робить це для кожного FK на Postgres
(`django/db/backends/postgresql/operations.py:151`). `DEFERRABLE` означає, що перевірку можна
відкласти, а `INITIALLY DEFERRED` — що її відкладено за замовчуванням. **Postgres перевіряє такий
FK не під час `INSERT`/`UPDATE`/`DELETE`, а на `COMMIT` транзакції.** Перевірено:

- `psql`: `BEGIN; INSERT INTO reviews_comment (…, review_request_id) VALUES (…, 999999)` дає
  `INSERT 0 1`. Помилка `violates foreign key constraint
  "reviews_comment_review_request_id_a40001e9_fk_reviews_r"` з'являється лише на `COMMIT`.
- Після `SET CONSTRAINTS ALL IMMEDIATE` у транзакції та сама помилка з'являється одразу на
  `INSERT`.
- Django без транзакції (autocommit): кожен запит — окрема транзакція з `COMMIT` одразу після
  `INSERT`, тому `Comment.objects.create(review_request_id=999999, …)` кидає `IntegrityError`
  одразу.
- Django в `transaction.atomic()`: `create()` повертає об'єкт з `id`, вкладений `atomic()`
  (savepoint) закривається без помилки. `IntegrityError` з'являється на виході із зовнішнього
  блоку, тобто на `COMMIT`. У базі нічого не лишається.

Навіщо так. Усередині транзакції рядки можна вставляти в будь-якому порядку (`loaddata` із
посиланнями вперед, циклічні FK), головне, щоб на коміті все сходилося. Ціна: помилка
з'являється далеко від рядка, який її спричинив, — наприкінці `atomic`, а не на `create()`.
`TestCase` загортає кожен тест у транзакцію, яку потім відкочує, тому сам перевіряє констрейнти
наприкінці тесту (`django/test/testcases.py:1497`). Інакше зламаний FK у тесті ніхто б не
помітив.
