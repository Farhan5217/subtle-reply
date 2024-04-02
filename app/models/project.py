from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi_users_db_sqlalchemy import GUID
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import (
    DateTime,
    Integer,
    String,
    Text,
)

from app.db import Base

if TYPE_CHECKING:
    from app.models.user import User  # noqa: F401


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String))

    user_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="projects")
    community_id: Mapped[UUID] = mapped_column(Integer, ForeignKey("communities.id"))
    community: Mapped["Community"] = relationship("Community", back_populates="projects")

    def __repr__(self):
        return f"<Project(id='{self.id}', title='{self.title}')>"


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    last_monitored: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="community")

    def __repr__(self):
        return f"<Community(name='{self.name}')>"


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    community_id: Mapped[int] = mapped_column(Integer, ForeignKey("communities.id"))
    community: Mapped["Community"] = relationship("Community", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(post_id='{self.post_id}', title='{self.title}')>"
