from typing import Optional

from pydantic import BaseModel, ConfigDict


class AutomationReleaseCreate(BaseModel):

    release_name: str


class AutomationReleaseResponse(BaseModel):

    id: int
    project_id: int
    release_name: str
    release_order: int

    model_config = ConfigDict(
        from_attributes=True
    )


class AutomationDetailCreate(BaseModel):

    pod: str

    requirements_rtb: int = 0

    test_cases: int = 0

    automatable: int = 0

    automated: int = 0


class AutomationDetailUpdate(BaseModel):

    pod: Optional[str] = None

    requirements_rtb: Optional[int] = None

    test_cases: Optional[int] = None

    automatable: Optional[int] = None

    automated: Optional[int] = None


class AutomationDetailResponse(BaseModel):

    id: int
    release_id: int
    pod: str
    requirements_rtb: int
    test_cases: int
    automatable: int
    automated: int

    model_config = ConfigDict(
        from_attributes=True
    )
