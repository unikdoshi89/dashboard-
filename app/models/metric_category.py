from sqlalchemy import Column, Integer, String, Numeric
from app.core.database import Base


class MetricCategory(Base):
    __tablename__ = "metric_categories"

    id = Column(Integer, primary_key=True)

    name = Column(
        String(150),
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
