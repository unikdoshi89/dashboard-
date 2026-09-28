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
    search_jira_bugs,
    search_jira_features,
    get_issue_environment,
)


router = APIRouter(
    prefix="/projects",
    tags=["Jira"],
)


# ============================================================
# Helpers
# ============================================================

def build_search_jql(
    base_jql: str,
    search: str | None,
):
    """
    Add Jira ID or keyword search to a configured JQL.
    """

    base_jql = (
        base_jql or ""
    ).strip()

    if not search:
        return base_jql

    search = search.strip()

    if not search:
        return base_jql

    escaped_search = (
        search
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    if re.match(
        r"^[A-Za-z][A-Za-z0-9_]*-\d+$",
        search,
    ):
        return (
            f"({base_jql}) "
            f'AND key = "{escaped_search}"'
        )

    return (
        f"({base_jql}) "
        f'text ~ "\\"{escaped_search}\\""'
    )


def normalize_jira_issue(
    issue,
    environment_field=None,
    uat_label=None,
    prod_label=None,
    forced_environment=None,
):
    fields = (
        issue.get("fields", {})
        or {}
    )

    status = fields.get(
        "status"
    ) or {}

    priority = fields.get(
        "priority"
    ) or {}

    assignee = fields.get(
        "assignee"
    ) or {}

    reporter = fields.get(
        "reporter"
    ) or {}

    labels = (
        fields.get("labels")
        or []
    )

    environment = get_issue_environment(
        fields=fields,
        environment_field=(
            environment_field
            or None
        ),
        uat_label=uat_label,
        prod_label=prod_label,
        forced_environment=(
            forced_environment
        ),
    )

    return {
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

        "environment": (
            environment
            or forced_environment
        ),

        "labels": labels,
    }


# ============================================================
# GET Jira Configuration
# ============================================================

@router.get(
    "/{project_id}/jira/config"
)
def get_jira_config(
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
            "jira_url": "",
            "jira_email": "",
            "jql": "",
            "feature_jql": "",
            "sit_jql": "",
            "uat_jql": "",
            "prod_jql": "",
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

        "feature_jql": (
            config.feature_jql
            or ""
        ),

        "sit_jql": (
            config.sit_jql
            or ""
        ),

        "uat_jql": (
            config.uat_jql
            or ""
        ),

        "prod_jql": (
            config.prod_jql
            or ""
        ),

        "environment_field": (
            getattr(
                config,
                "environment_field",
                None,
            )
            or ""
        ),

        "uat_label": (
            config.uat_label
            or ""
        ),

        "prod_label": (
            config.prod_label
            or ""
        ),

        "active": bool(
            config.active
        ),

        "has_api_token": bool(
            config.jira_api_token
        ),
    }


# ============================================================
# CREATE / UPDATE Jira Configuration
# ============================================================

@router.post(
    "/{project_id}/jira/config"
)
def create_or_update_jira_config(
    project_id: int,
    config_data: JiraConfigurationCreate,
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

    config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id
            == project_id
        )
        .first()
    )

    if config:

        config.jira_url = (
            config_data.jira_url.strip()
        )

        config.jira_email = (
            config_data.jira_email.strip()
        )

        if (
            config_data.jira_api_token
            and
            config_data.jira_api_token.strip()
        ):
            config.jira_api_token = (
                config_data.jira_api_token.strip()
            )

        config.jql = (
            config_data.jql.strip()
        )

        config.feature_jql = (
            config_data.feature_jql
            or ""
        ).strip()

        config.sit_jql = (
            config_data.sit_jql
            or ""
        ).strip()

        config.uat_jql = (
            config_data.uat_jql
            or ""
        ).strip()

        config.prod_jql = (
            config_data.prod_jql
            or ""
        ).strip()

        config.environment_field = (
            config_data.environment_field.strip()
            if config_data.environment_field
            else None
        )

        config.uat_label = (
            config_data.uat_label.strip()
        )

        config.prod_label = (
            config_data.prod_label.strip()
        )

        config.active = (
            config_data.active
        )

    else:

        if not (
            config_data.jira_api_token
            and
            config_data.jira_api_token.strip()
        ):
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
                config_data.feature_jql
                or ""
            ).strip(),

            sit_jql=(
                config_data.sit_jql
                or ""
            ).strip(),

            uat_jql=(
                config_data.uat_jql
                or ""
            ).strip(),

            prod_jql=(
                config_data.prod_jql
                or ""
            ).strip(),

            environment_field=(
                config_data.environment_field.strip()
                if config_data.environment_field
                else None
            ),

            uat_label=(
                config_data.uat_label.strip()
            ),

            prod_label=(
                config_data.prod_label.strip()
            ),

            active=(
                config_data.active
            ),
        )

        db.add(config)

    db.commit()
    db.refresh(config)

    return {
        "success": True,

        "message":
            "Jira configuration saved successfully",

        "project_id":
            project_id,

        "jira_url":
            config.jira_url,

        "jira_email":
            config.jira_email,

        "jql":
            config.jql,

        "feature_jql":
            config.feature_jql or "",

        "sit_jql":
            config.sit_jql or "",

        "uat_jql":
            config.uat_jql or "",

        "prod_jql":
            config.prod_jql or "",

        "environment_field":
            getattr(
                config,
                "environment_field",
                None,
            ) or "",

        "uat_label":
            config.uat_label,

        "prod_label":
            config.prod_label,

        "active":
            config.active,

        "has_api_token":
            bool(
                config.jira_api_token
            ),
    }


