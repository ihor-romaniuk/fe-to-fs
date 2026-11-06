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

# Задача 5. Escaping, middleware, DEBUG

## Escaping

Через форму надіслано `title=<script>alert(1)</script>` (302). У списку:

```html
<h2>&lt;script&gt;alert(1)&lt;/script&gt;</h2>
```

`grep -c '&lt;script&gt;'` дає 1, `grep -c '<script>alert'` — 0. Валідація форми тут не
допомагає й не мусить: назва довша за 3 символи, тобто валідна. Захищає автоекранування
під час виводу.

Із `{{ review.title|safe }}` у HTML потрапив живий `<h2><script>alert(1)</script></h2>`
(лічильники 0 і 1), і браузер його виконає. Шаблон повернуто, знову 1 і 0. `|safe` означає
«я ручаюся, що це безпечний HTML», а дані з форми таким не є ніколи.

## RequestLogMiddleware

Клас лежить у `reviewhub/middleware.py`: він наскрізний, не про відгуки. У `MIDDLEWARE` він
стоїть одразу після `AuthenticationMiddleware`. Вивід `runserver` на POST форми:

```
-> POST /reviews/new/ user=AnonymousUser
<- /reviews/new/ 302
[06/Nov/2026 11:28:17] "POST /reviews/new/ HTTP/1.1" 302 0
```

Між `->` і `<-` працює решта ланцюжка й view. Рядок `runserver` іде останнім: сервер пише
його, коли handler уже повернув відповідь. `logger.warning`, а не `info`, бо `LOGGING` не
налаштовано: у логера `reviewhub.middleware` немає handler-ів, і в stderr його виводить лише
`logging.lastResort`, у якого поріг WARNING.

## Middleware першим у списку

```
Internal Server Error: /reviews/
Traceback (most recent call last):
  File ".venv/.../django/core/handlers/exception.py", line 56, in inner
    response = get_response(request)
  File "reviewhub/reviewhub/middleware.py", line 15, in __call__
    logger.warning("-> %s %s user=%s", request.method, request.path, request.user)
AttributeError: 'WSGIRequest' object has no attribute 'user'
```

Статус 500. `request.user` створює `AuthenticationMiddleware`, а запит до неї ще не дійшов:
наш клас тепер зовнішній шар цибулини. Кадрів у traceback лише два: обгортка
`convert_exception_to_response` (`inner`) і наш `__call__`, більше нічого не встигло
виконатись. Порядок повернуто, знову 200.

## DEBUG=0: три наслідки

| Запит | `DEBUG=1` | `DEBUG=0` |
|---|---|---|
| `/nope/` | 404, сторінка на 2,4 КБ зі списком URL-патернів і `URLconf` | 404, 179 байт: `Not Found` |
| `/static/reviews/app.css` | 200, файл | 404, той самий `Not Found` |
| `Host: evil.example` | 400, налагоджувальна сторінка `DisallowedHost` на 67 КБ | 400, 143 байти: `Bad Request (400)` |

Чому:

1. **`/nope/`.** `django/core/handlers/exception.py:65`: на `Http404` при `DEBUG` викликається
   `debug.technical_404_response()` (показує, які патерни Django перебрав), інакше
   `get_exception_response(..., 404)`, тобто шаблон `404.html` або вбудована сторінка
   `Not Found`. Відвідувачу не видно структури URL.
2. **Статика.** `django/contrib/staticfiles/management/commands/runserver.py:34`:
   `if use_static_handler and (settings.DEBUG or insecure_serving): return StaticFilesHandler(handler)`.
   При `DEBUG=1` цей обробник перехоплює `/static/` ще до middleware, і в лозі немає наших
   `->`/`<-` для CSS. При `DEBUG=0` запит іде звичайним шляхом: через middleware в URLconf,
   де `/static/` немає, тож 404. Сторінки працюють, але без стилів. У продакшні статику
   роздає веб-сервер або WhiteNoise після `collectstatic`; примусово в `runserver` — прапорець
   `--insecure`.
