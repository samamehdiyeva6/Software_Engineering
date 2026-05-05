from __future__ import annotations

from fastapi import HTTPException, status

from database import (
    authenticate_user,
    create_project,
    create_user,
    delete_project,
    get_project_for_owner,
    get_projects_for_user,
    update_project,
)

from .schemas import LoginRequest, ProjectCreate, ProjectUpdate, RegisterRequest


def register_user(payload: RegisterRequest) -> dict:
    ok, message = create_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone=payload.phone or "",
        role=payload.role,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User was created, but the profile could not be loaded.",
        )
    return user


def login_user(payload: LoginRequest) -> dict:
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )
    return user


def list_projects(owner_user_id: int) -> list[dict]:
    return get_projects_for_user(owner_user_id)


def fetch_project(project_id: int, owner_user_id: int) -> dict:
    project = get_project_for_owner(project_id, owner_user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found for this user.",
        )
    return project


def create_project_record(payload: ProjectCreate) -> dict:
    ok, message, project_id = create_project(
        owner_user_id=payload.owner_user_id,
        title=payload.title,
        description=payload.description or "",
        customer_ref=payload.customer_ref or "",
        category=payload.category or "",
        start_date=payload.start_date.isoformat() if payload.start_date else "",
        end_date=payload.end_date.isoformat() if payload.end_date else "",
        budget_raw=str(payload.budget),
        status=payload.status,
    )
    if not ok or project_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return fetch_project(project_id, payload.owner_user_id)


def update_project_record(project_id: int, owner_user_id: int, payload: ProjectUpdate) -> dict:
    ok, message = update_project(
        project_id=project_id,
        owner_user_id=owner_user_id,
        title=payload.title,
        description=payload.description or "",
        customer_ref=payload.customer_ref or "",
        category=payload.category or "",
        start_date=payload.start_date.isoformat() if payload.start_date else "",
        end_date=payload.end_date.isoformat() if payload.end_date else "",
        budget_raw=str(payload.budget),
        status=payload.status,
    )
    if not ok:
        code = status.HTTP_404_NOT_FOUND if message == "Project not found or access denied." else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message)
    return fetch_project(project_id, owner_user_id)


def delete_project_record(project_id: int, owner_user_id: int) -> None:
    ok, message = delete_project(project_id, owner_user_id)
    if not ok:
        code = status.HTTP_404_NOT_FOUND if message == "Project not found or access denied." else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message)
