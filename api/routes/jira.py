import re

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.project import Project
from app.models.jira_configuration import JiraConfiguration

from app.schemas.project import (
    JiraConfigurationCreate,
    JiraConfigurationResponse,
)

from app.services.jira_service import (
    test_jira_connection,
    search_jira_bugs, search_jira_features,
)


router = APIRouter(
    prefix="/projects",
    tags=["Jira"],
)


# ============================================================
# Helpers
# ============================================================

def get_environment_from_labels(labels):
    """
    Determine environment from Jira labels.

    Supported labels:
        SIT
        UAT
        PROD

    Example:
        ["regression", "SIT"] -> SIT
    """

    if not labels:
        return None

    environment_labels = {
        "SIT",
        "UAT",
        "PROD",
    }

    for label in labels:
        normalized = str(label).strip().upper()

        if normalized in environment_labels:
            return normalized

    return None


def build_search_jql(
    base_jql: str,
    search: str | None,
):
    """
    Add Jira ID or keyword search to the
    project's configured JQL.
    """

    if not search:
        return base_jql

    search = search.strip()

    if not search:
        return base_jql

    # Escape characters used inside JQL strings
    escaped_search = (
        search
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    # Jira issue key:
    # ABC-123
    if re.match(
        r"^[A-Za-z][A-Za-z0-9_]*-\d+$",
        search,
    ):
        return (
            f"({base_jql}) "
            f'AND key = "{escaped_search}"'
        )

    # Keyword search
    return (
        f"({base_jql}) "
        f'AND text ~ "\\"{escaped_search}\\""'
    )


# ============================================================
# GET Jira Configuration
# ============================================================

@router.get(
    "/{project_id}/jira/config",
)
def get_jira_config(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get Jira configuration for a project.

    IMPORTANT:
    API token is never returned to frontend.
    """

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

    config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id
            == project_id
        )
        .first()
    )

    if not config:
        return {
            "configured": False,
            "project_id": project_id,
            "jira_url": "",
            "jira_email": "",
            "jql": "",
            "active": False,
        }

    return {
        "configured": True,
        "project_id": project_id,
        "jira_url": config.jira_url,
        "jira_email": config.jira_email,
        "jql": config.jql,
        "active": config.active,

        # Never return the real token
        "has_api_token": bool(
            config.jira_api_token
        ),
    }


# ============================================================
# CREATE / UPDATE Jira Configuration
# ============================================================

@router.post(
    "/{project_id}/jira/config",
)
def create_or_update_jira_config(
    project_id: int,
    config_data: JiraConfigurationCreate,
    db: Session = Depends(get_db),
):
    """
    Create or update Jira configuration
    for a project.
    """

    # ---------------------------------------------------------
    # Validate project
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Basic validation
    # ---------------------------------------------------------

    if not config_data.jira_url.strip():
        raise HTTPException(
            status_code=400,
            detail="Jira URL is required",
        )

    if not config_data.jira_email.strip():
        raise HTTPException(
            status_code=400,
            detail="Jira email is required",
        )

    if not config_data.jql.strip():
        raise HTTPException(
            status_code=400,
            detail="JQL is required",
        )

    if not config_data.uat_label.strip():
        raise HTTPException(
            status_code=400,
            detail="UAT issue label is required",
        )

    if not config_data.prod_label.strip():
        raise HTTPException(
            status_code=400,
            detail="Production issue label is required",
        )

    # ---------------------------------------------------------
    # Find existing configuration
    # ---------------------------------------------------------

    config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id
            == project_id
        )
        .first()
    )

    # ---------------------------------------------------------
    # UPDATE existing configuration
    # ---------------------------------------------------------

    if config:

        config.jira_url = (
            config_data.jira_url.strip()
        )

        config.jira_email = (
            config_data.jira_email.strip()
        )

        # Only update API token when a new token
        # has been supplied.
        if (
            config_data.jira_api_token
            and config_data.jira_api_token.strip()
        ):
            config.jira_api_token = (
                config_data.jira_api_token.strip()
            )

        config.jql = (
            config_data.jql.strip()
        )

        # Project-specific UAT label
        config.uat_label = (
            config_data.uat_label.strip()
        )

        # Project-specific Production label
        config.prod_label = (
            config_data.prod_label.strip()
        )

        config.active = (
            config_data.active
        )

    # ---------------------------------------------------------
    # CREATE new configuration
    # ---------------------------------------------------------

    else:

        if not config_data.jira_api_token.strip():
            raise HTTPException(
                status_code=400,
                detail="Jira API token is required",
            )

        config = JiraConfiguration(
            project_id=project_id,

            jira_url=(
                config_data.jira_url.strip()
            ),

            jira_email=(
                config_data.jira_email.strip()
            ),

            jira_api_token=(
                config_data.jira_api_token.strip()
            ),

            jql=(
                config_data.jql.strip()
            ),

            # Project-specific UAT label
            uat_label=(
                config_data.uat_label.strip()
            ),

            # Project-specific Production label
            prod_label=(
                config_data.prod_label.strip()
            ),

            active=(
                config_data.active
            ),
        )

        db.add(config)

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    db.commit()
    db.refresh(config)

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return {
        "success": True,
        "message": (
            "Jira configuration saved successfully"
        ),
        "project_id": project_id,
        "jira_url": config.jira_url,
        "jira_email": config.jira_email,
        "jql": config.jql,

        # Return configured labels
        "uat_label": config.uat_label,
        "prod_label": config.prod_label,

        "active": config.active,

        # Never return the actual API token
        "has_api_token": bool(
            config.jira_api_token
        ),
    }

# ============================================================
# Test Jira Connection
# ============================================================

@router.post(
    "/{project_id}/jira/test-connection",
)
async def test_project_jira_connection(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Test the Jira configuration already stored
    for the project.
    """

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

    config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id
            == project_id
        )
        .first()
    )

    if not config:
        raise HTTPException(
            status_code=404,
            detail=(
                "Jira is not configured "
                "for this project"
            ),
        )

    try:

        result = await test_jira_connection(
            jira_url=config.jira_url,
            jira_email=config.jira_email,
            jira_api_token=config.jira_api_token,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to connect to Jira: {str(exc)}"
            ),
        )

    if not result["success"]:

        raise HTTPException(
            status_code=401,
            detail=(
                "Jira authentication failed. "
                "Please verify Jira URL, email "
                "and API token."
            ),
        )

    return {
        "success": True,
        "message": "Jira connection successful",
        "display_name": result.get(
            "display_name"
        ),
    }


