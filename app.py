"""
ООО "ЭТАЖИ" - Сайт компании по ремонту и обслуживанию лифтов
Flask веб-приложение с админ-панелью и базой данных
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, Response, g, has_request_context, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import logging
import secrets
import socket
import json
import hmac
import re
import time
from xml.sax.saxutils import escape
from functools import wraps
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import text

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - handled at runtime in upload flow
    Image = None
    ImageOps = None

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
except ImportError:  # pragma: no cover - optional dependency
    sentry_sdk = None
    FlaskIntegration = None

# Загрузить переменные из .env рядом с app.py
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=env_path, override=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler("etazhi.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        request_id = "-"
        if has_request_context():
            request_id = getattr(g, "request_id", "-")
        record.request_id = request_id
        return True


class JsonRequestFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if has_request_context():
            payload["path"] = request.path
            payload["method"] = request.method
            payload["client_ip"] = get_client_ip()
        return json.dumps(payload, ensure_ascii=False)


request_id_filter = RequestIdFilter()
json_formatter = JsonRequestFormatter()
for handler in logging.getLogger().handlers:
    handler.addFilter(request_id_filter)
    handler.setFormatter(json_formatter)

# Инициализация приложения
app = Flask(__name__)

# Конфигурация
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY не задан")
app.config["SECRET_KEY"] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///etazhi.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "True").lower() == "true"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 64 * 1024))
app.config["STATIC_ASSETS_CACHE_MAX_AGE"] = int(os.environ.get("STATIC_ASSETS_CACHE_MAX_AGE", 604800))
app.config["ARTICLE_UPLOADS_CACHE_MAX_AGE"] = int(os.environ.get("ARTICLE_UPLOADS_CACHE_MAX_AGE", 86400))
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = app.config["STATIC_ASSETS_CACHE_MAX_AGE"]
app.config["SENTRY_DSN"] = os.environ.get("SENTRY_DSN", "").strip()
app.config["SENTRY_TRACES_SAMPLE_RATE"] = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
app.config["CSP_REPORT_ONLY"] = os.environ.get("CSP_REPORT_ONLY", "true").strip().lower() == "true"
app.config["CSP_REPORT_URI"] = os.environ.get("CSP_REPORT_URI", "").strip()
app.config["ADMIN_LOGIN_RATE_LIMIT_COUNT"] = int(os.environ.get("ADMIN_LOGIN_RATE_LIMIT_COUNT", 12))
app.config["ADMIN_LOGIN_RATE_LIMIT_WINDOW"] = int(os.environ.get("ADMIN_LOGIN_RATE_LIMIT_WINDOW", 300))
app.config["CONTACTS_RATE_LIMIT_COUNT"] = int(os.environ.get("CONTACTS_RATE_LIMIT_COUNT", 3))
app.config["CONTACTS_RATE_LIMIT_WINDOW"] = int(os.environ.get("CONTACTS_RATE_LIMIT_WINDOW", 600))
app.config["ADMIN_MAX_LOGIN_ATTEMPTS"] = int(os.environ.get("ADMIN_MAX_LOGIN_ATTEMPTS", 4))
app.config["ADMIN_LOGIN_BLOCK_MINUTES"] = int(os.environ.get("ADMIN_LOGIN_BLOCK_MINUTES", 30))

# Email настройки для Flask-Mail
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.mail.ru")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 465))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "False").lower() == "true"
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", "True").lower() == "true"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "Daniillomeyko@mail.ru")
app.config["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL", "Daniillomeyko@mail.ru")

# Инициализация Flask-Mail
mail = Mail(app)

admin_password = os.environ.get("ADMIN_PASSWORD")
if not admin_password:
    raise RuntimeError("ADMIN_PASSWORD не задан")
app.config["ADMIN_PASSWORD"] = admin_password

# Публичные параметры
app.config["COMPANY_NAME"] = 'ООО "ЭТАЖИ"'
app.config["COMPANY_SINCE"] = 2021
app.config["DESIGN_VARIANT"] = os.environ.get("DESIGN_VARIANT", "classic").strip().lower()
app.config["COMPANY_CITY"] = os.environ.get("COMPANY_CITY", "Санкт-Петербург")
app.config["COMPANY_ADDRESS"] = os.environ.get(
    "COMPANY_ADDRESS",
    "198320, г. Санкт-Петербург, пр-кт Ленина, д. 77 литера А, этаж 4, офис 418"
)
app.config["COMPANY_INN"] = os.environ.get("COMPANY_INN", "7807250523")
app.config["COMPANY_OGRN"] = os.environ.get("COMPANY_OGRN", "1217800123420")
app.config["COMPANY_WORK_HOURS"] = os.environ.get("COMPANY_WORK_HOURS", "Пн-Пт: 9:00 - 18:00")
app.config["YANDEX_METRIKA_ID"] = os.environ.get("YANDEX_METRIKA_ID", "").strip()
app.config["SITE_URL"] = os.environ.get("SITE_URL", "").strip().rstrip("/")
app.config["HERO_VIDEO_PATH"] = os.environ.get("HERO_VIDEO_PATH", "").strip()
app.config["HERO_IMAGE_PATH"] = os.environ.get("HERO_IMAGE_PATH", "").strip()
app.config["HERO_VIDEO_ENABLED"] = os.environ.get("HERO_VIDEO_ENABLED", "false").strip().lower() == "true"

if app.config["SENTRY_DSN"]:
    if sentry_sdk and FlaskIntegration:
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=app.config["SENTRY_TRACES_SAMPLE_RATE"],
        )
        logger.info("Sentry initialized")
    else:
        logger.warning("SENTRY_DSN is set, but sentry-sdk is not installed")

# Инициализация базы данных
db = SQLAlchemy(app)

# Ограничение попыток входа
LOGIN_ATTEMPTS = {}
RATE_LIMIT_BUCKETS = {}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DEFAULT_ARTICLES = [
    {
        "slug": "kak-podgotovit-lift-k-zime",
        "title": "Как подготовить лифт к зимнему периоду",
        "excerpt": "Практический чек-лист подготовки лифтов к зиме: что проверить заранее, чтобы снизить риск остановок и жалоб.",
        "published_at": "2026-04-22",
        "category": "Эксплуатация",
        "read_time": "9 минут",
        "content": [
            "Зимний период - это проверка качества эксплуатации лифта. Низкие температуры, влажность и рост нагрузки в пиковые часы увеличивают риск сбоев, если оборудование не подготовлено заранее.",
            "## Что проверить до начала холодов",
            "Профилактика перед сезоном должна проводиться заранее, а не после первых остановок. Чем раньше выполнен аудит, тем меньше внеплановых выездов.",
            "- Дверные приводы и створки: скорость закрытия, плавность хода, отсутствие перекосов.",
            "- Направляющие и механические узлы: износ, люфты, корректность регулировок.",
            "- Системы смазки: состояние и достаточность смазочных материалов по регламенту.",
            "- Электрооборудование: контакты, клеммы, состояние шкафов управления.",
            "- Диспетчеризация и связь: стабильность канала и корректность аварийных уведомлений.",
            "## Почему зимой растет количество обращений",
            "Основная причина - не один крупный дефект, а сочетание небольших отклонений: дверь закрывается медленнее, датчики реагируют с задержкой, увеличивается нагрузка на привод. В совокупности это приводит к частым остановкам.",
            "### Типовой сценарий",
            "Сначала появляются редкие рывки или задержки на этажах, затем растет число ложных срабатываний, а после - лифт начинает останавливаться по защите. Если обслуживающая команда реагирует только на факт остановки, проблемы повторяются.",
            "## Как построить подготовку правильно",
            "Эффективный подход - работать по чек-листу с фиксацией результатов. Это снижает зависимость от человеческого фактора и упрощает контроль для УК/ТСЖ.",
            "- Согласовать график профилактики заранее.",
            "- Выполнить диагностику по узлам с повышенным сезонным риском.",
            "- Закрыть выявленные замечания до начала пиковых морозов.",
            "- Зафиксировать выполненные работы в журнале ТО и актах.",
            "## Какие признаки нельзя игнорировать",
            "Если кабина стала работать шумнее, двери закрываются дольше обычного или периодически возникают рывки, это повод для внеплановой проверки. Такие сигналы часто предшествуют остановке оборудования.",
            "## Короткий вывод",
            "Подготовка лифта к зиме - это не формальность, а инструмент снижения рисков и затрат. Регулярная профилактика до сезона всегда дешевле аварийных выездов в разгар эксплуатации."
        ]
    },
    {
        "slug": "otchetnost-posle-servisnogo-vyezda",
        "title": "Какая отчетность нужна после сервисного выезда",
        "excerpt": "Разбираем, какие документы должен получать заказчик после выезда и как по ним контролировать качество обслуживания.",
        "published_at": "2026-04-15",
        "category": "Документы",
        "read_time": "8 минут",
        "content": [
            "После сервисного выезда важен не только факт выполнения работ, но и качество документирования. Именно документы позволяют заказчику понимать, что сделано, почему это сделано и в каком состоянии оборудование сейчас.",
            "## Базовый пакет документов",
            "Минимальный набор должен быть одинаково понятен техническим специалистам, бухгалтерии и управляющему персоналу объекта.",
            "- Акт выполненных работ с датой, адресом и перечнем операций.",
            "- Перечень замененных материалов и узлов (если применялось).",
            "- Отметка о текущем состоянии лифта после выезда.",
            "- Подписи ответственных сторон.",
            "## Что особенно важно для УК и ТСЖ",
            "При регулярной эксплуатации ключевую роль играет накопительная история работ. Без нее сложно анализировать повторяющиеся неисправности и принимать решения по модернизации.",
            "### Журнал технического обслуживания",
            "Журнал позволяет отследить периодичность работ, фактические интервалы между отказами и реакцию подрядчика на обращения. Это основа прозрачной эксплуатации.",
            "## Отчет после аварийного выезда",
            "Если выезд был внеплановым, в отчете важно зафиксировать не только устранение симптома, но и предполагаемую первопричину.",
            "- Причина обращения и характер инцидента.",
            "- Какие действия выполнены на месте.",
            "- Текущий статус: восстановлено/требуется дополнительный ремонт.",
            "- Рекомендации по предотвращению повторного отказа.",
            "## Как заказчику быстро проверить качество отчета",
            "Хороший отчет отвечает на три вопроса: что было неисправно, что сделано и что делать дальше. Если хотя бы один из ответов отсутствует, контроль качества становится формальным.",
            "### Частая ошибка",
            "Иногда документ ограничивается формулировкой «работоспособность восстановлена». Для управляемой эксплуатации этого недостаточно: нужна детализация по действиям и рекомендациям.",
            "## Короткий вывод",
            "Прозрачная отчетность - это инструмент контроля рисков и бюджета. Чем лучше оформлены документы после выезда, тем проще управлять лифтовым парком и планировать дальнейшие работы."
        ]
    },
    {
        "slug": "kogda-nuzhna-modernizaciya-lifta",
        "title": "Насколько безопасны лифты? 4 мифа и правила безопасности",
        "excerpt": "Разбираем популярные мифы о лифтах, ключевые системы безопасности и действия пассажира в нештатной ситуации.",
        "published_at": "2026-04-08",
        "category": "Безопасность",
        "read_time": "12 минут",
        "content": [
            "Лифтовое оборудование в жилых и коммерческих зданиях обеспечивает комфорт и безопасное перемещение людей и грузов. За безопасность на разных этапах отвечают разные участники: завод-изготовитель, поставщик, монтажная и обслуживающая организация, а также пользователь.",
            "## Что делает лифт безопасным",
            "Современный лифт безопасен при трех условиях: оборудование изготовлено по требованиям, корректно смонтировано и проходит регулярное техническое обслуживание.",
            "В практическом смысле безопасность - это набор решений, которые предотвращают падение, блокируют опасное движение и останавливают кабину при отклонениях.",
            "## Топ-5 систем безопасности",
            "- Тормозная система: штатная остановка и экстренное торможение.",
            "- Несущие канаты с запасом прочности: удержание кабины и противовеса.",
            "- Амортизационные буфера: снижение ударных нагрузок в крайних точках.",
            "- Ограничитель скорости и ловители: фиксация кабины при недопустимых режимах.",
            "- Блокировка дверей: запрет движения при открытых створках.",
            "Ключевой принцип системы безопасности - дублирование: при отказе основного элемента включается резервный.",
            "## 4 распространенных мифа",
            "### Миф 1. Оборвался трос - кабина падает",
            "Кабина удерживается несколькими канатами, а при опасном ускорении срабатывают ловители. Вероятность одновременного отказа всех уровней защиты минимальна.",
            "### Миф 2. Двери могут открыться без кабины",
            "Этажные двери не открываются без кабины на уровне этажа. Также система блокирует движение, пока двери не закрыты полностью.",
            "### Миф 3. В застрявшем лифте можно задохнуться",
            "Кабина не герметична, в современных решениях дополнительно предусмотрена вентиляция. Основной реальный риск связан не с остановкой, а с пожаром и задымлением.",
            "### Миф 4. Нет электричества - лифт становится опасным",
            "Современные системы обеспечивают безопасный алгоритм остановки. В ряде моделей используются резервные источники питания.",
            "## Почему случаются поломки",
            "- Экономия на оборудовании, комплектующих и квалификации подрядчика.",
            "- Нарушения при монтаже и эксплуатации.",
            "- Несвоевременное или формальное техническое обслуживание.",
            "- Игнорирование ранних признаков неисправности.",
            "## Когда вызывать специалистов сразу",
            "Скрежет, вибрации, рывки при старте/остановке, нестабильная работа дверей, а также остановка выше или ниже уровня этажа - это прямой сигнал к внеплановой проверке.",
            "## Если вы застряли в лифте",
            "Главное правило - не паниковать и вызвать специалистов через диспетчерскую связь.",
            "- Не пытайтесь вскрывать двери самостоятельно.",
            "- Не выходите через приоткрытую дверь.",
            "- Не прыгайте и не нажимайте подряд все кнопки.",
            "## Короткий вывод",
            "Лифт - это безопасная система при корректной эксплуатации и регулярном обслуживании. Чем дисциплинированнее регламент, тем ниже риск инцидентов."
        ]
    }
]
ARTICLES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "articles.json")
ARTICLE_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads", "articles")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def normalize_slug(raw_value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw_value.strip().lower()).strip("-")
    return slug


def load_articles():
    if not os.path.exists(ARTICLES_FILE):
        return list(DEFAULT_ARTICLES)
    try:
        with open(ARTICLES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            for item in data:
                image_url = (item or {}).get("image_url", "")
                if not image_url:
                    continue

                normalized_image_url = image_url.strip()
                # Support legacy records that might miss a leading slash.
                if normalized_image_url.startswith("static/uploads/articles/"):
                    normalized_image_url = f"/{normalized_image_url}"

                if normalized_image_url.startswith("/static/uploads/articles/"):
                    absolute_image_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        normalized_image_url.lstrip("/")
                    )
                    # If image file is missing, fallback to icon instead of a broken <img>.
                    if os.path.exists(absolute_image_path):
                        item["image_url"] = normalized_image_url
                    else:
                        item["image_url"] = ""
                else:
                    # External links are kept as-is.
                    item["image_url"] = normalized_image_url
            return data
    except Exception as e:
        logger.warning("Не удалось загрузить articles.json: %s", e)
    return list(DEFAULT_ARTICLES)


def save_articles(articles):
    os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as file:
        json.dump(articles, file, ensure_ascii=False, indent=2)


def get_client_ip():
    return (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()


def generate_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf_token(token):
    expected_token = session.get("csrf_token", "")
    return bool(expected_token) and bool(token) and secrets.compare_digest(expected_token, token)


def validate_contact_fields(name: str, email: str, phone: str, message: str):
    if not name or not email or not message:
        return "Пожалуйста, заполните все обязательные поля."
    if len(name) < 2 or len(name) > 80:
        return "Имя должно содержать от 2 до 80 символов."
    if len(email) > 120 or not EMAIL_PATTERN.fullmatch(email):
        return "Введите корректный email."
    if phone:
        normalized_phone = re.sub(r"[^\d+()\-\s]", "", phone)
        digits_only = re.sub(r"\D", "", normalized_phone)
        if normalized_phone != phone or len(digits_only) < 7 or len(digits_only) > 15:
            return "Введите корректный номер телефона."
    if len(message) < 10 or len(message) > 4000:
        return "Сообщение должно содержать от 10 до 4000 символов."
    return None


def hit_rate_limit(bucket_key: str, limit_count: int, window_seconds: int):
    now_ts = time.time()
    history = RATE_LIMIT_BUCKETS.get(bucket_key, [])
    history = [ts for ts in history if now_ts - ts < window_seconds]
    if len(history) >= limit_count:
        retry_after = max(1, int(window_seconds - (now_ts - history[0])))
        RATE_LIMIT_BUCKETS[bucket_key] = history
        return True, retry_after
    history.append(now_ts)
    RATE_LIMIT_BUCKETS[bucket_key] = history
    return False, 0


def get_site_url() -> str:
    configured_site_url = app.config.get("SITE_URL", "")
    if configured_site_url:
        return configured_site_url
    return request.url_root.rstrip("/")


def abs_url(path: str = "") -> str:
    site_url = get_site_url()
    if not path:
        return site_url
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{site_url}{path}"


@app.context_processor
def inject_template_vars():
    return {
        "csrf_token": generate_csrf_token,
        "site_url": get_site_url,
        "abs_url": abs_url
    }


@app.before_request
def set_request_id():
    header_request_id = request.headers.get("X-Request-ID", "").strip()
    g.request_id = header_request_id or secrets.token_hex(8)


@app.after_request
def add_admin_robots_header(response):
    response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
    if request.path.startswith("/admin"):
        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    if request.path.startswith("/static/uploads/articles/"):
        uploads_max_age = app.config.get("ARTICLE_UPLOADS_CACHE_MAX_AGE", 86400)
        response.headers["Cache-Control"] = f"public, max-age={uploads_max_age}"
    elif request.path.startswith("/static/"):
        assets_max_age = app.config.get("STATIC_ASSETS_CACHE_MAX_AGE", 604800)
        response.headers["Cache-Control"] = f"public, max-age={assets_max_age}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    csp_directives = [
        "default-src 'self'",
        "img-src 'self' data: https:",
        "script-src 'self' https://mc.yandex.ru https://cdnjs.cloudflare.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:",
        "connect-src 'self' https://mc.yandex.ru",
        "frame-ancestors 'self'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
    report_uri = app.config.get("CSP_REPORT_URI", "")
    if report_uri:
        csp_directives.append(f"report-uri {report_uri}")
    csp_value = "; ".join(csp_directives)
    if app.config.get("CSP_REPORT_ONLY", True):
        response.headers["Content-Security-Policy-Report-Only"] = csp_value
    else:
        response.headers["Content-Security-Policy"] = csp_value
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(_error):
    flash("Слишком большой объем данных. Сократите сообщение и повторите отправку.", "error")
    return render_template(get_public_template("contacts"), current_year=datetime.now().year), 413


@app.errorhandler(404)
def handle_not_found(_error):
    return render_template(get_public_template("404"), current_year=datetime.now().year), 404


@app.errorhandler(500)
def handle_internal_error(error):
    logger.exception("Внутренняя ошибка сервера: %s", error)
    db.session.rollback()
    return render_template(get_public_template("500"), current_year=datetime.now().year), 500


# ============ МОДЕЛИ БАЗЫ ДАННЫХ ============
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ ДЕКОРАТОРЫ ============
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# ============ РОУТЫ ============
def get_public_template(template_name):
    if app.config.get("DESIGN_VARIANT") == "futuristic":
        return f"{template_name}_futuristic.html"
    return f"{template_name}.html"


def get_article_by_slug(slug):
    articles = load_articles()
    return next((item for item in articles if item["slug"] == slug), None)


def get_ordered_articles():
    return list(load_articles())


def get_article_lastmod(article) -> str:
    published_at = (article or {}).get("published_at", "")
    try:
        return datetime.strptime(published_at, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        return datetime.utcnow().date().isoformat()


def is_allowed_image(filename: str) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_article_image(file_storage, slug_prefix: str):
    if not file_storage or not file_storage.filename:
        return None
    if not is_allowed_image(file_storage.filename):
        raise ValueError("Допустимы только изображения JPG, PNG или WEBP.")

    os.makedirs(ARTICLE_UPLOAD_DIR, exist_ok=True)
    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    filename = f"{slug_prefix}-{int(datetime.utcnow().timestamp())}.webp"
    absolute_path = os.path.join(ARTICLE_UPLOAD_DIR, filename)
    if Image is None or ImageOps is None:
        raise ValueError("Для загрузки изображений установите Pillow: pip install Pillow")

    with Image.open(file_storage.stream) as image:
        # Корректируем ориентацию по EXIF, чтобы обложка не была повернута/растянута.
        image = ImageOps.exif_transpose(image)
        max_width = 2560
        max_height = 1700
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        # Храним обложки в едином формате WEBP с повышенным качеством.
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")
        image.save(absolute_path, format="WEBP", quality=94, method=6)

    return f"/static/uploads/articles/{filename}"


def remove_uploaded_article_image(image_url: str):
    if not image_url or not image_url.startswith("/static/uploads/articles/"):
        return
    absolute_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_url.lstrip("/"))
    if os.path.exists(absolute_path):
        try:
            os.remove(absolute_path)
        except OSError:
            logger.warning("Не удалось удалить старое изображение статьи: %s", absolute_path)


@app.route("/robots.txt")
def robots():
    base_url = request.url_root.rstrip("/")
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {base_url}/sitemap.xml"
    ])
    return Response(body, mimetype="text/plain; charset=utf-8")


@app.route("/sitemap.xml")
def sitemap():
    base_url = request.url_root.rstrip("/")
    app_lastmod = datetime.utcfromtimestamp(os.path.getmtime(__file__)).date().isoformat()
    static_urls = [
        ("/", "weekly", "1.0", app_lastmod),
        ("/services", "weekly", "0.9", app_lastmod),
        ("/contacts", "monthly", "0.8", app_lastmod),
        ("/news", "daily", "0.9", app_lastmod),
        ("/novosti-liftov", "daily", "0.8", app_lastmod),
    ]

    items = []
    for path, changefreq, priority, lastmod in static_urls:
        absolute_url = escape(f"{base_url}{path}")
        items.append(
            "<url>"
            f"<loc>{absolute_url}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            f"<changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority>"
            "</url>"
        )

    for article in get_ordered_articles():
        absolute_url = escape(f"{base_url}/news/{article['slug']}")
        lastmod = get_article_lastmod(article)
        items.append(
            "<url>"
            f"<loc>{absolute_url}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            "<changefreq>monthly</changefreq>"
            "<priority>0.8</priority>"
            "</url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(items)
        + "</urlset>"
    )
    return Response(xml, mimetype="application/xml; charset=utf-8")


@app.route("/favicon.ico")
def favicon_ico():
    """Корневой favicon для роботов Google/Яндекс (часто запрашивают именно /favicon.ico)."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "logo-512.svg",
        mimetype="image/svg+xml",
    )


