from sqlalchemy import ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class ProjectMetric(Base):
    __tablename__ = "project_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id")
    )

    metric_definition_id: Mapped[int] = mapped_column(
        ForeignKey("metric_definitions.id")
    )

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
