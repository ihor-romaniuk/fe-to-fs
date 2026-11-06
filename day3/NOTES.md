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

# Задача 2. Список на Django Templates

## `{% empty %}`

Тимчасово `REVIEWS = []` у `reviews/store.py`. `runserver` перезавантажився сам, бо
змінився `.py`. Сторінка показала `0 reviews` без середньої оцінки (у view `avg_rating = None`,
у шаблоні `{% if avg_rating is not None %}`) і рівно один `<li>No reviews yet.</li>`. Дані
повернуто, знову 4 `<li>`.

## `TemplateDoesNotExist`

`base.html` перейменовано на `base.html.off`. Сторінка дала 500, а `curl -H 'Accept: text/plain'`
повернув налагоджувальну сторінку текстом. Шляхи нижче скорочено:

```
TemplateDoesNotExist at /reviews/
base.html
...
Template loader postmortem
Django tried loading these templates, in this order:

Using engine django:
    * filesystem.Loader:      reviewhub/templates/base.html (Source does not exist)
    * app_directories.Loader: .venv/.../django/contrib/admin/templates/base.html (Source does not exist)
    * app_directories.Loader: .venv/.../django/contrib/auth/templates/base.html (Source does not exist)
    * app_directories.Loader: reviewhub/reviews/templates/base.html (Source does not exist)

Template error:
In template reviewhub/reviews/templates/reviews/review_list.html, error at line 1
   1 :  {% extends "base.html" %}
```

Що з цього видно:

- Порядок пошуку такий: спершу `DIRS`, потім `templates/` app-ів у порядку `INSTALLED_APPS`.
  Перший знайдений файл виграє. Тому `DIRS` може перекрити шаблон будь-якого app-а, навіть
  адмінки, а однакові імена в різних app-ах конфліктують. Звідси й обов'язкова папка
  `reviews/` всередині `templates/`.
- У списку лише `admin`, `auth` і `reviews`: у `contenttypes`, `sessions`, `messages`,
  `staticfiles` немає папки `templates/`, і `app_directories` їх не перебирає.
- Помилка вказує на `{% extends %}` у дочірньому шаблоні, а не на view: view просив
  `reviews/review_list.html`, і цей шаблон знайшовся.

**Несподіванка: на вже запущеному сервері помилки не було.** Після перейменування
`base.html` сторінка й далі віддавала 200 зі старим вмістом. 500 з'явилось лише після
перезапуску `runserver`. А коли файл повернули, без перезапуску сервер і далі віддавав
500. 200 повернулось лише після `touch templates/base.html`. Причина в коді Django 6.1.3:

- `template/engine.py:41`: якщо `loaders` не задано, Django завжди обгортає їх у
  `cached.Loader`, і в розробці теж (так з Django 4.1). Скомпільований шаблон береться з кешу,
  тож видалення файлу непомітне.
- `template/loaders/cached.py`: кешується й промах, тобто `TemplateDoesNotExist`. Тому
  повернутий файл теж непомітний.
- Кеш скидає autoreload (`template/autoreload.py`, `template_changed` → `reset_loaders`), але
  `StatReloader` реагує лише на зростання mtime вже відомого файлу (`utils/autoreload.py`,
  `if old_time is None: continue`). Новий або видалений файл подію не породжує, а `touch`
  породжує.

Висновок: якщо шаблон перейменували, видалили чи додали, а сторінка поводиться дивно,
перезапустіть `runserver`.

# Задача 3. Форма, валідація, CSRF, redirect після POST

## Три сценарії зі сніпета

| Запит | Код | Що сталося |
|---|---|---|
| `title=Ok`, `rating=9`, з токеном | 200 | та сама форма, `errorlist` у `title` і `rating` |
| `title=Tailwind Basics`, `rating=5`, з токеном | 302 | `Location: /reviews/`, запис у `REVIEWS` |
| `title=X`, без cookie і токена | 403 | `CSRF cookie not set.` |

Після валідного POST `grep -c 'Tailwind Basics'` дав 1, після рестарту `runserver` — 0.
Будь-яка правка `.py` теж перезапускає процес і стирає додані записи. Правка шаблону лише
скидає кеш шаблонів (`template_changed` повертає `True`), тож запис її переживає: так і
сталося під час експерименту з CSRF нижче.

## Валідація (перевірено в `manage.py shell`)

- `"  ab  "` дає помилку довжини, `"  abc  "` перетворюється на `"abc"`. `CharField` обрізає
  пробіли ще до `clean_title` (`strip=True` за замовчуванням), тож явний `strip()` — страховка.
- `rating=2`: `body` із 19 символів дає помилку в `body`, із 20 — валідно. `rating=3` з
  коротким `body` теж валідно.
- `rating=1` з порожнім `body` дає лише `This field is required.`: поле, що не пройшло власну
  валідацію, відсутнє в `cleaned_data`, і `clean()` друге повідомлення не додає.