@app.route("/news")
def news():
    articles = get_ordered_articles()
    categories = sorted({item.get("category", "Статьи") for item in articles})
    return render_template(
        get_public_template("news"),
        articles=articles,
        categories=categories,
        current_year=datetime.now().year
    )


@app.route("/news/<slug>")
def news_article(slug):
    article = get_article_by_slug(slug)
    if not article:
        abort(404)
    related_articles = [
        item for item in get_ordered_articles()
        if item["slug"] != slug and item.get("category") == article.get("category")
    ][:3]
    if len(related_articles) < 3:
        for item in get_ordered_articles():
            if item["slug"] == slug or item in related_articles:
                continue
            related_articles.append(item)
            if len(related_articles) == 3:
                break
    return render_template(
        get_public_template("news_article"),
        article=article,
        related_articles=related_articles,
        current_year=datetime.now().year
    )


@app.route("/novosti-liftov")
def news_alias():
    return redirect(url_for("news"), code=301)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        ip = get_client_ip()
        limited, retry_after = hit_rate_limit(
            f"admin-login:{ip}",
            app.config["ADMIN_LOGIN_RATE_LIMIT_COUNT"],
            app.config["ADMIN_LOGIN_RATE_LIMIT_WINDOW"],
        )
        if limited:
            flash(f"Слишком частые попытки входа. Повторите через {retry_after} сек.", "error")
            return render_template("admin_login.html"), 429

        csrf = request.form.get("csrf_token", "")
        if not validate_csrf_token(csrf):
            abort(400)

        now = datetime.utcnow()
        attempt_data = LOGIN_ATTEMPTS.get(ip, {"count": 0, "blocked_until": None})
        password = request.form.get("password", "")

        # Если пароль верный, пускаем сразу и сбрасываем блокировку/счетчик попыток.
        if hmac.compare_digest(password, app.config["ADMIN_PASSWORD"]):
            LOGIN_ATTEMPTS.pop(ip, None)
            session.clear()
            session["admin_logged_in"] = True
            session["csrf_token"] = secrets.token_hex(32)
            session.permanent = True
            flash("Вы успешно вошли в админ-панель", "success")
            return redirect(url_for("admin"))

        blocked_until = attempt_data.get("blocked_until")
        if blocked_until and now < blocked_until:
            minutes_left = int((blocked_until - now).total_seconds() // 60) + 1
            flash(f"Слишком много попыток входа. Повторите через {minutes_left} мин.", "error")
            return render_template("admin_login.html")

        attempt_data["count"] = attempt_data.get("count", 0) + 1
        if attempt_data["count"] >= app.config["ADMIN_MAX_LOGIN_ATTEMPTS"]:
            attempt_data["blocked_until"] = now + timedelta(minutes=app.config["ADMIN_LOGIN_BLOCK_MINUTES"])
            attempt_data["count"] = 0
        LOGIN_ATTEMPTS[ip] = attempt_data
        flash("Неверный пароль", "error")
    return render_template("admin_login.html")


@app.route("/")
def home():
    logger.info("Посетитель открыл главную страницу")
    hero_video_path = app.config.get("HERO_VIDEO_PATH", "")
    hero_video_enabled = app.config.get("HERO_VIDEO_ENABLED", False)
    hero_image_path = app.config.get("HERO_IMAGE_PATH", "")
    hero_video_url = ""
    hero_video_type = ""
    hero_image_url = ""

    if hero_image_path:
        normalized_image_path = hero_image_path.lstrip("/")
        if normalized_image_path.startswith(("http://", "https://")):
            hero_image_url = normalized_image_path
        else:
            hero_image_url = url_for("static", filename=normalized_image_path)
    if hero_video_enabled and hero_video_path:
        normalized_path = hero_video_path.lstrip("/")
        if normalized_path.startswith(("http://", "https://")):
            hero_video_url = normalized_path
        else:
            hero_video_url = url_for("static", filename=normalized_path)

        extension = os.path.splitext(normalized_path.lower())[1]
        if extension == ".webm":
            hero_video_type = "video/webm"
        elif extension == ".mov":
            hero_video_type = ""
        else:
            hero_video_type = "video/mp4"

    return render_template(
        get_public_template("home"),
        current_year=datetime.now().year,
        hero_video_url=hero_video_url,
        hero_video_type=hero_video_type,
        hero_image_url=hero_image_url,
    )


@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}, 200
    except Exception as error:
        logger.exception("Health check failed: %s", error)
        return {"status": "degraded", "database": "error"}, 503


