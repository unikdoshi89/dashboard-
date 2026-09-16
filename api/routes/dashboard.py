from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.models.project_metric import ProjectMetric
from app.models.metric_definition import MetricDefinition
from app.models.metric_category import MetricCategory
from app.models.metric_value import MetricValue


router = APIRouter()


@router.get("/{project_id}/dashboard")
def get_project_dashboard(
    project_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # Project
    # --------------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------

    rows = (
        db.query(
            ProjectMetric,
            MetricDefinition,
            MetricCategory,
            MetricValue,
        )
        .join(
            MetricDefinition,
            ProjectMetric.metric_definition_id
            == MetricDefinition.id,
        )
        .join(
            MetricCategory,
            MetricDefinition.category_id
            == MetricCategory.id,
        )
        .outerjoin(
            MetricValue,
            ProjectMetric.id
            == MetricValue.project_metric_id,
        )
        .filter(
            ProjectMetric.project_id == project_id,
            ProjectMetric.enabled.is_(True),
        )
        .order_by(
            MetricCategory.display_order,
            MetricDefinition.display_order,
        )
        .all()
    )

    categories = {}

    for (
        project_metric,
        definition,
        category,
        value,
    ) in rows:

        if category.id not in categories:

            categories[category.id] = {
                "category_id": category.id,
                "category_name": category.name,
                "metrics": [],
            }

        categories[category.id]["metrics"].append(
            {
                "project_metric_id": project_metric.id,

                "metric_definition_id": definition.id,

                "metric_key": definition.metric_key,

                "name": definition.name,

                "description": definition.description,

                "unit": definition.unit,

                "value": (
                    float(value.value)
                    if value
                    else None
                ),

                "target": float(
                    definition.default_target
                ),

                "warning": float(
                    definition.warning_threshold
                ),

                "critical": float(
                    definition.critical_threshold
                ),

                "direction": definition.direction,

                "status": (
                    value.status
                    if value
                    else "not_available"
                ),

                "notes": (
                    value.notes
                    if value
                    else None
                ),

                "updated_by": (
                    value.updated_by
                    if value
                    else None
                ),

                "updated_at": (
                    value.updated_at.isoformat()
                    if value
                    else None
                ),
            }
        )

    # --------------------------------------------------
    # Response
    # --------------------------------------------------

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "project_key": project.project_key,
            "description": project.description,
        },
        "categories": list(
            categories.values()
        ),
    }
