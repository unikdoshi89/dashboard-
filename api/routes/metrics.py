from fastapi import APIRouter


from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.project_metric import ProjectMetric
from app.models.metric_definition import MetricDefinition
from app.models.metric_value import MetricValue
from app.models.metric_history import MetricHistory



from app.utils.status_calculator import calculate_status
from app.models.project import Project
from app.schemas.metric import AddMetricRequest, MetricValueUpdate

router = APIRouter()

@router.put("/{project_metric_id}/value")
def update_metric_value(
    project_metric_id: int,
    request: MetricValueUpdate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # 1. Find project metric
    # --------------------------------------------------

    project_metric = (
        db.query(ProjectMetric)
        .filter(
            ProjectMetric.id
            == project_metric_id
        )
        .first()
    )

    if not project_metric:

        raise HTTPException(
            status_code=404,
            detail="Project metric not found",
        )

    # --------------------------------------------------
    # 2. Find metric definition
    # --------------------------------------------------

    definition = (
        db.query(MetricDefinition)
        .filter(
            MetricDefinition.id
            == project_metric.metric_definition_id
        )
        .first()
    )

    if not definition:

        raise HTTPException(
            status_code=404,
            detail="Metric definition not found",
        )

    # --------------------------------------------------
    # 3. Find current value
    # --------------------------------------------------

    metric_value = (
        db.query(MetricValue)
        .filter(
            MetricValue.project_metric_id
            == project_metric_id
        )
        .first()
    )

    # --------------------------------------------------
    # 4. Save current value to history
    # --------------------------------------------------

    if metric_value:

        history = MetricHistory(
            project_metric_id=project_metric_id,
            value=metric_value.value,
            notes=metric_value.notes,
            changed_by=request.updated_by,
        )

        db.add(history)

    # --------------------------------------------------
    # 5. Calculate status
    # --------------------------------------------------

    status = calculate_status(
        request.value,
        definition.default_target,
        definition.warning_threshold,
        definition.critical_threshold,
        definition.direction,
    )

    # --------------------------------------------------
    # 6. Create or update metric value
    # --------------------------------------------------

    if not metric_value:

        metric_value = MetricValue(
            project_metric_id=project_metric_id,
        )

        db.add(metric_value)

    metric_value.value = request.value
    metric_value.status = status
    metric_value.notes = request.notes
    metric_value.updated_by = request.updated_by

    # --------------------------------------------------
    # 7. Commit
    # --------------------------------------------------

    db.commit()

    db.refresh(metric_value)

    # --------------------------------------------------
    # 8. Response
    # --------------------------------------------------

    return {
        "project_metric_id": project_metric_id,
        "metric": definition.name,
        "value": float(metric_value.value),
        "unit": definition.unit,
        "status": metric_value.status,
        "notes": metric_value.notes,
        "updated_by": metric_value.updated_by,
        "message": "Metric value updated successfully",
    }


@router.get("/{project_metric_id}/history")
def get_metric_history(
    project_metric_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # 1. Find project metric
    # --------------------------------------------------

    project_metric = (
        db.query(ProjectMetric)
        .filter(
            ProjectMetric.id == project_metric_id
        )
        .first()
    )

    if not project_metric:

        raise HTTPException(
            status_code=404,
            detail="Project metric not found",
        )

    # --------------------------------------------------
    # 2. Get metric definition
    # --------------------------------------------------

    definition = (
        db.query(MetricDefinition)
        .filter(
            MetricDefinition.id
            == project_metric.metric_definition_id
        )
        .first()
    )

    if not definition:

        raise HTTPException(
            status_code=404,
            detail="Metric definition not found",
        )

    # --------------------------------------------------
    # 3. Get current value
    # --------------------------------------------------

    current_value = (
        db.query(MetricValue)
        .filter(
            MetricValue.project_metric_id
            == project_metric_id
        )
        .first()
    )

    # --------------------------------------------------
    # 4. Get history
    # --------------------------------------------------

    history_records = (
        db.query(MetricHistory)
        .filter(
            MetricHistory.project_metric_id
            == project_metric_id
        )
        .order_by(
            MetricHistory.recorded_at.desc()
        )
        .all()
    )

    # --------------------------------------------------
    # 5. Response
    # --------------------------------------------------

    return {
        "project_metric_id": project_metric_id,

        "metric_definition_id": definition.id,

        "metric_key": definition.metric_key,

        "metric": definition.name,

        "unit": definition.unit,

        "current_value": (
            float(current_value.value)
            if current_value
            else None
        ),

        "current_status": (
            current_value.status
            if current_value
            else "not_available"
        ),

        "history": [
            {
                "id": record.id,

                "value": float(
                    record.value
                ),

                "notes": record.notes,

                "changed_by": record.changed_by,

                "recorded_at": (
                    record.recorded_at.isoformat()
                ),
            }

            for record in history_records
        ],
    }

@router.delete("/{project_metric_id}")
def delete_metric(
    project_metric_id: int,
    db: Session = Depends(get_db),
):

    project_metric = (
        db.query(ProjectMetric)
        .filter(
            ProjectMetric.id
            == project_metric_id
        )
        .first()
    )

    if not project_metric:

        raise HTTPException(
            status_code=404,
            detail="Project metric not found",
        )

    if not project_metric.enabled:

        raise HTTPException(
            status_code=400,
            detail="Metric is already disabled",
        )

    project_metric.enabled = False

    db.commit()

    return {
        "project_metric_id": project_metric_id,
        "message": "Metric removed from project successfully",
    }