@app.route("/csp-report", methods=["POST"])
def csp_report():
    report_payload = request.get_json(silent=True) or {}
    logger.warning("CSP report received: %s", json.dumps(report_payload, ensure_ascii=False)[:2000])
    return "", 204


@app.route("/services")
def services():
    logger.info("Посетитель открыл страницу услуг")
    return render_template(get_public_template("services"), current_year=datetime.now().year)


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        ip = get_client_ip()
        limited, retry_after = hit_rate_limit(
            f"contacts:{ip}",
            app.config["CONTACTS_RATE_LIMIT_COUNT"],
            app.config["CONTACTS_RATE_LIMIT_WINDOW"],
        )
        if limited:
            flash(f"Слишком много заявок с вашего IP. Повторите через {retry_after} сек.", "error")
            return render_template(get_public_template("contacts"), current_year=datetime.now().year), 429

        csrf = request.form.get("csrf_token", "")
        if not validate_csrf_token(csrf):
            abort(400)
        try:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            message = request.form.get("message", "").strip()
            validation_error = validate_contact_fields(name, email, phone, message)
            if validation_error:
                flash(validation_error, "error")
                return render_template(get_public_template("contacts"), current_year=datetime.now().year)

            new_message = ContactMessage(name=name, email=email, phone=phone, message=message)
            db.session.add(new_message)
            db.session.commit()
            logger.info(f"Новое сообщение от {name} ({email})")

            try:
                if app.config["MAIL_USERNAME"]:
                    msg = Message(
                        subject=f"Новая заявка с сайта - {name}",
                        sender=app.config["MAIL_DEFAULT_SENDER"],
                        recipients=[app.config["ADMIN_EMAIL"]],
                        body=f"""Новое сообщение с сайта ООО "ЭТАЖИ"

Имя: {name}
Email: {email}
Телефон: {phone or "Не указан"}
Время: {datetime.now().strftime("%d.%m.%Y %H:%M")}

Сообщение:
{message}"""
                    )
                    mail.send(msg)
                    logger.info("Email уведомление отправлено администратору")
            except Exception as e:
                logger.warning(f"Не удалось отправить email: {e}")

            flash("Спасибо! Ваше сообщение отправлено. Мы свяжемся с вами в ближайшее время.", "success")
            return render_template(get_public_template("contacts"), success=True, current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Ошибка при обработке формы: {e}")
            db.session.rollback()
            flash("Произошла ошибка при отправке сообщения.", "error")
            return render_template(get_public_template("contacts"), current_year=datetime.now().year)
    return render_template(get_public_template("contacts"), success=False, current_year=datetime.now().year)


@app.route("/admin")
@admin_login_required
def admin():
    filter_type = request.args.get("filter", "all")
    if filter_type == "unread":
        messages = ContactMessage.query.filter_by(is_read=False).order_by(ContactMessage.created_at.desc()).all()
    elif filter_type == "read":
        messages = ContactMessage.query.filter_by(is_read=True).order_by(ContactMessage.created_at.desc()).all()
    else:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()

    total_messages = ContactMessage.query.count()
    unread_count = ContactMessage.query.filter_by(is_read=False).count()
    read_count = ContactMessage.query.filter_by(is_read=True).count()
    return render_template(
        "admin.html",
        messages=messages,
        articles=get_ordered_articles()[:8],
        total_messages=total_messages,
        total_articles=len(get_ordered_articles()),
        unread_count=unread_count,
        read_count=read_count,
        filter=filter_type,
        current_year=datetime.now().year
    )


@app.route("/admin/articles/create", methods=["POST"])
@admin_login_required
def create_article():
    csrf = request.form.get("csrf_token", "")
    if not validate_csrf_token(csrf):
        abort(400)

    title = request.form.get("title", "").strip()
    excerpt = request.form.get("excerpt", "").strip()
    category = request.form.get("category", "").strip() or "Статьи"
    content_raw = request.form.get("content", "").strip()
    if not title or not excerpt or not content_raw:
        flash("Для статьи заполните заголовок, короткое описание и текст.", "error")
        return redirect(url_for("admin"))

    paragraphs = [line.strip() for line in content_raw.splitlines() if line.strip()]
    if not paragraphs:
        flash("Добавьте текст статьи (хотя бы один абзац).", "error")
        return redirect(url_for("admin"))

    articles = get_ordered_articles()
    requested_slug = request.form.get("slug", "").strip()
    base_slug = normalize_slug(requested_slug or title)
    if not base_slug:
        base_slug = f"article-{int(datetime.utcnow().timestamp())}"
    unique_slug = base_slug
    counter = 2
    existing_slugs = {item["slug"] for item in articles}
    while unique_slug in existing_slugs:
        unique_slug = f"{base_slug}-{counter}"
        counter += 1

    image_url = ""
    try:
        uploaded_image = request.files.get("image")
        saved_image = save_article_image(uploaded_image, unique_slug)
        if saved_image:
            image_url = saved_image
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("admin"))

    article = {
        "slug": unique_slug,
        "title": title,
        "excerpt": excerpt,
        "published_at": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "image_url": image_url,
        "content": paragraphs
    }
    articles.insert(0, article)
    save_articles(articles)
    flash("Статья опубликована.", "success")
    return redirect(url_for("news_article", slug=unique_slug))


