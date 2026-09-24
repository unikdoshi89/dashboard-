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
            JiraConfiguration.project_id == project_id,
            JiraConfiguration.active.is_(True),
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
            "feature_jql": "",
            "environment_field": "",
            "uat_label": "",
            "prod_label": "",
            "active": False,
            "has_api_token": False,
        }

    return {
        "configured": True,
        "project_id": project_id,
        "jira_url": config.jira_url,
        "jira_email": config.jira_email,
        "jql": config.jql,
        "feature_jql": config.feature_jql or "",
        "environment_field": getattr(config, "environment_field", None) or "",
        "uat_label": config.uat_label or "",
        "prod_label": config.prod_label or "",
        "active": bool(config.active),
        "has_api_token": bool(config.jira_api_token),
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

        config.feature_jql = (
            config_data.feature_jql.strip()
        )

        config.environment_field = (
            config_data.environment_field.strip()
            if config_data.environment_field
            else None
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

            feature_jql=(
                config_data.feature_jql.strip()
            ),

            environment_field=(
                config_data.environment_field.strip()
                if config_data.environment_field
                else None
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
        "feature_jql": config.feature_jql,
        "environment_field": (
            getattr(config, "environment_field", None) or ""
        ),

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

    Environment detection priority:
    1. Project-specific Jira environment field
    2. Project-specific UAT label
    3. Project-specific PROD label

    The environment field is project-specific, for example:

        Project A -> ENV_IOP
        Project B -> ENVIRONMENT
        Project C -> customfield_12345
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
    # 4. Environment configuration
    #
    # Environment field is optional because labels are still
    # supported as fallback.
    # ========================================================

    environment_field = (
        getattr(
            config,
            "environment_field",
            None,
        )
        or ""
    ).strip()

    uat_label = (
        config.uat_label.strip()
        if config.uat_label
        else None
    )

    prod_label = (
        config.prod_label.strip()
        if config.prod_label
        else None
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
            environment_field=environment_field or None,
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

    for issue in jira_data.get(
        "issues",
        [],
    ):

        fields = issue.get(
            "fields",
            {},
        ) or {}

        labels = (
            fields.get("labels")
            or []
        )

        # ----------------------------------------------------
        # Determine environment
        #
        # Priority:
        # ENV field -> UAT label -> PROD label
        # ----------------------------------------------------

        environment = get_issue_environment(
            fields=fields,
            environment_field=(
              jira_config.environment_field
              if jira_config.environment_field
              else None
             ),
            uat_label=jira_config.uat_label,
            prod_label=jira_config.prod_label,
            uat_environment=jira_config.uat_environment,
            prod_environment=jira_config.prod_environment,
        )

        # ----------------------------------------------------
        # Jira objects
        # ----------------------------------------------------

        assignee = fields.get(
            "assignee"
        )

        reporter = fields.get(
            "reporter"
        )

        status = fields.get(
            "status"
        )

        priority = fields.get(
            "priority"
        )

        # ----------------------------------------------------
        # Create normalized bug object
        # ----------------------------------------------------

        bug = {
            "jira_id": issue.get(
                "key"
            ),

            "summary": fields.get(
                "summary"
            ),

            "status": (
                status.get("name")
                if isinstance(
                    status,
                    dict,
                )
                else None
            ),

            "priority": (
                priority.get("name")
                if isinstance(
                    priority,
                    dict,
                )
                else None
            ),

            "assignee": (
                assignee.get(
                    "displayName"
                )
                if isinstance(
                    assignee,
                    dict,
                )
                else None
            ),

            "reporter": (
                reporter.get(
                    "displayName"
                )
                if isinstance(
                    reporter,
                    dict,
                )
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

            uat_bugs.append(
                bug
            )

        elif environment == "PROD":

            prod_bugs.append(
                bug
            )

    # ========================================================
    # 9. Pagination
    # ========================================================

    total = len(bugs)

    start = (
        page - 1
    ) * per_page

    end = (
        start + per_page
    )

    paged_bugs = bugs[
        start:end
    ]

    # IMPORTANT:
    # These lists are independently filtered by environment.
    # We retain the existing behavior of your application.
    paged_uat = uat_bugs[
        start:end
    ]

    paged_prod = prod_bugs[
        start:end
    ]

    # ========================================================
    # 10. Response
    # ========================================================

    return {
        "configured": True,

        "project_id": project_id,

        "project_name": project.name,

        "jql": jql,

        "environment_field": (
            environment_field
            or None
        ),

        "page": page,

        "per_page": per_page,

        "total": total,

        "uat_total": len(
            uat_bugs
        ),

        "prod_total": len(
            prod_bugs
        ),

        "pages": (
            total // per_page
        )
        + (
            1
            if total % per_page
            else 0
        ),

        "bugs": paged_bugs,

        "uat_bugs": paged_uat,

        "prod_bugs": paged_prod,
    }

def get_issue_environment(
    fields,
    environment_field=None,
    uat_label=None,
    prod_label=None,
):
    """
    Determine Jira issue environment.

    PROD matches when either the configured Jira environment value
    matches PROD or a configured production label matches.

    UAT matches when either the configured Jira environment value
    matches UAT or a configured UAT label matches.

    SIT has no explicit tag/value. Any issue that is not classified
    as UAT or PROD is treated as SIT by the caller.
    """

    fields = fields or {}

    environment_values = set()

    if environment_field:
        environment = fields.get(environment_field)

        if isinstance(environment, dict):
            value = (
                environment.get("value")
                or environment.get("name")
            )
            if value:
                environment_values.add(
                    str(value).strip().upper()
                )

        elif isinstance(environment, list):
            for item in environment:
                if isinstance(item, dict):
                    value = (
                        item.get("value")
                        or item.get("name")
                    )
                else:
                    value = item

                if value:
                    environment_values.add(
                        str(value).strip().upper()
                    )

        elif environment is not None:
            environment_values.add(
                str(environment).strip().upper()
            )

    labels = fields.get("labels") or []
    normalized_labels = {
        str(label).strip().lower()
        for label in labels
        if str(label).strip()
    }

    uat_labels = {
        label.strip().lower()
        for label in str(uat_label or "").split(",")
        if label.strip()
    }

    prod_labels = {
        label.strip().lower()
        for label in str(prod_label or "").split(",")
        if label.strip()
    }

    # Production has precedence when either production source matches.
    if "PROD" in environment_values:
        return "PROD"

    if prod_labels.intersection(normalized_labels):
        return "PROD"

    # UAT is checked after PROD so a production match always wins.
    if "UAT" in environment_values:
        return "UAT"

    if uat_labels.intersection(normalized_labels):
        return "UAT"

    return None

@router.get(
    "/{project_id}/jira/features"
)
async def get_jira_features(
    project_id: int,
    page: int = Query(
        default=1,
        ge=1,
    ),
    per_page: int = Query(
        default=20,
        ge=5,
        le=200,
    ),
    db: Session = Depends(get_db),
):

    # ========================================================
    # 1. Validate project
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
    # 2. Get Jira configuration
    # ========================================================

    config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id
            == project_id,

            JiraConfiguration.active.is_(True),
        )
        .first()
    )

    if not config:
        return {
            "configured": False,
            "project_id": project_id,
            "features": [],
        }

    # ========================================================
    # 3. Environment configuration
    # ========================================================

    environment_field = (
        getattr(
            config,
            "environment_field",
            None,
        )
        or ""
    ).strip()

    uat_label = (
        config.uat_label.strip()
        if config.uat_label
        else None
    )

    prod_label = (
        config.prod_label.strip()
        if config.prod_label
        else None
    )

    # ========================================================
    # 4. Build Feature JQL
    # ========================================================

    feature_jql = (
        config.feature_jql
        or ""
    ).strip()

    # --------------------------------------------------------
    # If feature_jql is not configured, generate it from
    # the project's base JQL.
    # --------------------------------------------------------

    if not feature_jql:

        base_jql = (
            config.jql
            or ""
        ).strip()

        if not base_jql:
            raise HTTPException(
                status_code=500,
                detail="Jira JQL is not configured.",
            )

        # Remove existing issue type condition if required
        # by your existing configuration.
        feature_jql = (
            f"({base_jql}) "
            "AND issuetype in (Story, Task, Epic)"
        )

    # ========================================================
    # 5. Fetch Jira features
    # ========================================================

    try:

        jira_data = (
            await search_jira_features(
                jira_url=config.jira_url,
                jira_email=config.jira_email,
                jira_api_token=config.jira_api_token,
                jql=feature_jql,
                environment_field=(
                    environment_field
                    or None
                ),
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to fetch Jira features: "
                f"{str(exc)}"
            ),
        )

    # ========================================================
    # 6. Raw features
    # ========================================================

    features_raw = (
        jira_data.get(
            "issues",
            [],
        )
    )

    total = len(
        features_raw
    )

    # ========================================================
    # 7. Pagination
    # ========================================================

    start = (
        page - 1
    ) * per_page

    end = (
        start + per_page
    )

    features = []

    # ========================================================
    # 8. Normalize Jira features
    # ========================================================

    for issue in features_raw[
        start:end
    ]:

        fields = (
            issue.get(
                "fields",
                {},
            )
            or {}
        )

        status = fields.get(
            "status"
        )

        priority = fields.get(
            "priority"
        )

        assignee = fields.get(
            "assignee"
        )

        parent = fields.get(
            "parent"
        )

        labels = (
            fields.get(
                "labels"
            )
            or []
        )

        # ----------------------------------------------------
        # Determine environment
        # ----------------------------------------------------

        environment = (
            get_issue_environment(
                fields=fields,
                environment_field=(
                    environment_field
                    or None
                ),
                uat_label=uat_label,
                prod_label=prod_label,
            )
        )

        features.append(
            {
                "jira_id": issue.get(
                    "key"
                ),

                "summary": fields.get(
                    "summary"
                ),

                "status": (
                    status.get("name")
                    if isinstance(
                        status,
                        dict,
                    )
                    else None
                ),

                "priority": (
                    priority.get("name")
                    if isinstance(
                        priority,
                        dict,
                    )
                    else None
                ),

                "assignee": (
                    assignee.get(
                        "displayName"
                    )
                    if isinstance(
                        assignee,
                        dict,
                    )
                    else None
                ),

                "story_points": fields.get(
                    "customfield_10008"
                ),

                "epic": (
                    parent.get("key")
                    if isinstance(
                        parent,
                        dict,
                    )
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
        )

    # ========================================================
    # 9. Response
    # ========================================================

    return {
        "configured": True,

        "project_id": project_id,

        "page": page,

        "per_page": per_page,

        "total": total,

        "pages": (
            total // per_page
        )
        + (
            1
            if total % per_page
            else 0
        ),

        "jql": feature_jql,

        "environment_field": (
            environment_field
            or None
        ),

        "features": features,
    }
