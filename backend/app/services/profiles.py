from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.user import Profile
from app.schemas.profiles import ProfileUpdate


class ProfileServiceError(RuntimeError):
    """Raised when profile persistence fails."""


def get_profile(db: Session, user_id: UUID) -> Profile | None:
    try:
        return db.scalar(select(Profile).where(Profile.id == user_id))
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileServiceError("Unable to retrieve profile") from exc


def upsert_profile(db: Session, user_id: UUID, update: ProfileUpdate) -> Profile:
    try:
        profile = db.scalar(select(Profile).where(Profile.id == user_id))
        if profile is None:
            profile = Profile(id=user_id, account_role="learner")
            db.add(profile)

        for field, value in update.model_dump(
            exclude_unset=True,
            mode="json",
        ).items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)
        return profile
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileServiceError("Unable to save profile") from exc


def delete_profile(db: Session, user_id: UUID) -> bool:
    try:
        profile = db.scalar(select(Profile).where(Profile.id == user_id))
        if profile is None:
            return False

        db.delete(profile)
        db.commit()
        return True
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileServiceError("Unable to delete profile") from exc