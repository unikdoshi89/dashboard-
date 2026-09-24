import httpx


# ============================================================
# Jira Connection
# ============================================================

async def test_jira_connection(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
):
    url = (
        f"{jira_url.rstrip('/')}"
        "/rest/api/3/myself"
    )

    headers = {
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(
        timeout=30,
        verify=False,
    ) as client:

        response = await client.get(
            url,
            auth=(
                jira_email,
                jira_api_token,
            ),
            headers=headers,
        )

    if response.status_code != 200:
        return {
            "success": False,
            "status_code": response.status_code,
            "message": response.text,
        }

    data = response.json()

    return {
        "success": True,
        "status_code": response.status_code,
        "display_name": data.get("displayName"),
        "email": data.get("emailAddress"),
        "account_id": data.get("accountId"),
    }


# ============================================================
# Jira Bugs
# ============================================================

async def search_jira_bugs(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
    jql: str,
    environment_field: str | None = None,
    max_results: int = 100,
):
    url = (
        f"{jira_url.rstrip('/')}"
        "/rest/api/3/search/jql"
    )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    all_issues = []
    next_page_token = None

    async with httpx.AsyncClient(
        timeout=60,
        verify=False,
    ) as client:

        while True:

            fields = [
                "summary",
                "status",
                "priority",
                "assignee",
                "reporter",
                "created",
                "updated",
                "labels",
            ]

            # ------------------------------------------------
            # Add configured environment field
            # ------------------------------------------------

            if environment_field:

                environment_field = (
                    str(environment_field)
                    .strip()
                )

                if (
                    environment_field
                    and environment_field not in fields
                ):
                    fields.append(
                        environment_field
                    )

            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }

            # ------------------------------------------------
            # Pagination
            # ------------------------------------------------

            if next_page_token:

                payload[
                    "nextPageToken"
                ] = next_page_token

            response = await client.post(
                url,
                auth=(
                    jira_email,
                    jira_api_token,
                ),
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:

                raise RuntimeError(
                    "Jira API failed: "
                    f"{response.status_code} - "
                    f"{response.text}"
                )

            data = response.json()

            issues = data.get(
                "issues",
                [],
            )

            all_issues.extend(
                issues
            )

            next_page_token = (
                data.get(
                    "nextPageToken"
                )
            )

            if not next_page_token:
                break

    return {
        "issues": all_issues,
        "total": len(all_issues),
    }


# ============================================================
# Jira Features
# ============================================================

async def search_jira_features(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
    jql: str,
    environment_field: str | None = None,
    max_results: int = 100,
):
    url = (
        f"{jira_url.rstrip('/')}"
        "/rest/api/3/search/jql"
    )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    all_features = []
    next_page_token = None

    async with httpx.AsyncClient(
        timeout=60,
        verify=False,
    ) as client:

        while True:

            fields = [
                "summary",
                "status",
                "priority",
                "assignee",
                "reporter",
                "created",
                "updated",
                "labels",
                "parent",
                "issuetype",
            ]

            # ------------------------------------------------
            # Add configured environment field
            # ------------------------------------------------

            if environment_field:

                environment_field = (
                    str(environment_field)
                    .strip()
                )

                if (
                    environment_field
                    and environment_field not in fields
                ):
                    fields.append(
                        environment_field
                    )

            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }

            # ------------------------------------------------
            # Pagination
            # ------------------------------------------------

            if next_page_token:

                payload[
                    "nextPageToken"
                ] = next_page_token

            response = await client.post(
                url,
                auth=(
                    jira_email,
                    jira_api_token,
                ),
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:

                raise RuntimeError(
                    "Jira API failed: "
                    f"{response.status_code} - "
                    f"{response.text}"
                )

            data = response.json()

            features = data.get(
                "issues",
                [],
            )

            all_features.extend(
                features
            )

            next_page_token = (
                data.get(
                    "nextPageToken"
                )
            )

            if not next_page_token:
                break

    return {
        "issues": all_features,
        "total": len(all_features),
    }


# ============================================================
# Environment Value Extraction
# ============================================================

def _extract_environment_value(
    value,
):
    """
    Extract environment value from Jira field.

    Supports:

        "UAT"

        {"value": "UAT"}

        {"name": "UAT"}

        {"displayName": "UAT"}

        [{"value": "UAT"}]

        [{"name": "UAT"}]

        ["UAT"]
    """

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(
        value,
        dict,
    ):

        return (
            value.get("value")
            or value.get("name")
            or value.get("displayName")
        )

    # --------------------------------------------------------
    # List
    # --------------------------------------------------------

    if isinstance(
        value,
        list,
    ):

        values = []

        for item in value:

            extracted = (
                _extract_environment_value(
                    item
                )
            )

            if extracted:

                values.append(
                    str(
                        extracted
                    ).strip()
                )

        if values:

            return ", ".join(
                values
            )

        return None

    # --------------------------------------------------------
    # None
    # --------------------------------------------------------

    if value is None:
        return None

    # --------------------------------------------------------
    # Plain value
    # --------------------------------------------------------

    return str(
        value
    ).strip()


# ============================================================
# Configured Labels
# ============================================================

def _configured_labels(
    value,
):
    """
    Convert comma-separated labels into
    normalized lowercase values.
    """

    if not value:
        return set()

    return {
        label.strip().lower()
        for label in str(
            value
        ).split(",")
        if label.strip()
    }


# ============================================================
# Environment Classification
# ============================================================

def get_issue_environment(
    fields=None,
    environment_field=None,
    uat_label=None,
    prod_label=None,
    uat_environment=None,
    prod_environment=None,
):
    """
    Determine Jira issue environment.

    Rules:

    PROD:
        Environment field == configured PROD environment
        OR
        PROD label matches

    UAT:
        Environment field == configured UAT environment
        OR
        UAT label matches

    SIT:
        Neither UAT nor PROD.

    The environment field is optional.

    If environment values are not configured,
    defaults are UAT and PROD.
    """

    fields = fields or {}

    # ========================================================
    # 1. ENVIRONMENT FIELD
    # ========================================================

    environment_value = None

    if environment_field:

        environment_field = (
            str(environment_field)
            .strip()
        )

        # ----------------------------------------------------
        # First try exactly what was configured.
        #
        # Example:
        #
        # environment_field = "Env_IOP"
        # ----------------------------------------------------

        environment_raw = fields.get(
            environment_field
        )

        # ----------------------------------------------------
        # If Jira returned the actual customfield ID instead,
        # allow it to be supplied through a field mapping.
        #
        # This does NOT hard-code any Jira field.
        # ----------------------------------------------------

        if environment_raw is None:

            for key, value in fields.items():

                if (
                    str(key).strip().lower()
                    == environment_field.lower()
                ):

                    environment_raw = value
                    break

        environment_value = (
            _extract_environment_value(
                environment_raw
            )
        )

    normalized_environment = (
        str(
            environment_value
        )
        .strip()
        .upper()
        if environment_value
        else None
    )

    # ========================================================
    # 2. ENVIRONMENT CONFIGURATION
    # ========================================================

    configured_uat_environment = (
        str(
            uat_environment
        )
        .strip()
        .upper()
        if uat_environment
        else "UAT"
    )

    configured_prod_environment = (
        str(
            prod_environment
        )
        .strip()
        .upper()
        if prod_environment
        else "PROD"
    )

    # ========================================================
    # 3. LABELS
    # ========================================================

    labels = (
        fields.get(
            "labels"
        )
        or []
    )

    normalized_labels = {
        str(label)
        .strip()
        .lower()
        for label in labels
        if str(label).strip()
    }

    uat_labels = _configured_labels(
        uat_label
    )

    prod_labels = _configured_labels(
        prod_label
    )

    # ========================================================
    # 4. PROD
    # ========================================================

    if (
        normalized_environment
        == configured_prod_environment
    ):
        return "PROD"

    if (
        prod_labels
        & normalized_labels
    ):
        return "PROD"

    # ========================================================
    # 5. UAT
    # ========================================================

    if (
        normalized_environment
        == configured_uat_environment
    ):
        return "UAT"

    if (
        uat_labels
        & normalized_labels
    ):
        return "UAT"

    # ========================================================
    # 6. SIT
    # ========================================================

    return None
