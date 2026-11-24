import re
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EducationEntry(BaseModel):
    degree: str | None = Field(default=None, max_length=150)
    institution: str | None = Field(default=None, max_length=255)
    year: int | None = Field(default=None, ge=1900, le=2100)

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)


class ExperienceEntry(BaseModel):
    company: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None, max_length=150)
    duration_months: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=5000)

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    education: list[EducationEntry] | None = None
    experience: list[ExperienceEntry] | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        phone = value.strip()
        if not re.fullmatch(r"\+?[0-9().\s-]+", phone):
            raise ValueError("Enter a valid phone number.")

        digits = sum(character.isdigit() for character in phone)
        if not 7 <= digits <= 15:
            raise ValueError("Phone number must contain between 7 and 15 digits.")

        return phone


class ProfileResponse(BaseModel):
    id: UUID
    full_name: str | None
    phone: str | None
    location: str | None
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    account_role: Literal["learner", "admin"]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("education", "experience", mode="before")
    @classmethod
    def normalize_json_list(cls, value: Any) -> Any:
        # Accept legacy single-object JSON while returning the contract's array shape.
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        return value