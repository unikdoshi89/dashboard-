from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.project import Project

from app.models.automation_release import (
    AutomationRelease,
)

from app.models.automation_detail import (
    AutomationDetail,
    AutomationUploadBatch,
    UploadedTestCase,
)

from app.schemas.automation import (
    AutomationReleaseCreate,
    AutomationReleaseResponse,
    AutomationDetailCreate,
    AutomationDetailUpdate,
    AutomationDetailResponse,
)


router = APIRouter(
    prefix="/projects",
    tags=["Automation"],
)


# ============================================================
# Helpers
# ============================================================

def is_positive_value(value) -> bool:
    """
    Determine whether an uploaded Excel value represents YES.

    Supported values:
        Yes
        YES
        Y
        True
        TRUE
        1
        1.0
    """

    if value is None:
        return False

    normalized = str(value).strip().lower()

    return normalized in {
        "yes",
        "y",
        "true",
        "1",
        "1.0",
    }


def get_latest_release_upload(
    release_id: int,
    db: Session,
):
    """
    Get the latest automation Excel upload
    for a specific release.
    """

    return (
        db.query(AutomationUploadBatch)
        .filter(
            AutomationUploadBatch.release_id
            == release_id
        )
        .order_by(
            AutomationUploadBatch.uploaded_at.desc(),
            AutomationUploadBatch.id.desc(),
        )
        .first()
    )


def calculate_upload_metrics(
    upload_batch,
    db: Session,
):
    """
    Calculate automation metrics from the latest
    uploaded Excel for a release.

    Returns:

        requirements_rtb
        test_cases
        automatable
        automated
        jira_ids
    """

    rows = (
        db.query(UploadedTestCase)
        .filter(
            UploadedTestCase.upload_batch_id
            == upload_batch.id
        )
        .order_by(
            UploadedTestCase.sno,
            UploadedTestCase.id,
        )
        .all()
    )

    # ========================================================
    # Requirements + RTB
    #
    # Unique non-empty Jira IDs
    # ========================================================

    jira_ids = set()

    for row in rows:

        jira_id = row.jira_id

        if jira_id is None:
            continue

        jira_id = str(
            jira_id
        ).strip()

        if jira_id:
            jira_ids.add(
                jira_id
            )

    requirements_rtb = len(
        jira_ids
    )

    # ========================================================
    # Test Cases
    # ========================================================

    test_cases = len(
        rows
    )

    # ========================================================
    # Automatable / Automated
    # ========================================================

    automatable = 0
    automated = 0

    for row in rows:

        if is_positive_value(
            row.automatable
        ):
            automatable += 1

        if is_positive_value(
            row.automated
        ):
            automated += 1

    # ========================================================
    # Automation Percentage
    # ========================================================

    automation_percentage = (
        round(
            (
                automated
                / automatable
            ) * 100,
            2,
        )
        if automatable > 0
        else None
    )

    return {
        "requirements_rtb": requirements_rtb,
        "test_cases": test_cases,
        "automatable": automatable,
        "automated": automated,
        "automation_percentage":
            automation_percentage,
        "jira_ids": jira_ids,
    }


# ============================================================
# Automation Details
# ============================================================