- У сценарії 1 правило з `clean()` не спрацювало, бо `rating=9` не пройшов `max_value`.
- `{{ form.as_p }}` ставить `<ul class="errorlist">` над полем, `aria-invalid="true"` і
  `aria-describedby` на input, а також HTML-атрибути `required`, `maxlength`, `min`/`max`.
  Тому в браузері `rating=9` не відправиться взагалі: браузер зупинить форму сам. Серверна
  валідація — справжній захист, а `curl` обходить браузерну й показує саме її.

## CSRF: причини 403 (сторінка 403 при `DEBUG=1`, рядок «Reason given for failure»)

| Що надіслано | Причина |
|---|---|
| ні cookie, ні токена (сценарій 3) | `CSRF cookie not set.` |
| cookie є, токена у формі немає | `CSRF token missing.` |
| cookie є, токен `xxx` | `CSRF token from POST has incorrect length.` |
| **без `{% csrf_token %}`**, новий відвідувач | `CSRF cookie not set.` |
| **без `{% csrf_token %}`**, cookie лишилась з минулого візиту | `CSRF token missing.` |

Без тега в HTML немає прихованого поля і, що менш очевидно, сервер навіть не ставить cookie
`csrftoken`: `curl -c` після GET отримав порожній jar. Тег робить дві речі: вставляє поле
`csrfmiddlewaretoken` і через `get_token()` просить middleware виставити cookie у відповіді.
`CsrfViewMiddleware` на POST порівнює токен із форми з cookie. Чужий сайт може змусити
браузер надіслати cookie, але не може прочитати її й підставити токен у форму. Тег повернуто.

# Задача 4. Admin на SQLite

## Що зроблено

- `admin` створено командою зі сніпета. Запуск `createsuperuser --noinput` бере пароль з
  `DJANGO_SUPERUSER_PASSWORD` як є: `validate_password` викликається лише в інтерактивній
  гілці (`contrib/auth/management/commands/createsuperuser.py:185` проти `:201`). Тому
  `--noinput` пропустив би й пароль `123`. `admin12345` валідатори, до речі, пропускають
  (перевірено `validate_password`).
- Через Admin створено групу `reviewers` і користувача `olena` (пароль `olena-reviews-2026`),
  а потім `olena` додано в групу. Запити ті самі, що робить браузер: логін, POST форм з
  CSRF-токеном. Форма додавання користувача не має поля груп: Admin спершу створює
  користувача й переводить на сторінку зміни, а групи вибираються вже там.
- Кожну дію Admin записав у `django_admin_log` (кнопка History на сторінці об'єкта):
  `Added` групи, `Added` користувача, `Changed Groups` користувача.

## Чому в списку лише Users і Groups

На головній `/admin/` єдиний блок — Authentication and Authorization → Groups, Users. Модель
з'являється в Admin, лише коли її зареєстровано. Серед наших `INSTALLED_APPS` це робить тільки
`django.contrib.auth` (`contrib/auth/admin.py:25` `@admin.register(Group)`, `:40`
`@admin.register(User)`). `sessions` і `contenttypes` свої моделі не реєструють. Власних
моделей ще немає; `admin.site.register` для них буде на Дні 4.

## Хто робить redirect анонімного користувача

`GET /admin/` без сесії дає `302 Location: /admin/login/?next=/admin/`. Ланцюжок у
`django/contrib/admin/sites.py`:

1. `AuthenticationMiddleware` кладе в `request.user` `AnonymousUser`.
2. `path("", wrap(self.index), name="index")` (`:276`): кожен view Admin, крім `login/`,
   обгорнуто в `wrap()` → `self.admin_view(view)`.
3. `admin_view()` → `inner()` (`:235`): `if not self.has_permission(request):`.
4. `has_permission()` (`:204`): `return request.user.is_active and request.user.is_staff`. Для
   анонімного користувача це `False`.
5. `return redirect_to_login(request.get_full_path(), reverse("admin:login", ...))` (`:244`).
6. `redirect_to_login()` у `django/contrib/auth/views.py:184` дописує `?next=/admin/` і
   повертає `HttpResponseRedirect`, тобто 302.

`login/` не обгорнуто (`path("login/", self.login, ...)`), інакше redirect ішов би по колу.
`LoginRequiredMiddleware` (з Django 5.1) тут ні до чого: її немає в `MIDDLEWARE`, Admin
перевіряє доступ сам.

## Звичайний користувач в Admin не зайде

Вхід як `olena` з правильним паролем повертає ту саму форму (200) з помилкою «Please enter
the correct username and password for a staff account». Її кидає
`AdminAuthenticationForm.confirm_login_allowed()` (`contrib/admin/forms.py:20`), коли
`not user.is_staff`. Повідомлення таке саме, як для неправильного пароля, тож не видає, що
пароль був правильний. Група `reviewers` поки без прав. Щоб працювати в Admin, потрібні
`is_staff` і права на конкретні моделі.

## Чому «останнім рядком»

З Django 5.2 `manage.py shell` сам імпортує моделі й першим рядком друкує
`12 objects imported automatically (use -v 2 for details).`, а вже потім результат `-c`.
