
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.core.config import settings


@lru_cache
def get_jwks_client():
    if not settings.SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured.")

    jwks_url = (
        f"{settings.SUPABASE_URL.rstrip('/')}"
        "/auth/v1/.well-known/jwks.json"
    )

    return PyJWKClient(jwks_url)


def verify_supabase_token(token: str) -> dict:
    """
    Verify a Supabase JWT and return its trusted claims.
    """

    issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"

    signing_key = get_jwks_client().get_signing_key_from_jwt(token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256"],
        audience="authenticated",
        issuer=issuer,
        options={
            "require": ["exp", "sub", "iss", "aud"],
        },
    )

    return payload
