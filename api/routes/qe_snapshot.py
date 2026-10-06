from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.project import Project
from app.models.project_qe_monthly_snapshot import (
    ProjectQEMonthlySnapshot,
)

from app.services.qe_snapshot_service import (
    create_or_update_qe_snapshot,
)


router = APIRouter()


# ============================================================
# Create / Update Monthly Snapshot
# ============================================================

@router.post(
    "/projects/{project_id}/qe/snapshot"
)
async def create_qe_snapshot(
    project_id: int,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:

        snapshot = (
            await create_or_update_qe_snapshot(
                db=db,
                project_id=project_id,
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to create QE snapshot: "
                f"{str(exc)}"
            ),
        )

    return {
        "message": (
            "QE monthly snapshot "
            "created successfully."
        ),

        "snapshot": {
            "id": snapshot.id,

            "project_id":
                snapshot.project_id,

            "snapshot_month":
                snapshot.snapshot_month,

            "snapshot_date":
                snapshot.snapshot_date,

            "total_bugs":
                snapshot.total_bugs,

            "sit_bugs":
                snapshot.sit_bugs,

            "uat_bugs":
                snapshot.uat_bugs,

            "prod_bugs":
                snapshot.prod_bugs,

            "total_features":
                snapshot.total_features,

            "total_test_cases":
                snapshot.total_test_cases,

            "automatable_test_cases":
                snapshot.automatable_test_cases,

            "automated_test_cases":
                snapshot.automated_test_cases,

            "automation_coverage":
                snapshot.automation_coverage,
        },
    }


# ============================================================
# Get Historical Trends
# ============================================================

@router.get(
    "/projects/{project_id}/qe/trends"
)
def get_qe_trends(
    project_id: int,
    months: int = 6,
    db: Session = Depends(get_db),
):

    if months < 1:
        months = 1

    if months > 24:
        months = 24

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    snapshots = (
        db.query(
            ProjectQEMonthlySnapshot
        )
        .filter(
            ProjectQEMonthlySnapshot.project_id
            == project_id
        )
        .order_by(
            ProjectQEMonthlySnapshot
            .snapshot_month
            .desc()
        )
        .limit(months)
        .all()
    )

    snapshots.reverse()

    return {
        "project_id": project_id,

        "project_name": project.name,

        "months": len(snapshots),

        "trends": [
            {
                "id": snapshot.id,

                "snapshot_month":
                    snapshot.snapshot_month,

                "snapshot_date":
                    snapshot.snapshot_date,

                "total_bugs":
                    snapshot.total_bugs,

                "sit_bugs":
                    snapshot.sit_bugs,

                "uat_bugs":
                    snapshot.uat_bugs,

                "prod_bugs":
                    snapshot.prod_bugs,

                "total_features":
                    snapshot.total_features,

                "total_test_cases":
                    snapshot.total_test_cases,

                "automatable_test_cases":
                    snapshot.automatable_test_cases,

                "automated_test_cases":
                    snapshot.automated_test_cases,

                "automation_coverage":
                    snapshot.automation_coverage,
            }
            for snapshot in snapshots
        ],
    }
