from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.profiles import ProfileResponse
from app.services.profiles import ProfileServiceError, get_profile

router = APIRouter(tags=["Authentication"])


@router.get("/auth-check")
def auth_check(
    current_user_id: Annotated[UUID, Depends(get_current_user)],
) -> dict[str, object]:
    return success_response(
        "Authentication successful",
        {"user_id": str(current_user_id)},
    )


@router.get("/auth/me")
def read_authenticated_user(
    current_user_id: Annotated[UUID, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    try:
        profile = get_profile(db, current_user_id)
    except ProfileServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    profile_data = (
        ProfileResponse.model_validate(profile).model_dump(mode="json")
        if profile is not None
        else None
    )
    return success_response(
        "Authenticated user retrieved successfully",
        {"user_id": str(current_user_id), "profile": profile_data},
    )