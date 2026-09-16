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

@router.get(
    "/{project_id}/automation"
)
def get_automation_details(
    project_id: int,
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

    total_requirements = 0
    total_test_cases = 0
    total_automatable = 0
    total_automated = 0


    for release in releases:

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


        for detail in details:

            total_requirements += (
                detail.requirements_rtb
            )

            total_test_cases += (
                detail.test_cases
            )

            total_automatable += (
                detail.automatable
            )

            total_automated += (
                detail.automated
            )


            pod_data.append({

                "id": detail.id,

                "pod": detail.pod,

                "requirements_rtb":
                    detail.requirements_rtb,

                "test_cases":
                    detail.test_cases,

                "automatable":
                    detail.automatable,

                "automated":
                    detail.automated,

                "automation_percentage":
                    (
                        round(
                            (
                                detail.automated
                                / detail.automatable
                            ) * 100,
                            2,
                        )
                        if detail.automatable > 0
                        else None
                    ),
            })


        result.append({

            "id": release.id,

            "release_name":
                release.release_name,

            "release_order":
                release.release_order,

            "pods": pod_data,

        })


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


    return {

        "project": {

            "id": project.id,

            "name": project.name,

            "project_key":
                project.project_key,

        },

        "releases": result,

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

@router.get(
    "/{project_id}/automation/summary"
)
def get_automation_summary(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    releases = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.project_id == project_id
        )
        .order_by(
            AutomationRelease.release_order,
            AutomationRelease.id,
        )
        .all()
    )

    result = []

    total_requirements = 0
    total_test_cases = 0
    total_automatable = 0
    total_automated = 0

    for release in releases:

        details = (
            db.query(AutomationDetail)
            .filter(
                AutomationDetail.release_id == release.id
            )
            .order_by(
                AutomationDetail.id
            )
            .all()
        )

        pod_data = []

        release_requirements = 0
        release_test_cases = 0
        release_automatable = 0
        release_automated = 0

        for detail in details:

            requirements = detail.requirements_rtb or 0
            test_cases = detail.test_cases or 0
            automatable = detail.automatable or 0
            automated = detail.automated or 0

            automation_percentage = (
                round(
                    (automated / automatable) * 100,
                    2,
                )
                if automatable > 0
                else None
            )

            pod_data.append(
                {
                    "id": detail.id,
                    "pod": detail.pod,
                    "requirements_rtb": requirements,
                    "test_cases": test_cases,
                    "automatable": automatable,
                    "automated": automated,
                    "automation_percentage":
                        automation_percentage,
                }
            )

            release_requirements += requirements
            release_test_cases += test_cases
            release_automatable += automatable
            release_automated += automated

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

        result.append(
            {
                "id": release.id,
                "release_name": release.release_name,
                "release_order": release.release_order,
                "pods": pod_data,
                "total": {
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
            }
        )

        total_requirements += release_requirements
        total_test_cases += release_test_cases
        total_automatable += release_automatable
        total_automated += release_automated

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

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "project_key": project.project_key,
        },
        "releases": result,
        "totals": {
            "requirements_rtb": total_requirements,
            "test_cases": total_test_cases,
            "automatable": total_automatable,
            "automated": total_automated,
            "automation_percentage":
                overall_percentage,
        },
    }

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

        release_id=release_id,

        pod=detail_data.pod,

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
