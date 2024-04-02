from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    email: str
    subscription_plan: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class UserCreate(schemas.BaseUserCreate):
    username: str
    email: str
    password: str
    subscription_plan: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class ProjectCreate(BaseModel):
    title: str
    description: str


class CommunityCreate(BaseModel):
    project_id: int
    name: str


class KeywordCreate(BaseModel):
    project_id: int
    keyword: str


class UserUpdate(schemas.BaseUserUpdate):
    pass
