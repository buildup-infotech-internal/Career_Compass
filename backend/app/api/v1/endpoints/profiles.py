from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.profiles import ProfileResponse, ProfileUpdate
from app.services.profiles import (
    ProfileServiceError,
    delete_profile,
    get_profile,
    upsert_profile,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])
CurrentUser = Annotated[UUID, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/me")
def read_my_profile(
    user_id: CurrentUser,
    db: DatabaseSession,
) -> dict[str, object]:
    try:
        profile = get_profile(db, user_id)
    except ProfileServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    data = ProfileResponse.model_validate(profile).model_dump(mode="json")
    return success_response("Profile retrieved successfully", data)


@router.put("/me")
def save_my_profile(
    update: ProfileUpdate,
    user_id: CurrentUser,
    db: DatabaseSession,
) -> dict[str, object]:
    try:
        profile = upsert_profile(db, user_id, update)
    except ProfileServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    data = ProfileResponse.model_validate(profile).model_dump(mode="json")
    return success_response("Profile saved successfully", data)


@router.delete("/me")
def remove_my_profile(
    user_id: CurrentUser,
    db: DatabaseSession,
) -> dict[str, object]:
    try:
        deleted = delete_profile(db, user_id)
    except ProfileServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return success_response(
        "Application profile and associated data deleted successfully",
        {"id": str(user_id)},
    )