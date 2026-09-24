import httpx


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
# Jira Field Resolution
# ============================================================

async def resolve_jira_field_id(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
    field_name_or_id: str,
):
    """
    Resolve a Jira field name to its actual Jira field ID.

    Example:

        Env_IOP
            ->
        customfield_12345

    If the supplied value is already a Jira field ID,
    it is returned unchanged.

    This allows the Jira configuration UI to store either:

        Env_IOP

    or:

        customfield_12345
    """

    if not field_name_or_id:
        return None

    field_name_or_id = str(
        field_name_or_id
    ).strip()

    if not field_name_or_id:
        return None

    # --------------------------------------------------------
    # Already a Jira custom field ID
    # --------------------------------------------------------

    if field_name_or_id.startswith(
        "customfield_"
    ):
        return field_name_or_id

    url = (
        f"{jira_url.rstrip('/')}"
        "/rest/api/3/field"
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
        raise RuntimeError(
            "Unable to retrieve Jira fields: "
            f"{response.status_code} - "
            f"{response.text}"
        )

    jira_fields = response.json()

    requested_name = (
        field_name_or_id
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # Exact field-name match
    # --------------------------------------------------------

    for field in jira_fields:

        field_id = field.get("id")
        field_name = field.get("name")

        if not field_id or not field_name:
            continue

        if (
            str(field_name)
            .strip()
            .lower()
            == requested_name
        ):
            return field_id

    raise RuntimeError(
        f"Jira field '{field_name_or_id}' "
        "was not found."
    )


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

    # --------------------------------------------------------
    # Resolve configured environment field
    #
    # Example:
    #
    # Env_IOP
    #     ->
    # customfield_12345
    # --------------------------------------------------------

    resolved_environment_field = None

    if environment_field:

        resolved_environment_field = (
            await resolve_jira_field_id(
                jira_url=jira_url,
                jira_email=jira_email,
                jira_api_token=jira_api_token,
                field_name_or_id=environment_field,
            )
        )

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
            # Add resolved Jira environment field
            # ------------------------------------------------

            if resolved_environment_field:

                if (
                    resolved_environment_field
                    not in fields
                ):
                    fields.append(
                        resolved_environment_field
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
        "environment_field": (
            resolved_environment_field
        ),
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

    # --------------------------------------------------------
    # Resolve configured environment field
    # --------------------------------------------------------

    resolved_environment_field = None

    if environment_field:

        resolved_environment_field = (
            await resolve_jira_field_id(
                jira_url=jira_url,
                jira_email=jira_email,
                jira_api_token=jira_api_token,
                field_name_or_id=environment_field,
            )
        )

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
            # Add resolved environment field
            # ------------------------------------------------

            if resolved_environment_field:

                if (
                    resolved_environment_field
                    not in fields
                ):
                    fields.append(
                        resolved_environment_field
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
        "environment_field": (
            resolved_environment_field
        ),
    }


# ============================================================
# Environment Value Extraction
# ============================================================

def _extract_environment_value(
    value,
):
    """
    Normalize common Jira custom-field response formats.

    Supported formats:

        "UAT"

        {
            "value": "UAT"
        }

        {
            "name": "UAT"
        }

        {
            "displayName": "UAT"
        }

        [
            {
                "value": "UAT"
            }
        ]

        [
            "UAT"
        ]
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
    # Empty
    # --------------------------------------------------------

    if value is None:
        return None

    # --------------------------------------------------------
    # Plain string / number
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
    Convert one or more comma-separated
    configured labels into a lowercase set.

    Example:

        "prod, production, PROD"

    becomes:

        {
            "prod",
            "production"
        }
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

    Classification rules:

        PROD =
            configured PROD environment value
            OR
            configured PROD label

        UAT =
            configured UAT environment value
            OR
            configured UAT label

        SIT =
            anything that is neither UAT nor PROD

    SIT does not require a Jira field or label.

    The environment field is optional.

    The configured environment values are also optional.

    Defaults:

        UAT environment -> UAT
        PROD environment -> PROD

    This keeps compatibility with existing projects.
    """

    fields = fields or {}

    # ========================================================
    # 1. ENVIRONMENT FIELD
    # ========================================================

    environment_value = None

    if environment_field:

        environment_value = (
            fields.get(
                environment_field
            )
        )

        environment_value = (
            _extract_environment_value(
                environment_value
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
    # 2. CONFIGURED ENVIRONMENT VALUES
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
    #
    # PROD wins if either the environment field OR
    # a configured PROD label matches.
    # ========================================================

    if (
        normalized_environment
        == configured_prod_environment
        or bool(
            prod_labels
            & normalized_labels
        )
    ):
        return "PROD"

    # ========================================================
    # 5. UAT
    #
    # UAT is returned if either the environment field OR
    # a configured UAT label matches.
    # ========================================================

    if (
        normalized_environment
        == configured_uat_environment
        or bool(
            uat_labels
            & normalized_labels
        )
    ):
        return "UAT"

    # ========================================================
    # 6. SIT / UNKNOWN
    #
    # Caller treats anything not UAT/PROD as SIT.
    # ========================================================

    return None