@app.route("/admin/articles/<slug>/edit", methods=["GET", "POST"])
@admin_login_required
def edit_article(slug):
    articles = get_ordered_articles()
    article = next((item for item in articles if item["slug"] == slug), None)
    if not article:
        abort(404)

    if request.method == "POST":
        csrf = request.form.get("csrf_token", "")
        if not validate_csrf_token(csrf):
            abort(400)

        title = request.form.get("title", "").strip()
        excerpt = request.form.get("excerpt", "").strip()
        category = request.form.get("category", "").strip() or "Статьи"
        content_raw = request.form.get("content", "").strip()
        if not title or not excerpt or not content_raw:
            flash("Для статьи заполните заголовок, короткое описание и текст.", "error")
            return redirect(url_for("edit_article", slug=slug))

        paragraphs = [line.strip() for line in content_raw.splitlines() if line.strip()]
        if not paragraphs:
            flash("Добавьте текст статьи (хотя бы один абзац).", "error")
            return redirect(url_for("edit_article", slug=slug))

        requested_slug = request.form.get("slug", "").strip()
        base_slug = normalize_slug(requested_slug or title)
        if not base_slug:
            base_slug = slug

        unique_slug = base_slug
        counter = 2
        existing_slugs = {item["slug"] for item in articles if item is not article}
        while unique_slug in existing_slugs:
            unique_slug = f"{base_slug}-{counter}"
            counter += 1

        try:
            uploaded_image = request.files.get("image")
            if uploaded_image and uploaded_image.filename:
                new_image_url = save_article_image(uploaded_image, unique_slug)
                if new_image_url:
                    remove_uploaded_article_image(article.get("image_url", ""))
                    article["image_url"] = new_image_url
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("edit_article", slug=slug))

        article["slug"] = unique_slug
        article["title"] = title
        article["excerpt"] = excerpt
        article["category"] = category
        article["content"] = paragraphs
        save_articles(articles)
        flash("Статья обновлена.", "success")
        return redirect(url_for("news_article", slug=unique_slug))

    article_form = {
        "slug": article["slug"],
        "title": article["title"],
        "excerpt": article["excerpt"],
        "category": article["category"],
        "image_url": article.get("image_url", ""),
        "content": "\n\n".join(article.get("content", []))
    }
    return render_template(
        "admin_article_edit.html",
        article=article_form,
        current_year=datetime.now().year
    )


