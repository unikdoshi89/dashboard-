from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey,
    Text,
)

from app.core.database import Base


class AutomationDetail(Base):
    __tablename__ = "automation_details"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    release_id = Column(
        Integer,
        ForeignKey("automation_releases.id"),
        nullable=False,
    )

    pod = Column(
        String(100),
        nullable=False,
    )

    requirements_rtb = Column(
        Integer,
        nullable=False,
        default=0,
    )

    test_cases = Column(
        Integer,
        nullable=False,
        default=0,
    )

    automatable = Column(
        Integer,
        nullable=False,
        default=0,
    )

    automated = Column(
        Integer,
        nullable=False,
        default=0,
    )


class AutomationUploadBatch(Base):
    __tablename__ = "automation_upload_batches"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Nullable for backward compatibility with existing
    # project-level uploads.
    release_id = Column(
        Integer,
        ForeignKey("automation_releases.id"),
        nullable=True,
        index=True,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    row_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class UploadedTestCase(Base):
    __tablename__ = "uploaded_test_cases"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    upload_batch_id = Column(
        Integer,
        ForeignKey("automation_upload_batches.id"),
        nullable=False,
        index=True,
    )

    sheet_name = Column(
        String(150),
        nullable=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    sno = Column(Integer, nullable=True)

    comment = Column(Text, nullable=True)

    owner = Column(String(150), nullable=True)

    jira_id = Column(
        String(150),
        nullable=True,
        index=True,
    )

    test_case_id = Column(
        String(150),
        nullable=False,
        index=True,
    )

    pre_condition = Column(Text, nullable=True)

    test_case_description = Column(
        Text,
        nullable=True,
    )

    steps = Column(Text, nullable=True)

    expected_result = Column(Text, nullable=True)

    status = Column(String(50), nullable=True)

    automatable = Column(
        String(20),
        nullable=True,
    )

    automated = Column(
        String(20),
        nullable=True,
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
