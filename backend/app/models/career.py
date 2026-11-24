
import uuid

from sqlalchemy import Boolean, String, Text , ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship 

from app.db.base import Base
from app.db.mixins import TimestampMixin


class CareerRole(TimestampMixin, Base):
    __tablename__ = "career_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    interests: Mapped[list["LearnerInterest"]] = relationship(
        back_populates="career_role",
        cascade="all, delete-orphan",
    )


class LearnerInterest(TimestampMixin, Base):
    __tablename__ = "learner_interests"

    __table_args__ = (
        # One interest per learner and career role.
        UniqueConstraint(
          "learner_id",
          "career_role_id",
          name="uq_learner_interests_learner_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    career_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    career_role: Mapped["CareerRole"] = relationship(
        back_populates="interests",
    )