# ============================================================
# Test Jira Connection
# ============================================================

@router.post(
    "/{project_id}/jira/test-connection"
)
async def test_project_jira_connection(
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
        "display_name":
            result.get("display_name"),
    }


# ============================================================
# GET Jira Bugs
# ============================================================

@router.get(
    "/{project_id}/jira/bugs"
)
async def get_jira_bugs(
    project_id: int,
    search: str | None = Query(
        default=None
    ),
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
    # Project
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
    # Configuration
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
            "project_name": project.name,
            "total": 0,
            "uat_total": 0,
            "prod_total": 0,
            "sit_total": 0,
            "bugs": [],
            "sit_bugs": [],
            "uat_bugs": [],
            "prod_bugs": [],
        }

    # ========================================================
    # Validate Jira credentials
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
    # Environment configuration
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
    # JQLs
    #
    # New configuration:
    #
    # SIT -> sit_jql
    # UAT -> uat_jql
    # PROD -> prod_jql
    #
    # Existing jql remains the fallback.
    # ========================================================

    sit_jql = (
        config.sit_jql or ""
    ).strip()

    uat_jql = (
        config.uat_jql or ""
    ).strip()

    prod_jql = (
        config.prod_jql or ""
    ).strip()

    # --------------------------------------------------------
    # Backward compatibility
    #
    # If environment-specific JQLs are not configured,
    # use the existing JQL and classification logic.
    # --------------------------------------------------------

    use_environment_jql = bool(
        sit_jql
        or uat_jql
        or prod_jql
    )

    # ========================================================
    # SEARCH MODE 1
    #
    # Environment-specific JQL
    # ========================================================

    if use_environment_jql:

        environment_queries = []

        if sit_jql:
            environment_queries.append(
                (
                    "SIT",
                    sit_jql,
                )
            )

        if uat_jql:
            environment_queries.append(
                (
                    "UAT",
                    uat_jql,
                )
            )

        if prod_jql:
            environment_queries.append(
                (
                    "PROD",
                    prod_jql,
                )
            )

        all_bugs_by_key = {}

        sit_bugs = []
        uat_bugs = []
        prod_bugs = []

        for (
            forced_environment,
            environment_jql,
        ) in environment_queries:

            final_jql = build_search_jql(
                environment_jql,
                search,
            )

            try:

                jira_data = (
                    await search_jira_bugs(
                        jira_url=config.jira_url,
                        jira_email=config.jira_email,
                        jira_api_token=config.jira_api_token,
                        jql=final_jql,
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
                        "Unable to fetch Jira "
                        f"{forced_environment} bugs: "
                        f"{str(exc)}"
                    ),
                )

            for issue in jira_data.get(
                "issues",
                [],
            ):

                bug = normalize_jira_issue(
                    issue=issue,
                    environment_field=(
                        environment_field
                    ),
                    uat_label=uat_label,
                    prod_label=prod_label,
                    forced_environment=(
                        forced_environment
                    ),
                )

                jira_key = bug.get(
                    "jira_id"
                )

                if not jira_key:
                    continue

                all_bugs_by_key[
                    jira_key
                ] = bug

                if (
                    forced_environment
                    == "SIT"
                ):
                    sit_bugs.append(
                        bug
                    )

                elif (
                    forced_environment
                    == "UAT"
                ):
                    uat_bugs.append(
                        bug
                    )

                elif (
                    forced_environment
                    == "PROD"
                ):
                    prod_bugs.append(
                        bug
                    )

        bugs = list(
            all_bugs_by_key.values()
        )

        total = len(bugs)

        start = (
            page - 1
        ) * per_page

        end = (
            start + per_page
        )

        return {
            "configured": True,

            "project_id":
                project_id,

            "project_name":
                project.name,

            "jql":
                config.jql,

            "sit_jql":
                sit_jql,

            "uat_jql":
                uat_jql,

            "prod_jql":
                prod_jql,

            "environment_field":
                environment_field or None,

            "page":
                page,

            "per_page":
                per_page,

            "total":
                total,

            "sit_total":
                len(sit_bugs),

            "uat_total":
                len(uat_bugs),

            "prod_total":
                len(prod_bugs),

            "pages":
                (
                    total // per_page
                )
                + (
                    1
                    if total % per_page
                    else 0
                ),

            "bugs":
                bugs[start:end],

            "sit_bugs":
                sit_bugs[start:end],

            "uat_bugs":
                uat_bugs[start:end],

            "prod_bugs":
                prod_bugs[start:end],
        }

    # ========================================================
    # SEARCH MODE 2
    #
    # Existing backward-compatible behavior
    # ========================================================

    jql = build_search_jql(
        config.jql,
        search,
    )

    try:

        jira_data = (
            await search_jira_bugs(
                jira_url=config.jira_url,
                jira_email=config.jira_email,
                jira_api_token=config.jira_api_token,
                jql=jql,
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
                f"Unable to fetch Jira bugs: {str(exc)}"
            ),
        )

    bugs = []
    uat_bugs = []
    prod_bugs = []
    sit_bugs = []

    for issue in jira_data.get(
        "issues",
        [],
    ):

        bug = normalize_jira_issue(
            issue=issue,
            environment_field=(
                environment_field
            ),
            uat_label=uat_label,
            prod_label=prod_label,
        )

        environment = (
            bug.get("environment")
        )

        if not environment:
            environment = "SIT"
            bug["environment"] = "SIT"

        bugs.append(
            bug
        )

        if environment == "UAT":
            uat_bugs.append(
                bug
            )

        elif environment == "PROD":
            prod_bugs.append(
                bug
            )

        else:
            sit_bugs.append(
                bug
            )

    total = len(
        bugs
    )

    start = (
        page - 1
    ) * per_page

    end = (
        start + per_page
    )

    return {
        "configured": True,

        "project_id":
            project_id,

        "project_name":
            project.name,

        "jql":
            jql,

        "sit_jql":
            sit_jql,

        "uat_jql":
            uat_jql,

        "prod_jql":
            prod_jql,

        "environment_field":
            environment_field or None,

        "page":
            page,

        "per_page":
            per_page,

        "total":
            total,

        "sit_total":
            len(sit_bugs),

        "uat_total":
            len(uat_bugs),

        "prod_total":
            len(prod_bugs),

        "pages":
            (
                total // per_page
            )
            + (
                1
                if total % per_page
                else 0
            ),

        "bugs":
            bugs[start:end],

        "sit_bugs":
            sit_bugs[start:end],

        "uat_bugs":
            uat_bugs[start:end],

        "prod_bugs":
            prod_bugs[start:end],
    }


