from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class MetricValue(Base):
    __tablename__ = "metric_values"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_metric_id: Mapped[int] = mapped_column(
        ForeignKey("project_metrics.id")
    )

    value: Mapped[float] = mapped_column(Numeric)

    notes: Mapped[str | None] = mapped_column(Text())

    status: Mapped[str] = mapped_column(String(30))

    updated_by: Mapped[str | None] = mapped_column(String(100))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