# ============================================================
# GET Jira Bugs
# ============================================================

@router.get(
    "/{project_id}/jira/bugs",
)
async def get_jira_bugs(
    project_id: int,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=5, le=200),
    db: Session = Depends(get_db),
):
    """
    Get Jira bugs for a project.

    The project's configured JQL is used as
    the base query.

    Optional search:
        Jira ID:
            ABC-123

        Keyword:
            login

    Issues are classified using the
    project-specific UAT and Production labels.
    """

    # ========================================================
    # 1. Validate project
    # ========================================================

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

    # ========================================================
    # 2. Get active Jira configuration
    # ========================================================

    config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id == project_id,
            JiraConfiguration.active.is_(True),
        )
        .first()
    )


    # Jira is not configured
    if not config:
        return {
            "configured": False,
            "project_id": project_id,
            "project_name": project.name,
            "total": 0,
            "uat_total": 0,
            "prod_total": 0,
            "bugs": [],
            "uat_bugs": [],
            "prod_bugs": [],
        }

    # ========================================================
    # 3. Validate Jira configuration
    # ========================================================

    if not config.jira_url.strip():
        raise HTTPException(
            status_code=500,
            detail="Jira URL is not configured.",
        )

    if not config.jira_email.strip():
        raise HTTPException(
            status_code=500,
            detail="Jira email is not configured.",
        )

    if not config.jira_api_token.strip():
        raise HTTPException(
            status_code=500,
            detail="Jira API token is not configured.",
        )

    if not config.jql.strip():
        raise HTTPException(
            status_code=500,
            detail="Jira JQL is not configured.",
        )

    # ========================================================
    # 4. Validate environment labels
    # ========================================================

    if not config.uat_label or not config.uat_label.strip():
        raise HTTPException(
            status_code=500,
            detail=(
                "UAT issue label is not configured "
                "for this project."
            ),
        )

    if not config.prod_label or not config.prod_label.strip():
        raise HTTPException(
            status_code=500,
            detail=(
                "Production issue label is not configured "
                "for this project."
            ),
        )

    # ========================================================
    # 5. Build JQL
    # ========================================================

    jql = build_search_jql(
        config.jql,
        search,
    )

    # ========================================================
    # 6. Fetch Jira issues
    # ========================================================

    try:

        jira_data = await search_jira_bugs(
            jira_url=config.jira_url,
            jira_email=config.jira_email,
            jira_api_token=config.jira_api_token,
            jql=jql,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to fetch Jira bugs: {str(exc)}"
            ),
        )

    # ========================================================
    # 7. Prepare response lists
    # ========================================================

    bugs = []
    uat_bugs = []
    prod_bugs = []

    # ========================================================
    # 8. Process Jira issues
    # ========================================================

    for issue in jira_data.get("issues", []):

        fields = issue.get(
            "fields",
            {},
        )

        # ----------------------------------------------------
        # Jira labels
        # ----------------------------------------------------

        labels = fields.get("labels") or []

        # ----------------------------------------------------
        # Determine environment
        # ----------------------------------------------------

        environment = get_issue_environment(
            labels=labels,
            uat_label=config.uat_label,
            prod_label=config.prod_label,
        )

        # ----------------------------------------------------
        # Jira objects
        # ----------------------------------------------------

        assignee = fields.get("assignee")
        reporter = fields.get("reporter")
        status = fields.get("status")
        priority = fields.get("priority")

        # ----------------------------------------------------
        # Create normalized bug object
        # ----------------------------------------------------

        bug = {
            "jira_id": issue.get("key"),

            "summary": fields.get(
                "summary"
            ),

            "status": (
                status.get("name")
                if status
                else None
            ),

            "priority": (
                priority.get("name")
                if priority
                else None
            ),

            "assignee": (
                assignee.get("displayName")
                if assignee
                else None
            ),

            "reporter": (
                reporter.get("displayName")
                if reporter
                else None
            ),

            "created": fields.get(
                "created"
            ),

            "updated": fields.get(
                "updated"
            ),

            "environment": environment,

            "labels": labels,
        }

        # ----------------------------------------------------
        # Add to all bugs
        # ----------------------------------------------------

        bugs.append(bug)

        # ----------------------------------------------------
        # Add to environment-specific lists
        # ----------------------------------------------------

        if environment == "UAT":

            uat_bugs.append(bug)

        elif environment == "PROD":

            prod_bugs.append(bug)

    # ========================================================
    # 9. Return response
    # ========================================================
        # Pagination
        total = len(bugs)
        start = (page - 1) * per_page
        end = start + per_page

        paged_bugs = bugs[start:end]
        paged_uat = uat_bugs[start:end]
        paged_prod = prod_bugs[start:end]
    return {
        "configured": True,
        "project_id": project_id,
        "project_name": project.name,
        "jql": jql,

        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total // per_page) + (1 if total % per_page else 0),

        "bugs": paged_bugs,
        "uat_bugs": paged_uat,
        "prod_bugs": paged_prod,
    }

