from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

import pandas as pd

from fastapi import File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from io import BytesIO

from app.core.database import get_db

from app.models.project import Project
from app.models.metric_value import MetricValue

from app.schemas.metric import AddMetricRequest
from app.models.metric_category import MetricCategory
from app.models.project_metric import ProjectMetric
from app.models.metric_definition import MetricDefinition
from app.models.jira_configuration import JiraConfiguration
from app.services.jira_service import (
    search_jira_bugs,
    search_jira_features,
    get_issue_environment,
)

from app.utils.status_calculator import calculate_status

from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    AutomationUploadBatchResponse, UploadedTestCaseResponse,
)

from app.models.automation_detail import (
AutomationUploadBatch,
UploadedTestCase,
)

from fastapi.responses import (
    StreamingResponse,
    HTMLResponse,
)
from app.services.project_report import (
    generate_project_report_pdf,
    generate_project_report_html,
)

from app.services.quality_score import (
    calculate_quality_confidence_score,
)



router = APIRouter()


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def get_projects(
    db: Session = Depends(get_db),
):
    return (
        db.query(Project)
        .filter(Project.active.is_(True))
        .order_by(Project.name)
        .all()
    )



@router.post("/projects/{project_id}/metrics")
def add_metric_to_project(
    project_id: int,
    request: AddMetricRequest,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # 1. Check project
    # --------------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # --------------------------------------------------
    # 2. Check metric definition
    # --------------------------------------------------

    definition = (
        db.query(MetricDefinition)
        .filter(
            MetricDefinition.id
            == request.metric_definition_id
        )
        .first()
    )

    if not definition:
        raise HTTPException(
            status_code=404,
            detail="Metric definition not found",
        )

    # --------------------------------------------------
    # 3. Check if metric already exists
    # --------------------------------------------------

    project_metric = (
        db.query(ProjectMetric)
        .filter(
            ProjectMetric.project_id == project_id,
            ProjectMetric.metric_definition_id
            == request.metric_definition_id,
        )
        .first()
    )

    if project_metric:

        if project_metric.enabled:
            raise HTTPException(
                status_code=409,
                detail="Metric already exists for this project",
            )

        # ----------------------------------------------
        # Previously deleted metric
        # ----------------------------------------------

        project_metric.enabled = True

        db.commit()
        db.refresh(project_metric)

    else:

        project_metric = ProjectMetric(
            project_id=project_id,
            metric_definition_id=definition.id,
            enabled=True,
        )

        db.add(project_metric)
        db.flush()

    # --------------------------------------------------
    # 4. Calculate status
    # --------------------------------------------------

    status = calculate_status(
        request.value,
        definition.default_target,
        definition.warning_threshold,
        definition.critical_threshold,
        definition.direction,
    )

    # --------------------------------------------------
    # 5. Create metric value
    # --------------------------------------------------

    metric_value = (
        db.query(MetricValue)
        .filter(
            MetricValue.project_metric_id
            == project_metric.id
        )
        .first()
    )

    if metric_value:

        metric_value.value = request.value
        metric_value.status = status
        metric_value.notes = request.notes
        metric_value.updated_by = request.added_by

    else:

        metric_value = MetricValue(
            project_metric_id=project_metric.id,
            value=request.value,
            status=status,
            notes=request.notes,
            updated_by=request.added_by,
        )

        db.add(metric_value)

    db.commit()

    db.refresh(project_metric)
    db.refresh(metric_value)

    return {
        "project_metric_id": project_metric.id,
        "metric_definition_id": definition.id,
        "metric_key": definition.metric_key,
        "metric": definition.name,
        "value": float(metric_value.value),
        "unit": definition.unit,
        "status": metric_value.status,
        "message": "Metric added successfully",
    }

@router.get("/{project_id}/available-metrics")
def get_available_metrics(
    project_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # 1. Check project
    # --------------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # --------------------------------------------------
    # 2. Get metric definitions not enabled
    # --------------------------------------------------

    metrics = (
        db.query(
            MetricDefinition,
            MetricCategory,
        )
        .join(
            MetricCategory,
            MetricDefinition.category_id
            == MetricCategory.id,
        )
        .outerjoin(
            ProjectMetric,
            (
                ProjectMetric.metric_definition_id
                == MetricDefinition.id
            )
            &
            (
                ProjectMetric.project_id
                == project_id
            )
            &
            (
                ProjectMetric.enabled.is_(True)
            ),
        )
        .filter(
            ProjectMetric.id.is_(None)
        )
        .order_by(
            MetricCategory.display_order,
            MetricDefinition.display_order,
        )
        .all()
    )

    return [
        {
            "metric_definition_id": definition.id,
            "metric_key": definition.metric_key,
            "name": definition.name,
            "description": definition.description,
            "unit": definition.unit,
            "target": float(
                definition.default_target
            ),
            "warning": float(
                definition.warning_threshold
            ),
            "critical": float(
                definition.critical_threshold
            ),
            "direction": definition.direction,
            "category_id": category.id,
            "category_name": category.name,
        }
        for definition, category in metrics
    ]

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    # Check duplicate project key
    existing_project = (
        db.query(Project)
        .filter(
            Project.project_key
            == project_data.project_key
        )
        .first()
    )

    if existing_project:
        raise HTTPException(
            status_code=409,
            detail="Project key already exists",
        )

    project = Project(
        name=project_data.name,
        project_key=project_data.project_key,
        description=project_data.description,
        active=True,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project

@router.get(
    "/projects/{project_id}/quality-score"
)
def get_quality_score(
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

    return calculate_quality_confidence_score(
        db,
        project_id,
    )


@router.get(
    "/projects/{project_id}/report/pdf"
)
async def download_project_report(
    project_id: int,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # ================================================================
    # Jira Bug Summary
    # ================================================================

    jira_total = 0
    jira_uat = 0
    jira_prod = 0
    jira_sit = 0

    jira_config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id == project_id,
            JiraConfiguration.active.is_(True),
        )
        .first()
    )

    if jira_config:
        try:

            jira_data = await search_jira_bugs(
                jira_url=jira_config.jira_url,
                jira_email=jira_config.jira_email,
                jira_api_token=jira_config.jira_api_token,
                jql=jira_config.jql,
                environment_field=(
                    jira_config.environment_field
                    if jira_config.environment_field
                    else None
                ),
            )

            issues = jira_data.get(
                "issues",
                [],
            )

            jira_total = len(issues)

            for issue in issues:

                fields = issue.get(
                    "fields",
                    {},
                )

                environment = get_issue_environment(
                    fields=fields,
                    environment_field=(
                        jira_config.environment_field
                        if jira_config.environment_field
                        else None
                    ),
                    uat_label=jira_config.uat_label,
                    prod_label=jira_config.prod_label,
                )

                if environment == "UAT":
                    jira_uat += 1

                elif environment == "PROD":
                    jira_prod += 1

            # SIT = Total - UAT - PROD
            jira_sit = max(
                jira_total
                - jira_uat
                - jira_prod,
                0,
            )

        except Exception as exc:

            print(
                "Jira bug fetch failed:",
                exc,
            )

            # Do not fail PDF generation
            # if Jira is unavailable.
            jira_total = 0
            jira_uat = 0
            jira_prod = 0
            jira_sit = 0

    # ================================================================
    # Generate PDF
    # ================================================================

    try:

        pdf_buffer = generate_project_report_pdf(
            db,
            project_id,
            jira_total=jira_total,
            jira_uat=jira_uat,
            jira_prod=jira_prod,
            jira_sit=jira_sit,
        )


    except Exception as exc:

        import traceback

        print("========================================")

        print("PDF GENERATION FAILED")

        print("========================================")

        print(str(exc))

        traceback.print_exc()

        print("========================================")

        raise HTTPException(

            status_code=500,

            detail=f"Failed to generate project PDF: {str(exc)}",

        )

    filename = (
        f"QE_Governance_"
        f"{project.name.replace(' ', '_')}.pdf"
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )

@router.get(
    "/projects/{project_id}/report/html",
    response_class=HTMLResponse,
)
async def project_html_report(
    project_id: int,
    db: Session = Depends(get_db),
):
    # ==========================================================
    # Validate Project
    # ==========================================================

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # ==========================================================
    # Jira defaults
    # ==========================================================

    jira_total = 0
    jira_uat = 0
    jira_prod = 0
    jira_sit = 0

    jira_issues = []
    jira_features = []
    jira_sit_issues = []
    jira_uat_issues = []
    jira_prod_issues = []
    jira_issue_environments = {}

    # ==========================================================
    # Jira configuration
    # ==========================================================

    jira_config = (
        db.query(JiraConfiguration)
        .filter(
            JiraConfiguration.project_id == project_id,
            JiraConfiguration.active.is_(True),
        )
        .first()
    )

    # ==========================================================
    # Jira Bugs
    # ==========================================================

    if jira_config:

        try:

            jira_data = await search_jira_bugs(
                jira_url=jira_config.jira_url,
                jira_email=jira_config.jira_email,
                jira_api_token=jira_config.jira_api_token,
                jql=jira_config.jql,
                environment_field=(
                    jira_config.environment_field
                    if jira_config.environment_field
                    else None
                ),
            )

            jira_issues = (
                jira_data.get(
                    "issues",
                    [],
                )
                if jira_data
                else []
            )

            jira_total = len(
                jira_issues
            )

            # --------------------------------------------------
            # Determine environment
            # --------------------------------------------------

            for issue in jira_issues:

                fields = (
                    issue.get(
                        "fields",
                        {},
                    )
                    or {}
                )

                environment = get_issue_environment(
                    fields=fields,
                    environment_field=(
                        jira_config.environment_field
                        if jira_config.environment_field
                        else None
                    ),
                    uat_label=jira_config.uat_label,
                    prod_label=jira_config.prod_label,
                )

                issue_key = issue.get("key")

                jira_issue_environments[issue_key] = environment or "SIT"

                if environment == "UAT":

                    jira_uat += 1
                    jira_uat_issues.append(issue)

                elif environment == "PROD":

                    jira_prod += 1
                    jira_prod_issues.append(issue)

                else:

                    jira_sit_issues.append(issue)

            # --------------------------------------------------
            # Remaining bugs
            #
            # Anything that is neither UAT nor PROD
            # is displayed as SIT.
            # --------------------------------------------------

            jira_sit = max(
                jira_total
                - jira_uat
                - jira_prod,
                0,
            )

            print(
                "HTML REPORT JIRA SUMMARY:",
                {
                    "project_id": project_id,
                    "total": jira_total,
                    "uat": jira_uat,
                    "prod": jira_prod,
                    "sit": jira_sit,
                    "environment_field": (
                        jira_config.environment_field
                        if jira_config.environment_field
                        else None
                    ),
                },
            )

        except Exception as exc:

            import traceback

            print(
                "========================================"
            )

            print(
                "HTML REPORT JIRA BUG FETCH FAILED"
            )

            print(
                "========================================"
            )

            print(
                str(exc)
            )

            traceback.print_exc()

            print(
                "========================================"
            )

            # Do not fail the complete report.
            #
            # Keep the report generation alive, but make
            # the Jira failure visible in backend logs.

            jira_total = 0
            jira_uat = 0
            jira_prod = 0
            jira_sit = 0
            jira_issues = []
            jira_sit_issues = []
            jira_uat_issues = []
            jira_prod_issues = []
            jira_issue_environments = {}

    # ==========================================================
    # Jira Features / Stories
    # ==========================================================

    if jira_config:

        feature_jql = (
            jira_config.feature_jql
            or ""
        ).strip()

        if feature_jql:

            try:

                feature_data = (
                    await search_jira_features(
                        jira_url=(
                            jira_config.jira_url
                        ),
                        jira_email=(
                            jira_config.jira_email
                        ),
                        jira_api_token=(
                            jira_config.jira_api_token
                        ),
                        jql=feature_jql,
                        environment_field=(
                            jira_config.environment_field
                            if jira_config.environment_field
                            else None
                        ),
                    )
                )

                jira_features = (
                    feature_data.get(
                        "issues",
                        [],
                    )
                    if feature_data
                    else []
                )

            except Exception as exc:

                import traceback

                print(
                    "HTML report Jira feature fetch failed:",
                    exc,
                )

                traceback.print_exc()

                jira_features = []

    # ==========================================================
    # Generate HTML
    # ==========================================================

    try:

        html = generate_project_report_html(
            db=db,
            project_id=project_id,

            # Jira summary
            jira_total=jira_total,
            jira_uat=jira_uat,
            jira_prod=jira_prod,
            jira_sit=jira_sit,

            # Jira details
            jira_issues=jira_issues,
            jira_features=jira_features,
            jira_sit_issues=jira_sit_issues,
            jira_uat_issues=jira_uat_issues,
            jira_prod_issues=jira_prod_issues,
            jira_issue_environments=jira_issue_environments,
        )

    except Exception as exc:

        import traceback

        print(
            "========================================"
        )

        print(
            "HTML REPORT GENERATION FAILED"
        )

        print(
            "========================================"
        )

        print(
            str(exc)
        )

        traceback.print_exc()

        print(
            "========================================"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate project HTML report: "
                f"{str(exc)}"
            ),
        )

    return HTMLResponse(
        content=html,
        status_code=200,
    )


@router.post(
    "/projects/{project_id}/automation/upload"
)
async def upload_automation_excel(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # ==================================================
    # Validate Project
    # ==================================================

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )


    # ==================================================
    # Validate File
    # ==================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please select an Excel file."
        )


    if not file.filename.lower().endswith(".xlsx"):

        raise HTTPException(
            status_code=400,
            detail="Only .xlsx Excel files are supported."
        )


    # ==================================================
    # Read ALL Excel Sheets
    # ==================================================

    REQUIRED_AUTOMATION_COLUMNS = [
        "S. No.",
        "Comment",
        "Owner",
        "Jira ID",
        "Test case ID",
        "Pre Condition",
        "Test Case Description",
        "Steps",
        "Expected Result",
        "Status",
        "Automat-able",
        "Automated",
    ]

    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded Excel file is empty."
            )

        excel_file = BytesIO(file_content)

        sheets = pd.read_excel(
            excel_file,
            sheet_name=None,
            engine="openpyxl"
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read Excel file: {str(exc)}"
        )





    # ==================================================
    # Validate and Combine Sheets
    # ==================================================

    combined_dataframes = []

    invalid_sheets = []


    for sheet_name, sheet_df in sheets.items():

        # Normalize column names
        sheet_df.columns = [
            str(column).strip()
            for column in sheet_df.columns
        ]


        # Check required columns
        missing_columns = (
                set(REQUIRED_AUTOMATION_COLUMNS)
                - set(sheet_df.columns)
        )


        if missing_columns:

            invalid_sheets.append(
                {
                    "sheet": sheet_name,
                    "missing_columns": sorted(
                        missing_columns
                    ),
                }
            )

            continue


        # Remove completely empty rows
        sheet_df = sheet_df.dropna(
            how="all"
        )


        if sheet_df.empty:
            continue


        # Keep only expected columns
        sheet_df = sheet_df[
            REQUIRED_AUTOMATION_COLUMNS
        ]


        # Add sheet name
        sheet_df["_sheet_name"] = (
            sheet_name
        )


        combined_dataframes.append(
            sheet_df
        )


    # ==================================================
    # Invalid Sheet Check
    # ==================================================

    if invalid_sheets:

        details = []

        for item in invalid_sheets:

            details.append(
                f"Sheet '{item['sheet']}' "
                f"is missing columns: "
                f"{', '.join(item['missing_columns'])}"
            )


        raise HTTPException(
            status_code=400,
            detail="; ".join(details)
        )


    # ==================================================
    # Check Data
    # ==================================================

    if not combined_dataframes:

        raise HTTPException(
            status_code=400,
            detail="No valid automation records found in the Excel file."
        )


    # ==================================================
    # Combine ALL Sheets
    # ==================================================

    df = pd.concat(
        combined_dataframes,
        ignore_index=True
    )


    # ==================================================
    # Helper
    # ==================================================

    def clean_value(value):

        if pd.isna(value):
            return None

        return str(value).strip()


    # ==================================================
    # Create Upload Batch
    # ==================================================

    upload_batch = AutomationUploadBatch(
        project_id=project_id,
        filename=file.filename,
        row_count=0,
    )

    db.add(upload_batch)

    db.flush()


    # ==================================================
    # Insert Test Cases
    # ==================================================

    rows_imported = 0


    for _, row in df.iterrows():

        test_case_id = clean_value(
            row["Test case ID"]
        )


        # Test Case ID is mandatory
        if not test_case_id:

            continue


        # Parse S. No.
        sno = None

        sno_value = row["S. No."]

        if not pd.isna(sno_value):

            try:

                sno = int(
                    float(sno_value)
                )

            except (
                ValueError,
                TypeError
            ):

                sno = None


        test_case = UploadedTestCase(

            upload_batch_id=upload_batch.id,

            project_id=project_id,

            sno=sno,

            comment=clean_value(
                row["Comment"]
            ),

            owner=clean_value(
                row["Owner"]
            ),

            jira_id=clean_value(
                row["Jira ID"]
            ),

            test_case_id=test_case_id,

            pre_condition=clean_value(
                row["Pre Condition"]
            ),

            test_case_description=clean_value(
                row["Test Case Description"]
            ),

            steps=clean_value(
                row["Steps"]
            ),

            expected_result=clean_value(
                row["Expected Result"]
            ),

            status=clean_value(
                row["Status"]
            ),

            automatable=clean_value(
                row["Automat-able"]
            ),

            automated=clean_value(
                row["Automated"]
            ),

        )


        db.add(test_case)

        rows_imported += 1


    # ==================================================
    # Update Row Count
    # ==================================================

    upload_batch.row_count = (
        rows_imported
    )


    # ==================================================
    # Commit
    # ==================================================

    try:

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save Excel data: {str(exc)}"
        )


    # ==================================================
    # Response
    # ==================================================

    return {

        "message":
            "Automation Excel uploaded successfully.",

        "project_id":
            project_id,

        "upload_batch_id":
            upload_batch.id,

        "filename":
            file.filename,

        "sheets_processed":
            len(sheets),

        "rows_imported":
            rows_imported,

    }

