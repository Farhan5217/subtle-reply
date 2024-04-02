from datetime import datetime
from typing import List

from pydantic import UUID4, BaseModel


class ProjectCreate(BaseModel):
    title: str
    description: str
    keywords: List[str] = []
    communities: List[str] = []


class ProjectUpdate(ProjectCreate):
    pass


class Project(BaseModel):
    id: int
    title: str
    description: str
    keywords: List[str] = []
    communities: List[str] = []

    created: datetime
    updated: datetime
    user_id: UUID4

    class Config:
        from_attributes = True