@app.route("/admin/articles/<slug>/delete", methods=["POST"])
@admin_login_required
def delete_article(slug):
    csrf = request.form.get("csrf_token", "")
    if not validate_csrf_token(csrf):
        abort(400)

    articles = get_ordered_articles()
    article = next((item for item in articles if item["slug"] == slug), None)
    if not article:
        abort(404)

    remove_uploaded_article_image(article.get("image_url", ""))
    articles.remove(article)
    save_articles(articles)
    flash("Статья удалена.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/articles/<slug>/move-up", methods=["POST"])
@admin_login_required
def move_article_up(slug):
    csrf = request.form.get("csrf_token", "")
    if not validate_csrf_token(csrf):
        abort(400)

    articles = get_ordered_articles()
    for idx, article in enumerate(articles):
        if article["slug"] == slug:
            if idx > 0:
                articles[idx - 1], articles[idx] = articles[idx], articles[idx - 1]
                save_articles(articles)
            break
    return redirect(url_for("admin"))


@app.route("/admin/articles/<slug>/move-down", methods=["POST"])
@admin_login_required
def move_article_down(slug):
    csrf = request.form.get("csrf_token", "")
    if not validate_csrf_token(csrf):
        abort(400)

    articles = get_ordered_articles()
    for idx, article in enumerate(articles):
        if article["slug"] == slug:
            if idx < len(articles) - 1:
                articles[idx + 1], articles[idx] = articles[idx], articles[idx + 1]
                save_articles(articles)
            break
    return redirect(url_for("admin"))


