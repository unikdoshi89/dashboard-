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

            payload = {
                "jql": jql,
                "maxResults": max_results,
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
    fields.append(environment_field),
            }

            # Add pagination token only after first request
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

            # Jira returns this when another page exists
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

            payload = {
                "jql": jql,
                "maxResults": max_results,
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
]

if environment_field:
    fields.append(environment_field),
            }

            # Add pagination token only after first request
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

            # Jira returns this when another page exists
            next_page_token = data.get(
                "nextPageToken"
            )

            if not next_page_token:
                break

    return {
        "issues": all_features,
        "total": len(all_features),
    }

def get_issue_environment(
    fields,
    environment_field=None,
    uat_label=None,
    prod_label=None,
):
    """
    Determine issue environment.

    Priority:
    1. Configured Jira environment field
    2. UAT label
    3. PROD label
    4. None
    """

    fields = fields or {}

    # ============================================================
    # 1. ENVIRONMENT FIELD
    # ============================================================

    if environment_field:

        environment = fields.get(
            environment_field
        )

        if isinstance(environment, dict):
            environment = (
                environment.get("value")
                or environment.get("name")
            )

        elif isinstance(environment, list):

            values = []

            for item in environment:

                if isinstance(item, dict):
                    value = (
                        item.get("value")
                        or item.get("name")
                    )
                else:
                    value = str(item)

                if value:
                    values.append(value)

            environment = ", ".join(values)

        if environment:

            environment = str(
                environment
            ).strip().upper()

            if environment == "UAT":
                return "UAT"

            if environment == "PROD":
                return "PROD"

    # ============================================================
    # 2. LABEL FALLBACK
    # ============================================================

    labels = fields.get("labels") or []

    if (
        uat_label
        and uat_label in labels
    ):
        return "UAT"

    if (
        prod_label
        and prod_label in labels
    ):
        return "PROD"

    return None