3. **Чужий Host.** Статус **не змінився**: 400 в обох режимах, бо `ALLOWED_HOSTS` у нас —
   явний список. Змінились тіло й лог. `exception.py:114`: на `SuspiciousOperation`
   (`DisallowedHost` — її підклас) при `DEBUG` віддається `technical_500_response(status_code=400)`
   з traceback і налаштуваннями, інакше коротка сторінка 400. `DisallowedHost` кидає вже
   `CommonMiddleware` (`request.get_host()`), до нашої middleware запит не доходить, тому
   `->`/`<-` для нього немає.

Ще один наслідок у консолі. При `DEBUG=0` зникли рядки `Not Found: /nope/` і traceback
`Invalid HTTP_HOST header`. У `DEFAULT_LOGGING` (`django/utils/log.py:39`) handler `console`
має фільтр `require_debug_true`, а помилки при `DEBUG=0` йдуть у `mail_admins`. Без
`ADMINS` і власного `LOGGING` вони не видно ніде. Для продакшну `LOGGING` треба налаштувати.

## Пастка в settings із Задачі 1

`DJANGO_ALLOWED_HOSTS=` (порожній рядок, саме так у `.env.example`) дає
`ALLOWED_HOSTS = ['']`. `os.environ.get` повертає `""`, а не значення за замовчуванням, і
`"".split(",")` дає `['']`. Такий список не порожній, тому:

- `runserver` при `DEBUG=0` не відмовляється стартувати (`runserver.py:80` перевіряє лише
  порожній список);
- при `DEBUG=1` не вмикається запасний варіант `.localhost`/`127.0.0.1`/`[::1]`;
- будь-який запит, навіть на `127.0.0.1`, дає 400 (перевірено).

Якщо скопіювати `.env.example` і заповнити лише ключ, сайт відповідатиме 400 на все.

# Задача 6. Шлях запиту

Шляхи проєкту відраховано від `day3/`. Шляхи Django (`django/...`) — від
`day3/.venv/lib/python3.12/site-packages/`, версія 6.1.3. Ознаки взято з перевірок
задач 1–5 і з прогону `curl -D -` на сервері з поточним кодом.

## GET /reviews/

1. **WSGI.** `runserver` бере `WSGI_APPLICATION` (`reviewhub/reviewhub/settings.py:74`), а
   той вказує на `application = get_wsgi_application()` (`reviewhub/reviewhub/wsgi.py:16`). На
   кожен запит викликається `WSGIHandler.__call__` (`django/core/handlers/wsgi.py:120`): він
   надсилає `request_started`, створює `WSGIRequest(environ)` (`:123`) і викликає
   `self.get_response(request)` (`:124`), тобто ланцюжок middleware
   (`django/core/handlers/base.py:142`).
   *Ознака:* `[06/Nov/2026 11:31:42] "GET /reviews/ HTTP/1.1" 200 1414` — цей рядок пише сам
   WSGI-сервер, коли відповідь уже готова.

2. **Middleware вперед, зверху вниз за `MIDDLEWARE`** (`reviewhub/reviewhub/settings.py:46`):
   - `SecurityMiddleware` (`settings.py:47`): на вході нічого, бо HTTPS-редирект вимкнено.
   - `SessionMiddleware` (`settings.py:48`): лінивий `request.session`; cookie `sessionid`
     у нас немає.
   - `CommonMiddleware` (`settings.py:49`): перевіряє Host через `request.get_host()`
     (`django/middleware/common.py:48`).
     *Ознака:* `-H 'Host: evil.example'` дав 400, і наших `->`/`<-` для нього немає (Задача 5).
   - `CsrfViewMiddleware` (`settings.py:50`): у `__call__` нічого. Перевірка відбувається
     пізніше, у `process_view` (крок 3).
   - `AuthenticationMiddleware` (`settings.py:51`): `request.user = SimpleLazyObject(...)`
     (`django/contrib/auth/middleware.py:39`).
     *Ознака:* без неї вище нашої — `AttributeError: 'WSGIRequest' object has no attribute 'user'`, 500 (Задача 5).
   - `RequestLogMiddleware` (`settings.py:52`), рядок `reviewhub/reviewhub/middleware.py:15`.
     *Ознака:* `-> GET /reviews/ user=AnonymousUser`.
   - `MessageMiddleware` (`settings.py:53`): готує `request._messages`. *Ознаки немає*:
     повідомлень ми не надсилаємо.
   - `XFrameOptionsMiddleware` (`settings.py:54`): на вході нічого.