@router.get(
    "/{project_id}/automation"
)
def get_automation_details(
    project_id: int,
    db: Session = Depends(get_db),
):

    # ========================================================
    # Validate Project
    # ========================================================

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # ========================================================
    # Get Releases
    # ========================================================

    releases = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.project_id
            == project_id
        )
        .order_by(
            AutomationRelease.release_order,
            AutomationRelease.id,
        )
        .all()
    )

    result = []

    # ========================================================
    # Project totals
    # ========================================================

    total_test_cases = 0
    total_automatable = 0
    total_automated = 0

    # Unique Jira IDs across uploaded releases
    uploaded_jira_ids = set()

    # Requirements from releases which don't
    # have an uploaded Excel
    manual_requirements = 0

    # ========================================================
    # Process Releases
    # ========================================================

    for release in releases:

        # ----------------------------------------------------
        # Get POD details
        # ----------------------------------------------------

        details = (
            db.query(AutomationDetail)
            .filter(
                AutomationDetail.release_id
                == release.id
            )
            .order_by(
                AutomationDetail.id
            )
            .all()
        )

        pod_data = []

        # ----------------------------------------------------
        # Existing POD totals
        # ----------------------------------------------------

        pod_requirements = 0
        pod_test_cases = 0
        pod_automatable = 0
        pod_automated = 0

        for detail in details:

            requirements = (
                detail.requirements_rtb
                or 0
            )

            test_cases = (
                detail.test_cases
                or 0
            )

            automatable = (
                detail.automatable
                or 0
            )

            automated = (
                detail.automated
                or 0
            )

            automation_percentage = (
                round(
                    (
                        automated
                        / automatable
                    ) * 100,
                    2,
                )
                if automatable > 0
                else None
            )

            pod_data.append(
                {
                    "id": detail.id,

                    "pod": detail.pod,

                    "requirements_rtb":
                        requirements,

                    "test_cases":
                        test_cases,

                    "automatable":
                        automatable,

                    "automated":
                        automated,

                    "automation_percentage":
                        automation_percentage,
                }
            )

            pod_requirements += (
                requirements
            )

            pod_test_cases += (
                test_cases
            )

            pod_automatable += (
                automatable
            )

            pod_automated += (
                automated
            )

        # ====================================================
        # Check latest Excel upload
        # ====================================================

        latest_upload = (
            get_latest_release_upload(
                release_id=release.id,
                db=db,
            )
        )

        # ====================================================
        # Uploaded Excel exists
        # ====================================================

        if latest_upload:

            metrics = (
                calculate_upload_metrics(
                    upload_batch=latest_upload,
                    db=db,
                )
            )

            release_requirements = (
                metrics[
                    "requirements_rtb"
                ]
            )

            release_test_cases = (
                metrics[
                    "test_cases"
                ]
            )

            release_automatable = (
                metrics[
                    "automatable"
                ]
            )

            release_automated = (
                metrics[
                    "automated"
                ]
            )

            release_percentage = (
                metrics[
                    "automation_percentage"
                ]
            )

            # Add Jira IDs to project-wide set
            uploaded_jira_ids.update(
                metrics[
                    "jira_ids"
                ]
            )

        # ====================================================
        # No Excel upload
        #
        # Keep existing POD behaviour.
        # ====================================================

        else:

            release_requirements = (
                pod_requirements
            )

            release_test_cases = (
                pod_test_cases
            )

            release_automatable = (
                pod_automatable
            )

            release_automated = (
                pod_automated
            )

            release_percentage = (
                round(
                    (
                        release_automated
                        / release_automatable
                    ) * 100,
                    2,
                )
                if release_automatable > 0
                else None
            )

            # These requirements are already manually
            # maintained, so they are added to the
            # project total separately.
            manual_requirements += (
                release_requirements
            )

        # ====================================================
        # Project totals
        # ====================================================

        total_test_cases += (
            release_test_cases
        )

        total_automatable += (
            release_automatable
        )

        total_automated += (
            release_automated
        )

        # ====================================================
        # Release result
        # ====================================================

        result.append(
            {
                "id": release.id,

                "release_name":
                    release.release_name,

                "release_order":
                    release.release_order,

                "pods":
                    pod_data,

                "total":
                    {
                        "requirements_rtb":
                            release_requirements,

                        "test_cases":
                            release_test_cases,

                        "automatable":
                            release_automatable,

                        "automated":
                            release_automated,

                        "automation_percentage":
                            release_percentage,
                    },

                # Useful for frontend
                "has_upload":
                    latest_upload is not None,

                "upload":
                    {
                        "id":
                            latest_upload.id,

                        "filename":
                            latest_upload.filename,

                        "row_count":
                            latest_upload.row_count,

                        "uploaded_at":
                            latest_upload.uploaded_at,
                    }
                    if latest_upload
                    else None,
            }
        )

    # ========================================================
    # Project Requirements + RTB
    #
    # Uploaded releases:
    #     unique Jira IDs
    #
    # Releases without uploads:
    #     existing manual requirement count
    # ========================================================

    total_requirements = (
        len(uploaded_jira_ids)
        + manual_requirements
    )

    # ========================================================
    # Overall Automation Coverage
    # ========================================================

    overall_percentage = (
        round(
            (
                total_automated
                / total_automatable
            ) * 100,
            2,
        )
        if total_automatable > 0
        else None
    )

    # ========================================================
    # Response
    # ========================================================

    return {

        "project": {

            "id":
                project.id,

            "name":
                project.name,

            "project_key":
                project.project_key,
        },

        "releases":
            result,

        "totals": {

            "requirements_rtb":
                total_requirements,

            "test_cases":
                total_test_cases,

            "automatable":
                total_automatable,

            "automated":
                total_automated,

            "automation_percentage":
                overall_percentage,
        },
    }


