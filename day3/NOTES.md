# Задача 1. settings.py зверху вниз

Пройдено весь `reviewhub/reviewhub/settings.py` (Django 6.1.3). Без питань, бо пояснено в
туторіалі або змінено сьогодні: `BASE_DIR`, `DEBUG`, `INSTALLED_APPS` (сам список),
`ROOT_URLCONF`, `TEMPLATES` → `APP_DIRS`, `DATABASES` (файл `BASE_DIR / 'db.sqlite3'`),
`LANGUAGE_CODE`, `TIME_ZONE`.

Незрозумілі блоки: питання і що знайшлося в документації та коді Django.

1. **`SECRET_KEY` — навіщо він.** Ним підписуються сесії, CSRF-токени, посилання для скидання
   пароля, `django.core.signing`. Якщо ключ витече, сесію можна підробити. Якщо його змінити,
   усі активні сесії й посилання стануть недійсними. Тому ключ береться з env, а не з git.

2. **`ALLOWED_HOSTS`.** Захищає від підробленого заголовка `Host`: на запит з чужим `Host`
   Django відповідає 400 (перевірено: `curl -H 'Host: evil.com' …` → 400). Якщо список
   порожній і `DEBUG=True`, Django сам пускає `.localhost`, `127.0.0.1`, `[::1]`
   (`django/http/request.py`). Якщо `DEBUG=False`, порожній список не пускає нікого.

3. **Шість `django.contrib.*` в `INSTALLED_APPS`.**
   - `admin` — адмінка на `/admin/`;
   - `auth` — користувачі, групи, права;
   - `contenttypes` — реєстр усіх моделей; на нього спираються права в `auth` і `admin`;
   - `sessions` — сесії, що зберігаються на сервері (у cookie лише id сесії);
   - `messages` — одноразові flash-повідомлення між запитами;
   - `staticfiles` — CSS, JS, картинки: пошук у `<app>/static/` і `collectstatic`.

   Сьогоднішній `migrate` створив таблиці саме для них.

4. **`MIDDLEWARE`.** Це обгортки навколо кожного запиту, як у Express/Koa: запит проходить
   список зверху вниз, відповідь — знизу вгору. Порядок важливий: `AuthenticationMiddleware`
   стоїть після `SessionMiddleware`, бо `request.user` береться із сесії.
   - `SecurityMiddleware` — заголовки безпеки (`X-Content-Type-Options: nosniff`,
     `Referrer-Policy`, `Cross-Origin-Opener-Policy`) і редирект на HTTPS, якщо він увімкнений;
   - `SessionMiddleware` — `request.session`;
   - `CommonMiddleware` — `APPEND_SLASH`: `/reviews` → 301 на `/reviews/` (перевірено);
   - `CsrfViewMiddleware` — відхиляє POST без CSRF-токена;
   - `AuthenticationMiddleware` — `request.user`;
   - `MessageMiddleware` — `messages`;
   - `XFrameOptionsMiddleware` — `X-Frame-Options: DENY`: сайт не можна вбудувати в
     `<iframe>` (захист від clickjacking).

5. **`TEMPLATES` → `DIRS` і `context_processors`.** `DIRS` — додаткові папки шаблонів поза
   app-ами, наприклад спільний `templates/base.html` на рівні проєкту. Context processors
   додають змінні в контекст кожного шаблону, що рендериться з `request` (`render()` так
   робить). Тому в шаблоні є змінні, яких view не передавав: `{{ request }}`, `{{ user }}`,
   `{{ perms }}`, `{{ messages }}`.

6. **`WSGI_APPLICATION`, `wsgi.py`, `asgi.py`.** WSGI — стандартний інтерфейс між веб-сервером
   і Python-застосунком: `runserver` бере об'єкт з `WSGI_APPLICATION`, у продакшні це робить
   `gunicorn reviewhub.wsgi`. ASGI — асинхронний аналог (async views, WebSocket), його
   запускають через uvicorn/daphne.

7. **`AUTH_PASSWORD_VALIDATORS`.** Правила для паролів: пароль не схожий на username чи email,
   має щонайменше 8 символів, його немає в списку ~20 000 поширених, він не складається лише з
   цифр. Діють у `createsuperuser`, `changepassword` і формах зміни пароля. **Не** діють у
   `User.objects.create_user()` і `set_password()`.

8. **`USE_I18N`, `USE_TZ`.** `USE_I18N` вмикає переклади (`gettext`, `{% translate %}`).
   `USE_TZ=True` означає, що дати в БД зберігаються в UTC як aware-`datetime`, а в шаблонах
   переводяться в `TIME_ZONE`. Наслідок для коду: `django.utils.timezone.now()`, а не
   `datetime.now()`, бо naive-дата при збереженні дасть `RuntimeWarning`.

9. **`STATIC_URL = 'static/'`.** Це префікс URL для статики (`{% static 'x.css' %}` →
   `/static/x.css`). `runserver` роздає статику лише при `DEBUG=True`. У нас `DEBUG` за
   замовчуванням `"0"`, тому без `.env` адмінка буде без стилів. Для продакшну потрібні
   `STATIC_ROOT` і `collectstatic`, а роздає файли веб-сервер або WhiteNoise.

10. **`MAILERS`** — нове в Django 6.1, у туторіалі цього блоку немає. Іменовані поштові
    з'єднання, як аліаси в `DATABASES`. Замінюють `EMAIL_BACKEND` та `EMAIL_*`, які тепер
    deprecated (`django/core/mail/deprecation.py`). `console.EmailBackend` нічого не надсилає,
    а друкує лист у stdout `runserver`.