3. **Resolver.** `_get_response()` викликає `resolve_request()`
   (`django/core/handlers/base.py:183`) з `ROOT_URLCONF = 'reviewhub.urls'`
   (`reviewhub/reviewhub/settings.py:57`). `path('reviews/', include('reviews.urls'))`
   (`reviewhub/reviewhub/urls.py:21`) відрізає `reviews/`, і залишок `""` збігається з
   `path("", views.review_list, name="review_list")` (`reviewhub/reviews/urls.py:7`). Далі цикл
   `process_view` (`django/core/handlers/base.py:186`): `CsrfViewMiddleware.process_view`
   (`django/middleware/csrf.py:414`) для GET одразу виходить (`csrf.py:425`).
   *Ознака:* при `DEBUG=1` `/nope/` віддав 404 зі списком патернів `reviews/` і `admin/`, а
   `{% url 'reviews:review_list' %}` дав `<a href="/reviews/">`.

4. **View.** `review_list` (`reviewhub/reviews/views.py:8`) рахує кількість і середнє
   (`views.py:10`, `views.py:11`) і викликає `render()` (`views.py:17`).
   *Ознака:* `4 reviews · average rating 4.0 / 5`.

5. **Template.** `render()` → `loader.render_to_string()` (`django/shortcuts.py:27`). Пошук
   іде спершу в `DIRS` (`reviewhub/reviewhub/settings.py:62`), потім в `APP_DIRS`
   (`settings.py:63`). Знайдено `reviewhub/reviews/templates/reviews/review_list.html`, у
   ньому `{% extends "base.html" %}` (`review_list.html:1`), батьківський шаблон —
   `reviewhub/templates/base.html`.
   *Ознака:* `<title>Reviews · ReviewHub</title>` (`{{ block.super }}`). Шляхи пошуку видно в
   postmortem `TemplateDoesNotExist` (Задача 2).

6. **Escaping.** Кожен `{{ ... }}` проходить `render_value_in_context()`, а та при
   `context.autoescape` повертає `conditional_escape(value)` (`django/template/base.py:1150`).
   У нас це `{{ review.title }}` (`review_list.html:17`).
   *Ознака:* `<h2>&lt;script&gt;alert(1)&lt;/script&gt;</h2>` (Задача 5).

7. **HttpResponse.** `return HttpResponse(content, content_type, status)` (`django/shortcuts.py:28`).
   *Ознака:* `HTTP/1.1 200 OK`, `Content-Type: text/html; charset=utf-8`.

8. **Middleware назад, знизу вгору:**
   - `XFrameOptionsMiddleware`: `response.headers["X-Frame-Options"] = ...`
     (`django/middleware/clickjacking.py:34`).
     *Ознака:* `X-Frame-Options: DENY`.
   - `MessageMiddleware`: повідомлень немає, *ознаки немає*.
   - `RequestLogMiddleware`: `reviewhub/reviewhub/middleware.py:17`.
     *Ознака:* `<- /reviews/ 200`.
   - `AuthenticationMiddleware`: на виході нічого.
   - `CsrfViewMiddleware.process_response` (`django/middleware/csrf.py:472`): шаблон списку не
     викликав `get_token()`.
     *Ознака:* у відповіді на `GET /reviews/` немає `Set-Cookie` (на `GET /reviews/new/` він є).
   - `CommonMiddleware.process_response` (`django/middleware/common.py:107`): 404 на шляху без
     слеша перетворюється на 301.
     *Ознака:* на `GET /reviews` наш лог пише `<- /reviews 404`, а клієнт отримує
     `301 Location: /reviews/`. Наша middleware всередині, тож бачить 404 раніше, ніж
     `CommonMiddleware` його підмінить.
   - `SessionMiddleware.process_response`: сесію читали, тому
     `patch_vary_headers(response, ("Cookie",))` (`django/contrib/sessions/middleware.py:81`).
     *Ознака:* `Vary: Cookie`. Сесію читає наш `str(request.user)` у лозі: лінивий user
     обчислюється й лізе в сесію. Перевірено test Client: без `RequestLogMiddleware`
     `Vary` немає, з нею — `Cookie`. Тобто логування зробило сторінку гіршою для кешів.
   - `SecurityMiddleware`: `X-Content-Type-Options` (`django/middleware/security.py:47`),
     `Referrer-Policy`, `Cross-Origin-Opener-Policy`.
     *Ознака:* `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`,
     `Cross-Origin-Opener-Policy: same-origin`.