# ============================================================
# Automation Summary
# ============================================================

@router.get(
    "/{project_id}/automation/summary"
)
def get_automation_summary(
    project_id: int,
    db: Session = Depends(get_db),
):

    # ========================================================
    # Validate Project
    # ========================================================

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # ========================================================
    # Get Releases
    # ========================================================

    releases = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.project_id
            == project_id
        )
        .order_by(
            AutomationRelease.release_order,
            AutomationRelease.id,
        )
        .all()
    )

    result = []

    total_test_cases = 0
    total_automatable = 0
    total_automated = 0

    uploaded_jira_ids = set()
    manual_requirements = 0

    # ========================================================
    # Process Releases
    # ========================================================

    for release in releases:

        # ----------------------------------------------------
        # Existing POD details
        # ----------------------------------------------------

        details = (
            db.query(AutomationDetail)
            .filter(
                AutomationDetail.release_id
                == release.id
            )
            .order_by(
                AutomationDetail.id
            )
            .all()
        )

        pod_data = []

        pod_requirements = 0
        pod_test_cases = 0
        pod_automatable = 0
        pod_automated = 0

        for detail in details:

            requirements = (
                detail.requirements_rtb
                or 0
            )

            test_cases = (
                detail.test_cases
                or 0
            )

            automatable = (
                detail.automatable
                or 0
            )

            automated = (
                detail.automated
                or 0
            )

            automation_percentage = (
                round(
                    (
                        automated
                        / automatable
                    ) * 100,
                    2,
                )
                if automatable > 0
                else None
            )

            pod_data.append(
                {
                    "id":
                        detail.id,

                    "pod":
                        detail.pod,

                    "requirements_rtb":
                        requirements,

                    "test_cases":
                        test_cases,

                    "automatable":
                        automatable,

                    "automated":
                        automated,

                    "automation_percentage":
                        automation_percentage,
                }
            )

            pod_requirements += (
                requirements
            )

            pod_test_cases += (
                test_cases
            )

            pod_automatable += (
                automatable
            )

            pod_automated += (
                automated
            )

        # ====================================================
        # Latest release-level upload
        # ====================================================

        latest_upload = (
            get_latest_release_upload(
                release_id=release.id,
                db=db,
            )
        )

        if latest_upload:

            metrics = (
                calculate_upload_metrics(
                    upload_batch=latest_upload,
                    db=db,
                )
            )

            release_requirements = (
                metrics[
                    "requirements_rtb"
                ]
            )

            release_test_cases = (
                metrics[
                    "test_cases"
                ]
            )

            release_automatable = (
                metrics[
                    "automatable"
                ]
            )

            release_automated = (
                metrics[
                    "automated"
                ]
            )

            release_percentage = (
                metrics[
                    "automation_percentage"
                ]
            )

            uploaded_jira_ids.update(
                metrics[
                    "jira_ids"
                ]
            )

        else:

            release_requirements = (
                pod_requirements
            )

            release_test_cases = (
                pod_test_cases
            )

            release_automatable = (
                pod_automatable
            )

            release_automated = (
                pod_automated
            )

            release_percentage = (
                round(
                    (
                        release_automated
                        / release_automatable
                    ) * 100,
                    2,
                )
                if release_automatable > 0
                else None
            )

            manual_requirements += (
                release_requirements
            )

        # ====================================================
        # Project totals
        # ====================================================

        total_test_cases += (
            release_test_cases
        )

        total_automatable += (
            release_automatable
        )

        total_automated += (
            release_automated
        )

        # ====================================================
        # Release result
        # ====================================================

        result.append(
            {
                "id":
                    release.id,

                "release_name":
                    release.release_name,

                "release_order":
                    release.release_order,

                "pods":
                    pod_data,

                "total":
                    {
                        "requirements_rtb":
                            release_requirements,

                        "test_cases":
                            release_test_cases,

                        "automatable":
                            release_automatable,

                        "automated":
                            release_automated,

                        "automation_percentage":
                            release_percentage,
                    },

                "has_upload":
                    latest_upload is not None,
            }
        )

    # ========================================================
    # Overall requirements
    # ========================================================

    total_requirements = (
        len(uploaded_jira_ids)
        + manual_requirements
    )

    # ========================================================
    # Overall coverage
    # ========================================================

    overall_percentage = (
        round(
            (
                total_automated
                / total_automatable
            ) * 100,
            2,
        )
        if total_automatable > 0
        else None
    )

    # ========================================================
    # Response
    # ========================================================

    return {

        "project": {

            "id":
                project.id,

            "name":
                project.name,

            "project_key":
                project.project_key,
        },

        "releases":
            result,

        "totals": {

            "requirements_rtb":
                total_requirements,

            "test_cases":
                total_test_cases,

            "automatable":
                total_automatable,

            "automated":
                total_automated,

            "automation_percentage":
                overall_percentage,
        },
    }


