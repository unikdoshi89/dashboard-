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


class AutomationRelease(Base):

    __tablename__ = "automation_releases"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
    )

    release_name = Column(
        String(200),
        nullable=False,
    )

    release_order = Column(
        Integer,
        nullable=False,
        default=0,
    )
