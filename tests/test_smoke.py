import importlib
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

app_module = importlib.import_module("app")
app = app_module.app
db = app_module.db


@pytest.fixture()
def client():
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client


def test_home_page_returns_ok(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.headers.get("Content-Security-Policy-Report-Only")


def test_favicon_ico_returns_ok(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert response.headers.get("X-Request-ID")


def test_unknown_page_returns_custom_404(client):
    response = client.get("/definitely-missing-page")
    assert response.status_code == 404
    assert b"404" in response.data


def test_csp_report_endpoint_returns_204(client):
    response = client.post("/csp-report", json={"csp-report": {"blocked-uri": "https://example.com"}})
    assert response.status_code == 204


def test_admin_requires_login_redirect(client):
    response = client.get("/admin")
    assert response.status_code == 302
    assert "/admin/login" in response.headers.get("Location", "")


@pytest.mark.parametrize(
    "path",
    ["/services", "/contacts", "/news"],
)
def test_public_section_pages_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