# ============================================================
# GET Jira Features
# ============================================================

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
            "project_id":
                project_id,
            "features": [],
        }

    feature_jql = (
        config.feature_jql
        or ""
    ).strip()

    if not feature_jql:

        base_jql = (
            config.jql
            or ""
        ).strip()

        if not base_jql:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Jira JQL is not configured."
                ),
            )

        feature_jql = (
            f"({base_jql}) "
            "AND issuetype in "
            "(Story, Task, Epic)"
        )

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

    features_raw = (
        jira_data.get(
            "issues",
            [],
        )
    )

    total = len(
        features_raw
    )

    start = (
        page - 1
    ) * per_page

    end = (
        start + per_page
    )

    features = []

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

        status = (
            fields.get(
                "status"
            )
            or {}
        )

        priority = (
            fields.get(
                "priority"
            )
            or {}
        )

        assignee = (
            fields.get(
                "assignee"
            )
            or {}
        )

        reporter = (
            fields.get(
                "reporter"
            )
            or {}
        )

        parent = (
            fields.get(
                "parent"
            )
            or {}
        )

        labels = (
            fields.get(
                "labels"
            )
            or []
        )

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
                "jira_id":
                    issue.get("key"),

                "summary":
                    fields.get(
                        "summary"
                    ),

                "status":
                    (
                        status.get("name")
                        if isinstance(
                            status,
                            dict,
                        )
                        else None
                    ),

                "priority":
                    (
                        priority.get("name")
                        if isinstance(
                            priority,
                            dict,
                        )
                        else None
                    ),

                "assignee":
                    (
                        assignee.get(
                            "displayName"
                        )
                        if isinstance(
                            assignee,
                            dict,
                        )
                        else None
                    ),

                "reporter":
                    (
                        reporter.get(
                            "displayName"
                        )
                        if isinstance(
                            reporter,
                            dict,
                        )
                        else None
                    ),

                "created":
                    fields.get(
                        "created"
                    ),

                "updated":
                    fields.get(
                        "updated"
                    ),

                "environment":
                    environment,

                "labels":
                    labels,

                "parent":
                    (
                        parent.get("key")
                        if isinstance(
                            parent,
                            dict,
                        )
                        else None
                    ),

                "story_points":
                    fields.get(
                        "customfield_10008"
                    ),
            }
        )

    return {
        "configured": True,

        "project_id":
            project_id,

        "project_name":
            project.name,

        "jql":
            feature_jql,

        "environment_field":
            environment_field or None,

        "page":
            page,

        "per_page":
            per_page,

        "total":
            total,

        "pages":
            (
                total // per_page
            )
            + (
                1
                if total % per_page
                else 0
            ),

        "features":
            features,
    }