@app.route("/admin/mark-read/<int:message_id>", methods=["POST"])
@admin_login_required
def mark_read(message_id):
    csrf = request.form.get("csrf_token", "")
    if not validate_csrf_token(csrf):
        abort(400)

    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    flash("Сообщение отмечено как прочитанное", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:message_id>", methods=["POST"])
@admin_login_required
def delete_message(message_id):
    csrf = request.form.get("csrf_token", "")
    if not validate_csrf_token(csrf):
        abort(400)

    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash("Сообщение удалено", "success")
    return redirect(url_for("admin"))


@app.route("/admin/logout")
@admin_login_required
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Вы вышли из админ-панели", "info")
    return redirect(url_for("admin_login"))


# ============ ИНИЦИАЛИЗАЦИЯ ============
def init_db():
    with app.app_context():
        db.create_all()
        logger.info("База данных инициализирована")


def pick_available_port(preferred_port: int, attempts: int = 20) -> int:
    """Возвращает первый свободный порт, начиная с preferred_port."""
    for port in range(preferred_port, preferred_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return preferred_port


# ============ ЗАПУСК ============
if __name__ == "__main__":
    init_db()
    logger.info("Запуск приложения ООО 'ЭТАЖИ'...")
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    preferred_port = int(os.environ.get("PORT", "5000"))
    run_port = pick_available_port(preferred_port)
    if run_port != preferred_port:
        logger.warning(
            "Порт %s занят. Используется свободный порт %s.",
            preferred_port,
            run_port
        )
    logger.info("Открой в браузере: http://127.0.0.1:%s", run_port)
    app.run(debug=debug_mode, host="0.0.0.0", port=run_port, use_reloader=debug_mode)