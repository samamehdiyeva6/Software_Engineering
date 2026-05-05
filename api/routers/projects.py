from fastapi import APIRouter, Query

from ..schemas import APIMessage, ProjectCreate, ProjectListResponse, ProjectOut, ProjectUpdate
from ..services import (
    create_project_record,
    delete_project_record,
    fetch_project,
    list_projects,
    update_project_record,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
def get_projects(owner_user_id: int = Query(gt=0)) -> ProjectListResponse:
    return ProjectListResponse(projects=list_projects(owner_user_id))


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, owner_user_id: int = Query(gt=0)) -> ProjectOut:
    return ProjectOut(**fetch_project(project_id, owner_user_id))


@router.post("", response_model=ProjectOut, status_code=201)
def create_new_project(payload: ProjectCreate) -> ProjectOut:
    return ProjectOut(**create_project_record(payload))


@router.put("/{project_id}", response_model=ProjectOut)
def update_existing_project(
    project_id: int,
    payload: ProjectUpdate,
    owner_user_id: int = Query(gt=0),
) -> ProjectOut:
    return ProjectOut(**update_project_record(project_id, owner_user_id, payload))


@router.delete("/{project_id}", response_model=APIMessage)
def remove_project(project_id: int, owner_user_id: int = Query(gt=0)) -> APIMessage:
    delete_project_record(project_id, owner_user_id)
    return APIMessage(message="Project deleted successfully.")
