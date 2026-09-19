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

            if environment_field:
                if environment_field not in fields:
                    fields.append(environment_field)

            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }

            if next_page_token:
                payload["nextPageToken"] = next_page_token

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
                    f"Jira API failed: "
                    f"{response.status_code} - "
                    f"{response.text}"
                )

            data = response.json()

            issues = data.get(
                "issues",
                [],
            )

            all_issues.extend(issues)

            next_page_token = data.get(
                "nextPageToken"
            )

            if not next_page_token:
                break

    return {
        "issues": all_issues,
        "total": len(all_issues),
    }


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

            if environment_field:
                if environment_field not in fields:
                    fields.append(environment_field)

            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }

            if next_page_token:
                payload["nextPageToken"] = next_page_token

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
                    f"Jira API failed: "
                    f"{response.status_code} - "
                    f"{response.text}"
                )

            data = response.json()

            features = data.get(
                "issues",
                [],
            )

            all_features.extend(features)

            next_page_token = data.get(
                "nextPageToken"
            )

            if not next_page_token:
                break

    return {
        "issues": all_features,
        "total": len(all_features),
    }


def _extract_environment_value(value):
    """Normalize common Jira environment-field response formats."""

    if isinstance(value, dict):
        return (
            value.get("value")
            or value.get("name")
            or value.get("displayName")
        )

    if isinstance(value, list):
        values = []

        for item in value:
            extracted = _extract_environment_value(item)

            if extracted:
                values.append(
                    str(extracted).strip()
                )

        return ", ".join(values)

    if value is None:
        return None

    return str(value).strip()


def _configured_labels(value):
    """Convert one or more comma-separated configured labels to a set."""

    if not value:
        return set()

    return {
        label.strip().lower()
        for label in str(value).split(",")
        if label.strip()
    }


def get_issue_environment(
    fields=None,
    environment_field=None,
    uat_label=None,
    prod_label=None,
):
    """
    Determine Jira issue environment.

    Production and UAT are determined independently using OR logic:

        PROD = configured PROD environment value OR PROD label
        UAT  = configured UAT environment value OR UAT label

    SIT does not have its own tag/value. Anything that is neither
    UAT nor PROD is treated as SIT by the caller/report.

    The environment field is optional. When it is not configured,
    classification falls back to labels.
    """

    fields = fields or {}

    # ------------------------------------------------------------
    # Read configured Jira environment field
    # ------------------------------------------------------------

    environment_value = None

    if environment_field:
        environment_value = _extract_environment_value(
            fields.get(environment_field)
        )

    normalized_environment = (
        str(environment_value).strip().upper()
        if environment_value
        else None
    )

    # ------------------------------------------------------------
    # Read Jira labels
    # ------------------------------------------------------------

    labels = fields.get("labels") or []

    normalized_labels = {
        str(label).strip().lower()
        for label in labels
        if str(label).strip()
    }

    uat_labels = _configured_labels(uat_label)
    prod_labels = _configured_labels(prod_label)

    # ------------------------------------------------------------
    # PROD must win when either PROD source matches.
    # This also handles an issue that has both UAT and PROD
    # indicators: a production indicator is sufficient for PROD.
    # ------------------------------------------------------------

    if (
        normalized_environment == "PROD"
        or bool(prod_labels & normalized_labels)
    ):
        return "PROD"

    # ------------------------------------------------------------
    # UAT when either UAT source matches.
    # ------------------------------------------------------------

    if (
        normalized_environment == "UAT"
        or bool(uat_labels & normalized_labels)
    ):
        return "UAT"

    return None
