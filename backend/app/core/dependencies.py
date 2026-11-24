
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.core.security import verify_supabase_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UUID:
    """
    Verify the Supabase access token and return the authenticated user's UUID.
    """

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = verify_supabase_token(credentials.credentials)

        user_id = payload.get("sub")

        if not user_id:
            raise unauthorized

        return UUID(user_id)

    except (InvalidTokenError, PyJWKClientError, ValueError):
        raise unauthorized
