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

    # ============================================================
    # Jira Connection
    # ============================================================

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

    # ============================================================
    # Existing JQL
    #
    # Kept for backward compatibility and feature JQL generation.
    # ============================================================

    jql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    feature_jql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ============================================================
    # Environment-specific JQL
    # ============================================================

    sit_jql: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    uat_jql: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prod_jql: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ============================================================
    # Existing label configuration
    # ============================================================

    uat_label: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    prod_label: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # ============================================================
    # Optional Jira environment field
    #
    # This is retained for display/classification when Jira
    # actually returns the field.
    # ============================================================

    environment_field: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # ============================================================
    # Status / timestamps
    # ============================================================

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
