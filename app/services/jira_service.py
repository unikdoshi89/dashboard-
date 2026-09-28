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
# Common Jira Search
# ============================================================

async def _search_jira(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
    jql: str,
    fields: list[str],
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

            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }

            if next_page_token:
                payload["nextPageToken"] = (
                    next_page_token
                )

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
# Search Bugs
# ============================================================

async def search_jira_bugs(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
    jql: str,
    environment_field: str | None = None,
    max_results: int = 100,
):
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
            fields.append(
                environment_field
            )

    return await _search_jira(
        jira_url=jira_url,
        jira_email=jira_email,
        jira_api_token=jira_api_token,
        jql=jql,
        fields=fields,
        max_results=max_results,
    )


# ============================================================
# Search Features
# ============================================================

async def search_jira_features(
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
    jql: str,
    environment_field: str | None = None,
    max_results: int = 100,
):
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
            fields.append(
                environment_field
            )

    return await _search_jira(
        jira_url=jira_url,
        jira_email=jira_email,
        jira_api_token=jira_api_token,
        jql=jql,
        fields=fields,
        max_results=max_results,
    )


# ============================================================
# Environment Helpers
# ============================================================

def _extract_environment_values(value):
    """
    Normalize Jira environment/custom-field responses.

    Supports:

        "PROD"

        {"value": "PROD"}

        {"name": "PROD"}

        [{"value": "PROD"}]

        ["PROD"]
    """

    values = []

    if value is None:
        return values

    if isinstance(value, dict):

        extracted = (
            value.get("value")
            or value.get("name")
            or value.get("displayName")
        )

        if extracted:
            values.append(
                str(extracted).strip().upper()
            )

        return values

    if isinstance(value, list):

        for item in value:

            values.extend(
                _extract_environment_values(
                    item
                )
            )

        return values

    text = str(value).strip()

    if text:
        values.append(
            text.upper()
        )

    return values


def _configured_labels(value):
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
    forced_environment=None,
):
    """
    Determine issue environment.

    Priority:

    1. forced_environment
       Used when the issue was returned by an
       environment-specific JQL.

    2. Configured Jira environment field

    3. PROD label

    4. UAT label

    5. None
    """

    fields = fields or {}

    # ============================================================
    # 1. Forced environment
    # ============================================================

    if forced_environment:

        normalized = (
            str(forced_environment)
            .strip()
            .upper()
        )

        if normalized in {
            "SIT",
            "UAT",
            "PROD",
        }:
            return normalized

    # ============================================================
    # 2. Environment field
    # ============================================================

    if environment_field:

        environment_values = (
            _extract_environment_values(
                fields.get(
                    environment_field
                )
            )
        )

        if "PROD" in environment_values:
            return "PROD"

        if "UAT" in environment_values:
            return "UAT"

        if "SIT" in environment_values:
            return "SIT"

    # ============================================================
    # 3. Labels
    # ============================================================

    labels = fields.get(
        "labels"
    ) or []

    normalized_labels = {
        str(label).strip().lower()
        for label in labels
        if str(label).strip()
    }

    prod_labels = _configured_labels(
        prod_label
    )

    uat_labels = _configured_labels(
        uat_label
    )

    if prod_labels.intersection(
        normalized_labels
    ):
        return "PROD"

    if uat_labels.intersection(
        normalized_labels
    ):
        return "UAT"

    return None
