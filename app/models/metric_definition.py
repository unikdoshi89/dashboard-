from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    ForeignKey,
)

from app.core.database import Base


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id = Column(
        Integer,
        primary_key=True
    )

    category_id = Column(
        Integer,
        ForeignKey(
            "metric_categories.id"
        ),
        nullable=False
    )

    metric_key = Column(
        String(100),
        unique=True,
        nullable=False
    )

    name = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    unit = Column(
        String(20),
        nullable=False
    )

    default_target = Column(
        Numeric,
        nullable=False
    )

    warning_threshold = Column(
        Numeric,
        nullable=False
    )

    critical_threshold = Column(
        Numeric,
        nullable=False
    )

    direction = Column(
        String(30),
        nullable=False
    )

    display_order = Column(
        Integer,
        nullable=False
    )

    weight = Column(
        Numeric(5, 2),
        nullable=False,
        default=0
    )
