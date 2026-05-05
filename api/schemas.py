from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database import is_valid_email_format, normalize_email

UserRole = Literal["customer", "worker"]
ProjectStatus = Literal["draft", "published", "active", "completed", "cancelled"]


class APIMessage(BaseModel):
    message: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: str | None = None
    role: UserRole
    created_at: str | None = None


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=3, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    role: UserRole = "customer"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = normalize_email(value)
        if not is_valid_email_format(normalized):
            raise ValueError("Email format is invalid.")
        return normalized

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned.split()) < 2:
            raise ValueError("Full name must include at least name and surname.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = normalize_email(value)
        if not is_valid_email_format(normalized):
            raise ValueError("Email format is invalid.")
        return normalized


class AuthResponse(BaseModel):
    message: str
    user: UserOut


class ProjectBase(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=3000)
    customer_ref: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    end_date: date | None = None
    budget: float = Field(ge=0)
    status: ProjectStatus = "published"

    @field_validator("title", "description", "customer_ref", "category")
    @classmethod
    def strip_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: date | None, info) -> date | None:
        start_date = info.data.get("start_date")
        if value and start_date and value < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        return value


class ProjectCreate(ProjectBase):
    owner_user_id: int = Field(gt=0)


class ProjectUpdate(ProjectBase):
    pass


class ProjectOut(BaseModel):
    id: int
    owner_user_id: int
    title: str
    description: str | None = None
    customer_ref: str | None = None
    category: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    budget: float
    status: ProjectStatus
    created_at: str | None = None
    updated_at: str | None = None


class ProjectListResponse(BaseModel):
    projects: list[ProjectOut]

