# lift_site — сайт ООО «ЭТАЖИ»

Новичку: сначала открой `START_HERE_BEGINNER.md`.

Flask-приложение для сайта компании по обслуживанию лифтов:
- публичные страницы: `/`, `/services`, `/contacts`
- админ-панель заявок: `/admin`

## Технологии
- Python 3.10+
- Flask
- Flask-SQLAlchemy
- SQLite (по умолчанию)
- python-dotenv

## Быстрый локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Переменные окружения (.env)
Обязательные:
- `SECRET_KEY`
- `ADMIN_PASSWORD`

Основные:
- `DATABASE_URL` — опционально (по умолчанию SQLite)
- `DESIGN_VARIANT=classic|futuristic`
- `HERO_VIDEO_ENABLED=true|false` — включение видео в hero (по умолчанию `false`)
- `HERO_VIDEO_PATH=` — опционально: путь к видео hero (например `videos/hero.mp4`) или полный URL
- `HERO_IMAGE_PATH=` — опционально: фоновое изображение hero (например `uploads/hero-elevator.jpg`) или полный URL
- `FLASK_DEBUG=true|false`
- `SITE_URL=https://your-domain.ru` — канонический домен для SEO (`canonical`, `og:url`, schema)
- `STATIC_ASSETS_CACHE_MAX_AGE=604800` — TTL для CSS/JS и прочей статики (сек)
- `ARTICLE_UPLOADS_CACHE_MAX_AGE=86400` — TTL для загруженных обложек статей (сек)
- `CSP_REPORT_ONLY=true|false` — режим CSP (`Report-Only` для мягкого внедрения)
- `CSP_REPORT_URI=` — endpoint для отчетов CSP (опционально)
- `SENTRY_DSN=` — DSN Sentry для сбора ошибок (опционально)
- `SENTRY_TRACES_SAMPLE_RATE=0.0..1.0` — доля performance-трейсов
- `ADMIN_LOGIN_RATE_LIMIT_COUNT`, `ADMIN_LOGIN_RATE_LIMIT_WINDOW` — ограничение частоты POST на `/admin/login`
- `CONTACTS_RATE_LIMIT_COUNT`, `CONTACTS_RATE_LIMIT_WINDOW` — ограничение частоты POST на `/contacts`
- `MAIL_*` и `ADMIN_EMAIL` — для уведомлений о новых заявках

## Безопасность
Реализовано:
- CSRF-защита форм (контакты и админ-действия)
- POST-only для админ-изменений (`mark-read`, `delete`)
- ограничение попыток входа в админку по IP
- базовый IP rate-limit для `/admin/login` и `/contacts`
- обязательные `SECRET_KEY` и `ADMIN_PASSWORD`
- ограничение срока админ-сессии (`PERMANENT_SESSION_LIFETIME`)
- `X-Request-ID` в каждом ответе и логах для трассировки
- CSP в режиме `Report-Only` по умолчанию

Отчеты CSP можно принимать на endpoint `POST /csp-report`.

## Дизайн
- `classic` — текущий рабочий дизайн
- `futuristic` — альтернативный вариант

Для переключения поменяйте `DESIGN_VARIANT` в `.env` и перезапустите приложение.

## Проверка перед деплоем

```bash
python -m compileall app.py config.py
pytest
```

После запуска проверьте:
- `/`
- `/services`
- `/contacts` (включая отправку формы)
- `/admin` (вход, фильтр, mark-read/delete)

Проверка SEO URL (canonical/og) локально:
```bash
.venv/bin/python scripts/check_seo_urls.py
```

