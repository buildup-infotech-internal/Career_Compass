from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import verify_supabase_token
from app.db.session import get_db
from app.main import app

USER_ID = UUID("6f1c12fd-1ed6-4f85-87dc-438a8545ec34")
ISSUER = "https://career-compass-test.supabase.co/auth/v1"


class FakeSigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class FakeJwksClient:
    def __init__(self, key: object) -> None:
        self.key = key
        self.requested_kid: str | None = None

    def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
        self.requested_kid = jwt.get_unverified_header(token).get("kid")
        return FakeSigningKey(self.key)


def make_token(
    private_key: object,
    *,
    subject: str = str(USER_ID),
    issuer: str = ISSUER,
    audience: str = "authenticated",
    expires_at: datetime | None = None,
) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": expires_at or now + timedelta(minutes=5),
    }
    return jwt.encode(
        claims,
        private_key,
        algorithm="ES256",
        headers={"kid": "test-key-1"},
    )


@pytest.fixture
def signing_keys(monkeypatch: pytest.MonkeyPatch) -> tuple[object, object, FakeJwksClient]:
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    other_private_key = ec.generate_private_key(ec.SECP256R1())
    jwks_client = FakeJwksClient(private_key.public_key())
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://career-compass-test.supabase.co")
    monkeypatch.setattr("app.core.security.get_jwks_client", lambda: jwks_client)
    return private_key, other_private_key, jwks_client


def test_verifies_es256_signature_and_selects_key_id(
    signing_keys: tuple[object, object, FakeJwksClient],
) -> None:
    private_key, _, jwks_client = signing_keys
    token = make_token(private_key)

    payload = verify_supabase_token(token)

    assert payload["sub"] == str(USER_ID)
    assert jwks_client.requested_kid == "test-key-1"


def test_protected_auth_route_accepts_only_verified_access_tokens(
    signing_keys: tuple[object, object, FakeJwksClient],
) -> None:
    private_key, other_private_key, _ = signing_keys
    valid_token = make_token(private_key)
    invalid_token = make_token(other_private_key)

    with TestClient(app) as client:
        valid_response = client.get(
            "/api/v1/auth-check",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        invalid_response = client.get(
            "/api/v1/auth-check",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

    assert valid_response.status_code == 200
    assert valid_response.json()["data"]["user_id"] == str(USER_ID)
    assert invalid_response.status_code == 401


def test_auth_me_returns_verified_identity_and_optional_profile(
    signing_keys: tuple[object, object, FakeJwksClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, _, _ = signing_keys
    monkeypatch.setattr("app.api.v1.endpoints.auth.get_profile", lambda _db, _id: None)
    app.dependency_overrides[get_db] = lambda: object()

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {make_token(private_key)}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"] == {"user_id": str(USER_ID), "profile": None}


def test_rejects_invalid_signature(
    signing_keys: tuple[object, object, FakeJwksClient],
) -> None:
    _, other_private_key, _ = signing_keys

    with pytest.raises(InvalidTokenError):
        verify_supabase_token(make_token(other_private_key))


@pytest.mark.parametrize(
    ("claims", "exception"),
    [
        ({"expires_at": datetime.now(UTC) - timedelta(minutes=1)}, jwt.ExpiredSignatureError),
        ({"issuer": "https://wrong.example/auth/v1"}, jwt.InvalidIssuerError),
        ({"audience": "wrong-audience"}, jwt.InvalidAudienceError),
        ({"subject": "not-a-uuid"}, None),
    ],
)
def test_rejects_invalid_claims_and_malformed_subject(
    signing_keys: tuple[object, object, FakeJwksClient],
    claims: dict[str, object],
    exception: type[Exception] | None,
) -> None:
    private_key, _, _ = signing_keys
    token = make_token(private_key, **claims)  # type: ignore[arg-type]

    if exception is None:
        with pytest.raises(HTTPException) as error:
            get_current_user(
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            )
        assert error.value.status_code == 401
    else:
        with pytest.raises(exception):
            verify_supabase_token(token)


def test_missing_credentials_are_unauthorized() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_user(None)

    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}