@router.get(
    "/projects/{project_id}/automation/uploads/latest",
)
def get_latest_automation_upload(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    upload_batch = (
        db.query(AutomationUploadBatch)
        .filter(
            AutomationUploadBatch.project_id == project_id
        )
        .order_by(
            AutomationUploadBatch.uploaded_at.desc()
        )
        .first()
    )

    if not upload_batch:
        return {
            "upload": None,
            "rows": [],
        }

    rows = (
        db.query(UploadedTestCase)
        .filter(
            UploadedTestCase.upload_batch_id
            == upload_batch.id
        )
        .order_by(
            UploadedTestCase.sno,
            UploadedTestCase.id,
        )
        .all()
    )

    return {
        "upload": AutomationUploadBatchResponse.model_validate(
            upload_batch
        ),
        "rows": [
            UploadedTestCaseResponse.model_validate(row)
            for row in rows
        ],
    }

@router.post(
    "/projects/{project_id}/releases/{release_id}/automation/upload"
)
async def upload_release_automation_excel(
    project_id: int,
    release_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ==================================================
    # Validate Project
    # ==================================================
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # ==================================================
    # Validate Release belongs to Project
    # ==================================================
    release = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.id == release_id,
            AutomationRelease.project_id == project_id,
        )
        .first()
    )

    if not release:
        raise HTTPException(
            status_code=404,
            detail="Release not found for this project",
        )

    # ==================================================
    # Validate File
    # ==================================================
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select an Excel file.",
        )

    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx Excel files are supported.",
        )

    REQUIRED_AUTOMATION_COLUMNS = [
        "S. No.",
        "Comment",
        "Owner",
        "Jira ID",
        "Test case ID",
        "Pre Condition",
        "Test Case Description",
        "Steps",
        "Expected Result",
        "Status",
        "Automat-able",
        "Automated",
    ]

    # ==================================================
    # Read ALL Excel Sheets
    # ==================================================
    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded Excel file is empty.",
            )

        sheets = pd.read_excel(
            BytesIO(file_content),
            sheet_name=None,
            engine="openpyxl",
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read Excel file: {str(exc)}",
        )

    # ==================================================
    # Validate and Combine Sheets
    # ==================================================
    combined_dataframes = []
    invalid_sheets = []

    for sheet_name, sheet_df in sheets.items():
        sheet_df.columns = [
            str(column).strip()
            for column in sheet_df.columns
        ]

        missing_columns = (
            set(REQUIRED_AUTOMATION_COLUMNS)
            - set(sheet_df.columns)
        )

        if missing_columns:
            invalid_sheets.append(
                {
                    "sheet": sheet_name,
                    "missing_columns": sorted(missing_columns),
                }
            )
            continue

        sheet_df = sheet_df.dropna(how="all")

        if sheet_df.empty:
            continue

        sheet_df = sheet_df[REQUIRED_AUTOMATION_COLUMNS]
        sheet_df["_sheet_name"] = sheet_name
        combined_dataframes.append(sheet_df)

    if invalid_sheets:
        details = [
            f"Sheet '{item['sheet']}' is missing columns: "
            f"{', '.join(item['missing_columns'])}"
            for item in invalid_sheets
        ]

        raise HTTPException(
            status_code=400,
            detail="; ".join(details),
        )

    if not combined_dataframes:
        raise HTTPException(
            status_code=400,
            detail="No valid automation records found in the Excel file.",
        )

    df = pd.concat(
        combined_dataframes,
        ignore_index=True,
    )

    def clean_value(value):
        if pd.isna(value):
            return None
        return str(value).strip()

    # ==================================================
    # Create Release Upload Batch
    # ==================================================
    upload_batch = AutomationUploadBatch(
        project_id=project_id,
        release_id=release_id,
        filename=file.filename,
        row_count=0,
    )

    db.add(upload_batch)
    db.flush()

    rows_imported = 0

    for _, row in df.iterrows():
        test_case_id = clean_value(row["Test case ID"])

        if not test_case_id:
            continue

        sno = None
        sno_value = row["S. No."]

        if not pd.isna(sno_value):
            try:
                sno = int(float(sno_value))
            except (ValueError, TypeError):
                sno = None

        test_case = UploadedTestCase(
            upload_batch_id=upload_batch.id,
            project_id=project_id,
            sno=sno,
            comment=clean_value(row["Comment"]),
            owner=clean_value(row["Owner"]),
            jira_id=clean_value(row["Jira ID"]),
            test_case_id=test_case_id,
            pre_condition=clean_value(row["Pre Condition"]),
            test_case_description=clean_value(
                row["Test Case Description"]
            ),
            steps=clean_value(row["Steps"]),
            expected_result=clean_value(row["Expected Result"]),
            status=clean_value(row["Status"]),
            automatable=clean_value(row["Automat-able"]),
            automated=clean_value(row["Automated"]),
            sheet_name=clean_value(row["_sheet_name"]),
        )

        db.add(test_case)
        rows_imported += 1

    upload_batch.row_count = rows_imported

    try:
        db.commit()
        db.refresh(upload_batch)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save Excel data: {str(exc)}",
        )

    return {
        "message": "Automation Excel uploaded successfully.",
        "project_id": project_id,
        "release_id": release_id,
        "upload_batch_id": upload_batch.id,
        "filename": file.filename,
        "sheets_processed": len(sheets),
        "rows_imported": rows_imported,
    }


@router.get(
    "/projects/{project_id}/releases/{release_id}/automation/uploads/latest"
)
def get_latest_release_automation_upload(
    project_id: int,
    release_id: int,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.active.is_(True),
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    release = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.id == release_id,
            AutomationRelease.project_id == project_id,
        )
        .first()
    )

    if not release:
        raise HTTPException(
            status_code=404,
            detail="Release not found for this project",
        )

    upload_batch = (
        db.query(AutomationUploadBatch)
        .filter(
            AutomationUploadBatch.project_id == project_id,
            AutomationUploadBatch.release_id == release_id,
        )
        .order_by(
            AutomationUploadBatch.uploaded_at.desc()
        )
        .first()
    )

    if not upload_batch:
        return {
            "upload": None,
            "rows": [],
        }

    rows = (
        db.query(UploadedTestCase)
        .filter(
            UploadedTestCase.upload_batch_id == upload_batch.id
        )
        .order_by(
            UploadedTestCase.sno,
            UploadedTestCase.id,
        )
        .all()
    )

    return {
        "upload": AutomationUploadBatchResponse.model_validate(
            upload_batch
        ),
        "rows": [
            UploadedTestCaseResponse.model_validate(row)
            for row in rows
        ],
    }
