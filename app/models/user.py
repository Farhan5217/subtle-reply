from datetime import datetime
from typing import TYPE_CHECKING, List

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseOAuthAccountTableUUID, SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import (
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey

from app.db import Base

if TYPE_CHECKING:
    from app.models.project import Project  # noqa: F401


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    @declared_attr
    def user_id(cls) -> Mapped[GUID]:
        return mapped_column(GUID, ForeignKey("users.id", ondelete="cascade"), nullable=False)


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    # id, email and hashed_password are already in SQLAlchemyBaseUserTableUUID
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # subscription_plan: Mapped[str] = mapped_column(String, default="basic", nullable=False)

    projects: Mapped["Project"] = relationship(back_populates="users", cascade="all, delete")
    oauth_accounts: Mapped[List[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.email!r})"