# def get_issue_environment(
#     labels,
#     uat_label,
#     prod_label,
# ):
#     """
#     Determine Jira issue environment using
#     project-specific labels.
#     """
#
#     if not labels:
#         return None
#
#     normalized_labels = {
#         str(label).strip().lower()
#         for label in labels
#     }
#
#     configured_uat_label = (
#         str(uat_label).strip().lower()
#     )
#
#     configured_prod_label = (
#         str(prod_label).strip().lower()
#     )
#
#     if configured_uat_label in normalized_labels:
#         return "UAT"
#
#     if configured_prod_label in normalized_labels:
#         return "PROD"
#
#     return None

def get_issue_environment(labels, uat_label, prod_label):
    """
    Determine Jira issue environment using multiple project-specific labels.
    Supports comma-separated labels OR single labels.
    """

    if not labels:
        return None

    # Normalize all labels from Jira issue
    normalized_labels = {
        str(label).strip().lower() for label in labels
    }

    # Convert configured labels to lists (split by comma)
    uat_labels = [
        l.strip().lower()
        for l in str(uat_label).split(",")
        if l.strip()
    ]

    prod_labels = [
        l.strip().lower()
        for l in str(prod_label).split(",")
        if l.strip()
    ]

    # Check UAT matches
    for u_label in uat_labels:
        if u_label in normalized_labels:
            return "UAT"

    # Check PROD matches
    for p_label in prod_labels:
        if p_label in normalized_labels:
            return "PROD"

    return None

@router.get("/{project_id}/jira/features")
async def get_jira_features(
    project_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=5, le=200),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    config = db.query(JiraConfiguration).filter(
        JiraConfiguration.project_id == project_id,
        JiraConfiguration.active.is_(True),
    ).first()

    if not config:
        return {"configured": False, "features": []}

    # Auto-generate feature JQL
    base_jql = config.jql.split("AND")[0].strip()
    feature_jql = f"{base_jql} AND issuetype in (Story, Task, Epic)"

    try:
        jira_data = await search_jira_features(
            jira_url=config.jira_url,
            jira_email=config.jira_email,
            jira_api_token=config.jira_api_token,
            jql=feature_jql,
        )
    except Exception as exc:
        raise HTTPException(502, f"Unable to fetch Jira features: {str(exc)}")

    features_raw = jira_data["issues"]
    total = len(features_raw)

    start = (page - 1) * per_page
    end = start + per_page

    features = []
    for issue in features_raw[start:end]:
        fields = issue.get("fields", {})
        features.append({
            "jira_id": issue.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName"),
            "story_points": fields.get("customfield_10008"),
            "epic": fields.get("parent", {}).get("key"),
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "labels": fields.get("labels") or [],
        })

    return {
        "configured": True,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total // per_page) + (1 if total % per_page else 0),
        "features": features,
    }