9. **Назад у WSGI.** `start_response(status, response_headers)` (`django/core/handlers/wsgi.py:133`),
   потім сервер відправляє тіло й пише рядок логу з кроку 1.

## POST /reviews/new/

Кроки 1–2 ті самі. *Ознака:* `-> POST /reviews/new/ user=AnonymousUser`. Нижче лише те, що
відрізняється.

3. **Resolver.** Залишок `new/` збігається з
   `path("new/", views.review_create, name="review_create")` (`reviewhub/reviews/urls.py:8`).

3a. **[відмінність] CSRF → 403.** `CsrfViewMiddleware.process_view`
   (`django/middleware/csrf.py:414`): POST не є безпечним методом, тому викликається
   `self._check_token(request)` (`csrf.py:466`). Без cookie це
   `RejectRequest(REASON_NO_CSRF_COOKIE)` (`csrf.py:362`), далі `return self._reject(...)`
   (`csrf.py:468`): відповідь **403**, view не викликається. Поле й cookie дає
   `{% csrf_token %}` у формі (`review_form.html:9`).
   *Ознака:* у лозі `-> POST /reviews/new/ user=AnonymousUser`, потім
   `Forbidden (CSRF cookie not set.): /reviews/new/`, потім `<- /reviews/new/ 403`. Наш `->`
   стоїть **раніше** за `Forbidden`, хоча `CsrfViewMiddleware` вище в списку: `process_view`
   працює вже після всіх `__call__`, між resolver і view. А `403` повертається крізь усі
   middleware назад, тому є й наш `<-`.

4. **View.** `review_create` (`reviewhub/reviews/views.py:20`): `request.method == "POST"`
   (`views.py:21`), `ReviewForm(request.POST)` (`views.py:22`), **`form.is_valid()`**
   (`views.py:23`). Усередині — валідація полів (`max_value=5` у `reviewhub/reviews/forms.py:7`),
   `clean_title` (`forms.py:10`), потім `clean()` (`forms.py:18`).

5a. **[відмінність] Гілка помилок → 200.** `is_valid()` повертає `False`, і виконання
   доходить до `render(request, "reviews/review_form.html", {"form": form})` (`views.py:32`).
   Кроки 5–9 як у GET, але з `review_form.html`.
   *Ознака:* `HTTP/1.1 200 OK`, `<ul class="errorlist" id="id_title_error"><li>Title must be
   at least 3 characters long.`, `<- /reviews/new/ 200`.

5b. **[відмінність] Гілка redirect → 302.** `REVIEWS.append(...)` (`views.py:26`), потім
   `return redirect("reviews:review_list")` (`views.py:28`): `reverse()` дає `/reviews/`,
   відповідь — `HttpResponseRedirect`. Шаблон не рендериться. Middleware назад як у GET.
   *Ознака:* `HTTP/1.1 302 Found`, `Location: /reviews/`, `<- /reviews/new/ 302`. Далі
   браузер робить **новий** `GET /reviews/` (увесь шлях вище), і `grep -c 'Tailwind Basics'`
   дає 1.

## Три питання про settings.py — повернутися на Дні 4

1. `DATABASES` (`reviewhub/reviewhub/settings.py:80`) для Postgres: який `ENGINE`, як
   передати облікові дані з env (окремі змінні чи один `DATABASE_URL`) і що змінюють
   `CONN_MAX_AGE` та `CONN_HEALTH_CHECKS`?
2. У `settings.py` немає `DEFAULT_AUTO_FIELD`, а в `reviewhub/reviews/apps.py` немає
   `default_auto_field`. Який тип первинного ключа отримає модель `Review` і хто це вирішує?
3. `TIME_ZONE = 'UTC'` і `USE_TZ = True` (`settings.py:112`, `settings.py:116`): у якому вигляді
   Postgres зберігатиме `created_at`, у якій зоні його покаже Admin і чи варто ставити
   `'Europe/Kyiv'`?
