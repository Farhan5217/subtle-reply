from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from starlette.responses import Response

from app.deps.db import CurrentAsyncSession
from app.deps.users import CurrentUser
from app.models.project import Project
from app.schemas.project import Project as ProjectSchema
from app.schemas.project import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects")


@router.get("", response_model=List[ProjectSchema])
async def get_projects(
    response: Response,
    session: CurrentAsyncSession,
    user: CurrentUser,
) -> Any:
    # total = await session.scalar(select(func.count(Project.id).filter(Project.user_id == user.id)))
    projects = (await session.execute(select(Project).filter(Project.user_id == user.id))).scalars().all()
    return projects


@router.post("", response_model=ProjectSchema, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    session: CurrentAsyncSession,
    user: CurrentUser,
) -> Any:
    project = Project(**project_in.dict())
    project.user_id = user.id
    session.add(project)
    await session.commit()
    return project


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    session: CurrentAsyncSession,
    user: CurrentUser,
) -> Any:
    project: Optional[Project] = await session.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404)
    update_data = project_in.dict(exclude_unset=True)
    for field, value in update_data.projects():
        setattr(project, field, value)
    session.add(project)
    await session.commit()
    return project


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
) -> Any:
    project: Optional[Project] = await session.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
) -> Any:
    project: Optional[Project] = await session.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404)
    await session.delete(project)
    await session.commit()
    return {"success": True}
