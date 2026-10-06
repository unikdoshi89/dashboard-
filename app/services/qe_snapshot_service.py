from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.jira_configuration import JiraConfiguration
from app.models.project_qe_monthly_snapshot import (
    ProjectQEMonthlySnapshot,
)
from app.models.uploaded_test_case import UploadedTestCase
from app.models.automation_upload_batch import (
    AutomationUploadBatch,
)

from app.api.routes.jira import (
    collect_jira_bug_metrics,
    collect_jira_feature_metrics,
)


# ============================================================
# Snapshot Month
# ============================================================

def _get_snapshot_month():
    """
    Return the first day of the current calendar month.

    Example:
        2026-10-06
        ->
        2026-10-01
    """

    today = date.today()

    return date(
        today.year,
        today.month,
        1,
    )


# ============================================================
# Automation Metrics
# ============================================================

def _calculate_automation_metrics(
    db: Session,
    project_id: int,
):
    """
    Calculate automation metrics from the latest
    uploaded test-case batch for the project.

    Metrics:
        - Total test cases
        - Automatable test cases
        - Automated test cases
        - Automation coverage
    """

    # --------------------------------------------------------
    # Find latest upload batch
    # --------------------------------------------------------

    latest_batch = (
        db.query(
            AutomationUploadBatch
        )
        .filter(
            AutomationUploadBatch.project_id
            == project_id
        )
        .order_by(
            AutomationUploadBatch.id.desc()
        )
        .first()
    )

    # --------------------------------------------------------
    # No automation upload yet
    # --------------------------------------------------------

    if not latest_batch:

        return {
            "total_test_cases": 0,
            "automatable_test_cases": 0,
            "automated_test_cases": 0,
            "automation_coverage": 0.0,
        }

    # --------------------------------------------------------
    # Get test cases belonging to latest batch
    # --------------------------------------------------------

    latest_test_cases = (
        db.query(
            UploadedTestCase
        )
        .filter(
            UploadedTestCase.project_id
            == project_id,

            UploadedTestCase.upload_batch_id
            == latest_batch.id,
        )
        .all()
    )

    total_test_cases = len(
        latest_test_cases
    )

    automatable_test_cases = 0
    automated_test_cases = 0

    # --------------------------------------------------------
    # Calculate automation counts
    # --------------------------------------------------------

    for test_case in latest_test_cases:

        automatable = (
            str(
                test_case.automatable
                or ""
            )
            .strip()
            .lower()
        )

        automated = (
            str(
                test_case.automated
                or ""
            )
            .strip()
            .lower()
        )

        if automatable in {
            "yes",
            "y",
            "true",
        }:
            automatable_test_cases += 1

        if automated in {
            "yes",
            "y",
            "true",
        }:
            automated_test_cases += 1

    # --------------------------------------------------------
    # Automation coverage
    #
    # Coverage is:
    #
    # Automated / Automatable * 100
    # --------------------------------------------------------

    if automatable_test_cases > 0:

        automation_coverage = (
            automated_test_cases
            / automatable_test_cases
        ) * 100

    else:

        automation_coverage = 0.0

    return {
        "total_test_cases": total_test_cases,

        "automatable_test_cases":
            automatable_test_cases,

        "automated_test_cases":
            automated_test_cases,

        "automation_coverage":
            round(
                automation_coverage,
                2,
            ),
    }


# ============================================================
# Create / Update QE Monthly Snapshot
# ============================================================

