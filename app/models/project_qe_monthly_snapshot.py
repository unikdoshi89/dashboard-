from datetime import datetime, date

from sqlalchemy import (
    Integer,
    Float,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectQEMonthlySnapshot(Base):

    __tablename__ = "project_qe_monthly_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "snapshot_month",
            name="uq_project_qe_snapshot_month",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # First day of the month.
    # Example: 2026-10-01
    snapshot_month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ------------------------------------------------------------
    # Jira / Bug metrics
    # ------------------------------------------------------------

    total_bugs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    sit_bugs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    uat_bugs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    prod_bugs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------
    # Feature metrics
    # ------------------------------------------------------------

    total_features: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------
    # Automation metrics
    # ------------------------------------------------------------

    total_test_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    automatable_test_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    automated_test_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    automation_coverage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
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
