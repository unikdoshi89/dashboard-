from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.jira_configuration import JiraConfiguration
from app.models.project_qe_monthly_snapshot import (
    ProjectQEMonthlySnapshot,
)
from app.models.uploaded_test_case import UploadedTestCase

from app.api.routes.jira import (
    collect_jira_bug_metrics,
    collect_jira_feature_metrics,
)


def _get_snapshot_month():
    today = date.today()

    return date(
        today.year,
        today.month,
        1,
    )


def _calculate_automation_metrics(
    db: Session,
    project_id: int,
):
    """
    Calculate automation metrics from the latest
    uploaded test cases for the project.
    """

    latest_test_cases = (
        db.query(UploadedTestCase)
        .filter(
            UploadedTestCase.project_id
            == project_id
        )
        .order_by(
            UploadedTestCase.id.desc()
        )
        .all()
    )

    total_test_cases = len(
        latest_test_cases
    )

    automatable_test_cases = 0
    automated_test_cases = 0

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


async def create_or_update_qe_snapshot(
    db: Session,
    project_id: int,
):
    """
    Capture the current QE/Jira state for the
    current calendar month.

    If a snapshot already exists for the month,
    update it instead of creating a duplicate.
    """

    # ------------------------------------------------------------
    # Validate project
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Jira configuration
    # ------------------------------------------------------------

    jira_config = (
        db.query(JiraConfiguration)
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

    # ------------------------------------------------------------
    # Get Jira bugs
    # ------------------------------------------------------------

    jira_result = await search_jira_bugs(
        jira_url=jira_config.jira_url,
        jira_email=jira_config.jira_email,
        jira_api_token=jira_config.jira_api_token,
        jql=jira_config.jql,
        environment_field=(
            jira_config.environment_field
        ),
        max_results=200,
    )

    issues = jira_result.get(
        "issues",
        [],
    )

    total_bugs = len(issues)

    sit_bugs = 0
    uat_bugs = 0
    prod_bugs = 0

    for issue in issues:

        fields = issue.get(
            "fields",
            {},
        )

        environment = (
            _get_environment(
                fields=fields,
                environment_field=(
                    jira_config.environment_field
                ),
                uat_label=(
                    jira_config.uat_label
                ),
                prod_label=(
                    jira_config.prod_label
                ),
            )
        )

        if environment == "PROD":
            prod_bugs += 1

        elif environment == "UAT":
            uat_bugs += 1

        else:
            sit_bugs += 1

    # ------------------------------------------------------------
    # Automation
    # ------------------------------------------------------------

    automation_metrics = (
        _calculate_automation_metrics(
            db=db,
            project_id=project_id,
        )
    )

    # ------------------------------------------------------------
    # Current snapshot month
    # ------------------------------------------------------------

    snapshot_month = (
        _get_snapshot_month()
    )

    # ------------------------------------------------------------
    # Find existing snapshot
    # ------------------------------------------------------------

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

    if not snapshot:

        snapshot = ProjectQEMonthlySnapshot(
            project_id=project_id,
            snapshot_month=snapshot_month,
        )

        db.add(snapshot)

    # ------------------------------------------------------------
    # Update values
    # ------------------------------------------------------------

    snapshot.total_bugs = total_bugs
    snapshot.sit_bugs = sit_bugs
    snapshot.uat_bugs = uat_bugs
    snapshot.prod_bugs = prod_bugs

    # Feature count can be added using the existing
    # feature search once we wire that into the service.
    #
    # Keeping it zero here prevents us from duplicating
    # feature/JQL logic incorrectly.
    #
    # We will wire this to your existing feature endpoint
    # in the next step.

    snapshot.total_features = 0

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

    snapshot.snapshot_date = (
        datetime.utcnow()
    )

    db.commit()

    db.refresh(snapshot)

    return snapshot


def _get_environment(
    fields,
    environment_field=None,
    uat_label=None,
    prod_label=None,
):
    """
    Local environment classification for snapshots.
    """

    if environment_field:

        value = fields.get(
            environment_field
        )

        if isinstance(value, dict):

            value = (
                value.get("value")
                or value.get("name")
                or value.get("displayName")
            )

        if value:

            normalized = (
                str(value)
                .strip()
                .upper()
            )

            if normalized == "PROD":
                return "PROD"

            if normalized == "UAT":
                return "UAT"

            if normalized == "SIT":
                return "SIT"

    labels = fields.get(
        "labels"
    ) or []

    normalized_labels = {
        str(label).strip().lower()
        for label in labels
        if str(label).strip()
    }

    if prod_label:

        prod_labels = {
            x.strip().lower()
            for x in str(
                prod_label
            ).split(",")
            if x.strip()
        }

        if prod_labels & normalized_labels:
            return "PROD"

    if uat_label:

        uat_labels = {
            x.strip().lower()
            for x in str(
                uat_label
            ).split(",")
            if x.strip()
        }

        if uat_labels & normalized_labels:
            return "UAT"

    return "SIT"
