from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JiraConfiguration(Base):
    __tablename__ = "jira_configurations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    jira_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    jira_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    jira_api_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    jql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    feature_jql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    uat_label: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    prod_label: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
     environment_field: Mapped[str | None] = mapped_column(
    String(150),
    nullable=True,
)

uat_environment: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
)

prod_environment: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
)