async def create_or_update_qe_snapshot(
    db: Session,
    project_id: int,
):
    """
    Capture the current QE/Jira state for the
    current calendar month.

    If a snapshot already exists for the month,
    update it instead of creating a duplicate.

    Jira metrics are collected using the same
    reusable logic as jira.py:

        SIT JQL
        UAT JQL
        PROD JQL

    The underlying Jira service handles pagination,
    so all Jira pages are fetched.
    """

    # ========================================================
    # Validate project
    # ========================================================

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
        )
        .first()
    )

    if not project:

        raise ValueError(
            "Project not found"
        )

    # ========================================================
    # Jira configuration
    # ========================================================

    jira_config = (
        db.query(
            JiraConfiguration
        )
        .filter(
            JiraConfiguration.project_id
            == project_id,

            JiraConfiguration.active.is_(True),
        )
        .first()
    )

    if not jira_config:

        raise ValueError(
            "Jira is not configured for this project"
        )

    # ========================================================
    # Jira Bug Metrics
    #
    # IMPORTANT:
    #
    # This uses the exact reusable Jira logic
    # added to jira.py.
    #
    # It handles:
    #
    #   SIT JQL
    #   UAT JQL
    #   PROD JQL
    #
    # and all Jira pagination.
    # ========================================================

    try:

        jira_metrics = (
            await collect_jira_bug_metrics(
                config=jira_config,
            )
        )

    except Exception as exc:

        raise ValueError(
            f"Unable to fetch Jira bug metrics: {str(exc)}"
        ) from exc

    total_bugs = jira_metrics.get(
        "total",
        0,
    )

    sit_bugs = jira_metrics.get(
        "sit_total",
        0,
    )

    uat_bugs = jira_metrics.get(
        "uat_total",
        0,
    )

    prod_bugs = jira_metrics.get(
        "prod_total",
        0,
    )

    # ========================================================
    # Jira Feature Metrics
    #
    # Uses the same feature JQL logic already present
    # in jira.py.
    #
    # This also uses the paginated Jira search service.
    # ========================================================

    try:

        feature_metrics = (
            await collect_jira_feature_metrics(
                config=jira_config,
            )
        )

    except Exception as exc:

        raise ValueError(
            f"Unable to fetch Jira feature metrics: {str(exc)}"
        ) from exc

    total_features = feature_metrics.get(
        "total",
        0,
    )

    # ========================================================
    # Automation Metrics
    # ========================================================

    automation_metrics = (
        _calculate_automation_metrics(
            db=db,
            project_id=project_id,
        )
    )

    # ========================================================
    # Current Snapshot Month
    # ========================================================

    snapshot_month = (
        _get_snapshot_month()
    )

    # ========================================================
    # Find Existing Snapshot
    # ========================================================

    snapshot = (
        db.query(
            ProjectQEMonthlySnapshot
        )
        .filter(
            ProjectQEMonthlySnapshot.project_id
            == project_id,

            ProjectQEMonthlySnapshot.snapshot_month
            == snapshot_month,
        )
        .first()
    )

    # ========================================================
    # Create Snapshot If It Does Not Exist
    # ========================================================

    if not snapshot:

        snapshot = (
            ProjectQEMonthlySnapshot(
                project_id=project_id,
                snapshot_month=snapshot_month,
            )
        )

        db.add(snapshot)

    # ========================================================
    # Update Jira Metrics
    # ========================================================

    snapshot.total_bugs = (
        total_bugs
    )

    snapshot.sit_bugs = (
        sit_bugs
    )

    snapshot.uat_bugs = (
        uat_bugs
    )

    snapshot.prod_bugs = (
        prod_bugs
    )

    snapshot.total_features = (
        total_features
    )

    # ========================================================
    # Update Automation Metrics
    # ========================================================

    snapshot.total_test_cases = (
        automation_metrics[
            "total_test_cases"
        ]
    )

    snapshot.automatable_test_cases = (
        automation_metrics[
            "automatable_test_cases"
        ]
    )

    snapshot.automated_test_cases = (
        automation_metrics[
            "automated_test_cases"
        ]
    )

    snapshot.automation_coverage = (
        automation_metrics[
            "automation_coverage"
        ]
    )

    # ========================================================
    # Snapshot Timestamp
    # ========================================================

    snapshot.snapshot_date = (
        datetime.utcnow()
    )

    # ========================================================
    # Save
    # ========================================================

    db.commit()

    db.refresh(
        snapshot
    )

    return snapshot