# ============================================================
# CREATE RELEASE
# ============================================================

@router.post(
    "/{project_id}/automation/releases",
    response_model=AutomationReleaseResponse,
)
def create_automation_release(
    project_id: int,
    release_data: AutomationReleaseCreate,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    existing = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.project_id
            == project_id,
            AutomationRelease.release_name
            == release_data.release_name,
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Release already exists",
        )

    last_release = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.project_id
            == project_id
        )
        .order_by(
            AutomationRelease.release_order.desc()
        )
        .first()
    )

    release_order = (
        last_release.release_order + 1
        if last_release
        else 1
    )

    release = AutomationRelease(
        project_id=project_id,
        release_name=
            release_data.release_name,
        release_order=
            release_order,
    )

    db.add(release)

    db.commit()

    db.refresh(release)

    return release


# ============================================================
# CREATE POD DETAIL
# ============================================================

@router.post(
    "/automation/releases/{release_id}/details",
    response_model=AutomationDetailResponse,
)
def create_automation_detail(
    release_id: int,
    detail_data: AutomationDetailCreate,
    db: Session = Depends(get_db),
):

    release = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.id
            == release_id
        )
        .first()
    )

    if not release:

        raise HTTPException(
            status_code=404,
            detail="Release not found",
        )

    detail = AutomationDetail(

        release_id=
            release_id,

        pod=
            detail_data.pod,

        requirements_rtb=
            detail_data.requirements_rtb,

        test_cases=
            detail_data.test_cases,

        automatable=
            detail_data.automatable,

        automated=
            detail_data.automated,
    )

    db.add(detail)

    db.commit()

    db.refresh(detail)

    return detail


# ============================================================
# UPDATE POD DETAIL
# ============================================================

@router.put(
    "/automation/details/{detail_id}",
    response_model=AutomationDetailResponse,
)
def update_automation_detail(
    detail_id: int,
    detail_data: AutomationDetailUpdate,
    db: Session = Depends(get_db),
):

    detail = (
        db.query(AutomationDetail)
        .filter(
            AutomationDetail.id
            == detail_id
        )
        .first()
    )

    if not detail:

        raise HTTPException(
            status_code=404,
            detail="Automation detail not found",
        )

    updates = (
        detail_data.model_dump(
            exclude_unset=True
        )
    )

    for field, value in updates.items():

        setattr(
            detail,
            field,
            value,
        )

    db.commit()

    db.refresh(detail)

    return detail


# ============================================================
# DELETE POD DETAIL
# ============================================================

@router.delete(
    "/automation/details/{detail_id}"
)
def delete_automation_detail(
    detail_id: int,
    db: Session = Depends(get_db),
):

    detail = (
        db.query(AutomationDetail)
        .filter(
            AutomationDetail.id
            == detail_id
        )
        .first()
    )

    if not detail:

        raise HTTPException(
            status_code=404,
            detail="Automation detail not found",
        )

    db.delete(detail)

    db.commit()

    return {
        "message":
            "Automation detail deleted"
    }
