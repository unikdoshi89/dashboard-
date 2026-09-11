from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    project_key: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    project_key: str
    description: str | None = None
    active: bool

    model_config = {
        "from_attributes": True
    }

class AutomationUploadBatchResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    row_count: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UploadedTestCaseResponse(BaseModel):

    id: int
    upload_batch_id: int
    project_id: int

    sheet_name: str | None = None

    sno: int | None = None
    comment: str | None = None
    owner: str | None = None
    jira_id: str | None = None
    test_case_id: str

    pre_condition: str | None = None
    test_case_description: str | None = None
    steps: str | None = None
    expected_result: str | None = None

    status: str | None = None
    automatable: str | None = None
    automated: str | None = None

    uploaded_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

# ============================================================
# Jira
# ============================================================

class JiraConfigurationCreate(BaseModel):
    jira_url: str
    jira_email: str
    jira_api_token: str
    jql: str
    feature_jql: str
    uat_label: str
    prod_label: str
    active: bool = True


class JiraConfigurationResponse(BaseModel):
    id: int
    project_id: int
    jira_url: str
    jira_email: str
    jql: str
    feature_jql: str
    uat_label: str
    prod_label: str
    active: bool

    model_config = ConfigDict(
        from_attributes=True
    )

class JiraBugResponse(BaseModel):
    jira_id: str
    summary: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    reporter: str | None = None
    created: str | None = None
    updated: str | None = None
    environment: str | None = None
    labels: list[str] = []
