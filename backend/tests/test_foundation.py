from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.session import dispose_database, get_db, get_engine, get_session_factory
from app.main import app, create_app


def test_root_and_health_routes_use_success_envelope() -> None:
    with TestClient(app) as client:
        for path in ("/", "/health", "/api/v1/health"):
            response = client.get(path)
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert body["message"]
            assert body["data"] == {}


def test_http_errors_use_contract_envelope() -> None:
    with TestClient(app) as client:
        response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "Not Found",
        "errors": [],
    }


def test_auth_error_uses_contract_envelope() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/auth-check")
        auth_me_response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "message": "Invalid or expired authentication token.",
        "errors": [],
    }
    assert auth_me_response.status_code == 401


def test_validation_errors_use_contract_envelope() -> None:
    validation_app = create_app(Settings())

    @validation_app.get("/validation-probe")
    def validation_probe(count: int) -> dict[str, int]:
        return {"count": count}

    with TestClient(validation_app) as client:
        response = client.get("/validation-probe", params={"count": "invalid"})

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Request validation failed"
    assert body["errors"][0]["loc"] == ["query", "count"]


def test_swagger_and_openapi_are_available() -> None:
    with TestClient(app) as client:
        docs_response = client.get("/docs")
        schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert "swagger-ui" in docs_response.text
    assert schema_response.status_code == 200
    paths = schema_response.json()["paths"]
    assert "/api/v1/health" in paths
    assert set(paths["/api/v1/profiles/me"]) == {"get", "put", "delete"}


def test_cors_origins_are_configurable() -> None:
    cors_app = create_app(Settings(CORS_ORIGINS="https://web.example, http://localhost:5173"))
    with TestClient(cors_app) as client:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://web.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://web.example"


def test_database_dependency_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr(
        "app.db.session.get_session_factory",
        lambda: lambda: session,
    )
    db_dependency = get_db()

    assert next(db_dependency) is session
    with pytest.raises(StopIteration):
        next(db_dependency)
    session.close.assert_called_once_with()


def test_database_disposal_clears_cached_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.db.session.settings.DATABASE_URL",
        "sqlite+pysqlite:///:memory:",
    )
    get_engine()
    get_session_factory()

    dispose_database()

    assert get_engine.cache_info().currsize == 0
    assert get_session_factory.cache_info().currsize == 0