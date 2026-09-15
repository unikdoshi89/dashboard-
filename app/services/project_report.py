from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.metric_category import MetricCategory
from app.models.metric_definition import MetricDefinition
from app.models.project_metric import ProjectMetric
from app.models.metric_value import MetricValue
from app.models.automation_release import AutomationRelease
from app.models.automation_detail import AutomationDetail
from collections import defaultdict
from app.models.jira_configuration import JiraConfiguration

from app.models.automation_detail import AutomationUploadBatch
from app.models.automation_detail import UploadedTestCase

from app.services.quality_score import (
    calculate_quality_confidence_score,
)


def _status_color(status):
    if not status:
        return colors.grey

    status = str(status).upper()

    if status in ("GREEN", "PASS", "GOOD", "STRONG"):
        return colors.HexColor("#16A34A")

    if status in ("AMBER", "WARNING", "MODERATE"):
        return colors.HexColor("#D97706")

    if status in ("RED", "CRITICAL", "FAIL", "LOW"):
        return colors.HexColor("#DC2626")

    return colors.grey


def _safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _is_yes(value):
    """
    Convert Excel Yes/No style values into a boolean.
    Supports:
    Yes / Y / TRUE / 1
    No / N / FALSE / 0
    """
    if value is None:
        return False

    value = str(value).strip().upper()

    return value in (
        "YES",
        "Y",
        "TRUE",
        "1",
    )


def generate_project_report_pdf(
    db: Session,
    project_id: int,
    jira_total: int = 0,
    jira_uat: int = 0,
    jira_prod: int = 0,
    jira_sit: int = 0,
):
    """
    Generate a complete QE Governance PDF report
    for one project.
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise ValueError("Project not found")

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "NormalReport",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = []

    # ==========================================================
    # HEADER
    # ==========================================================

    story.append(
        Paragraph(
            "QE Governance Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"{project.name} — {project.project_key}",
            subtitle_style,
        )
    )

    project_info = [
        ["Project", project.name],
        ["Project Key", project.project_key],
        [
            "Description",
            project.description or "N/A",
        ],
        [
            "Generated",
            datetime.now().strftime(
                "%d-%b-%Y %H:%M"
            ),
        ],
    ]

    info_table = Table(
        project_info,
        colWidths=[40 * mm, 135 * mm],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#EFF6FF"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#1E40AF"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(info_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # QUALITY CONFIDENCE SCORE
    # ==========================================================

    score_data = calculate_quality_confidence_score(
        db,
        project_id,
    )

    story.append(
        Paragraph(
            "Quality Confidence Score",
            section_style,
        )
    )

    score = score_data.get("score")
    score_status = score_data.get("status")

    score_display = (
        f"{float(score):.1f}"
        if score is not None
        else "N/A"
    )

    score_table = Table(
        [
            [
                "Quality Confidence Score",
                score_display,
                score_status or "NO_DATA",
            ]
        ],
        colWidths=[
            75 * mm,
            45 * mm,
            55 * mm,
        ],
    )

    score_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F8FAFC"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (1, 0),
                    (1, 0),
                    20,
                ),
                (
                    "TEXTCOLOR",
                    (2, 0),
                    (2, 0),
                    _status_color(score_status),
                ),
                (
                    "FONTNAME",
                    (2, 0),
                    (2, 0),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (2, 0),
                    "CENTER",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(score_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # CATEGORY SCORE TABLE
    # ==========================================================

    story.append(
        Paragraph(
            "Quality Category Summary",
            section_style,
        )
    )

    category_rows = [
        [
            "Category",
            "Weight",
            "Score",
            "Status",
        ]
    ]

    for category in score_data.get(
        "categories",
        [],
    ):
        category_score = category.get("score")

        category_rows.append(
            [
                category.get(
                    "category_name",
                    "",
                ),
                f"{category.get('weight', 0)}%",
                (
                    f"{float(category_score):.1f}"
                    if category_score is not None
                    else "N/A"
                ),
                (
                    "NO_DATA"
                    if category_score is None
                    else "AVAILABLE"
                ),
            ]
        )

    category_table = Table(
        category_rows,
        colWidths=[
            90 * mm,
            25 * mm,
            30 * mm,
            30 * mm,
        ],
        repeatRows=1,
    )

    category_style = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#1E3A8A"),
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white,
        ),
        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold",
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#CBD5E1"),
        ),
        (
            "ALIGN",
            (1, 1),
            (-1, -1),
            "CENTER",
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            6,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            6,
        ),
    ]

    for row_index in range(
        1,
        len(category_rows),
    ):
        category_status = category_rows[
            row_index
        ][3]

        if category_status == "AVAILABLE":
            category_style.append(
                (
                    "TEXTCOLOR",
                    (3, row_index),
                    (3, row_index),
                    colors.HexColor("#16A34A"),
                )
            )

    category_table.setStyle(
        TableStyle(category_style)
    )

    story.append(category_table)
    story.append(Spacer(1, 15))

    # ==========================================================
    # METRICS
    # ==========================================================

    story.append(
        Paragraph(
            "Dashboard Metrics",
            section_style,
        )
    )

    categories = (
        db.query(MetricCategory)
        .order_by(
            MetricCategory.display_order
        )
        .all()
    )

    for category in categories:

        project_metrics = (
            db.query(
                ProjectMetric,
                MetricDefinition,
                MetricValue,
            )
            .join(
                MetricDefinition,
                ProjectMetric.metric_definition_id
                == MetricDefinition.id,
            )
            .outerjoin(
                MetricValue,
                MetricValue.project_metric_id
                == ProjectMetric.id,
            )
            .filter(
                ProjectMetric.project_id
                == project_id,
                ProjectMetric.enabled.is_(True),
                MetricDefinition.category_id
                == category.id,
            )
            .order_by(
                MetricDefinition.display_order
            )
            .all()
        )

        if not project_metrics:
            continue

        story.append(
            Paragraph(
                category.name,
                ParagraphStyle(
                    f"Category_{category.id}",
                    parent=styles["Heading3"],
                    fontSize=11,
                    textColor=colors.HexColor(
                        "#334155"
                    ),
                    spaceBefore=8,
                    spaceAfter=5,
                ),
            )
        )

        metric_rows = [
            [
                "Metric",
                "Value",
                "Unit",
                "Target",
                "Status",
            ]
        ]

        metric_statuses = []

        for (
            project_metric,
            definition,
            metric_value,
        ) in project_metrics:

            value = (
                _safe_float(
                    metric_value.value
                )
                if metric_value
                else None
            )

            target = _safe_float(
                definition.default_target
            )

            status = (
                metric_value.status
                if metric_value
                else "NO_DATA"
            )

            metric_rows.append(
                [
                    definition.name,
                    (
                        f"{value:.2f}"
                        if value is not None
                        else "N/A"
                    ),
                    definition.unit,
                    (
                        f"{target:.2f}"
                        if target is not None
                        else "N/A"
                    ),
                    status,
                ]
            )

            metric_statuses.append(
                status
            )

        metric_table = Table(
            metric_rows,
            colWidths=[
                75 * mm,
                25 * mm,
                20 * mm,
                25 * mm,
                30 * mm,
            ],
            repeatRows=1,
        )

        metric_style = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#E2E8F0"),
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER",
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ]

        for row_index, status in enumerate(
            metric_statuses,
            start=1,
        ):
            metric_style.append(
                (
                    "TEXTCOLOR",
                    (4, row_index),
                    (4, row_index),
                    _status_color(status),
                )
            )

            metric_style.append(
                (
                    "FONTNAME",
                    (4, row_index),
                    (4, row_index),
                    "Helvetica-Bold",
                )
            )

        metric_table.setStyle(
            TableStyle(metric_style)
        )

        story.append(metric_table)
        story.append(Spacer(1, 8))

    # ==========================================================
    # AUTOMATION DETAILS
    # ==========================================================

    releases = (
        db.query(AutomationRelease)
        .filter(
            AutomationRelease.project_id
            == project_id
        )
        .order_by(
            AutomationRelease.release_order,
            AutomationRelease.id,
        )
        .all()
    )

    if releases:

        story.append(PageBreak())

        story.append(
            Paragraph(
                "Automation Details",
                section_style,
            )
        )

        automation_rows = [
            [
                "Release",
                "POD",
                "Requirements + RTB",
                "Test Cases",
                "Automatable",
                "Automated",
                "Automation %",
            ]
        ]

        total_rtb = 0
        total_test_cases = 0
        total_automatable = 0
        total_automated = 0

        for release in releases:

            details = (
                db.query(AutomationDetail)
                .filter(
                    AutomationDetail.release_id
                    == release.id
                )
                .order_by(
                    AutomationDetail.id
                )
                .all()
            )

            for detail in details:
                automation_percentage = (
                    (
                            detail.automated
                            / detail.automatable
                    ) * 100
                    if detail.automatable > 0
                    else None
                )

                automation_rows.append(
                    [
                        release.release_name,
                        detail.pod,
                        detail.requirements_rtb,
                        detail.test_cases,
                        detail.automatable,
                        detail.automated,
                        (
                            f"{automation_percentage:.2f}%"
                            if automation_percentage is not None
                            else "—"
                        ),
                    ]
                )

                total_rtb += detail.requirements_rtb
                total_test_cases += detail.test_cases
                total_automatable += detail.automatable
                total_automated += detail.automated

        total_automation_percentage = (
            (
                    total_automated
                    / total_automatable
            ) * 100
            if total_automatable > 0
            else None
        )

        automation_rows.append(
            [
                "TOTAL",
                "",
                total_rtb,
                total_test_cases,
                total_automatable,
                total_automated,
                (
                    f"{total_automation_percentage:.2f}%"
                    if total_automation_percentage is not None
                    else "—"
                ),
            ]
        )

        automation_table = Table(
            automation_rows,
            colWidths=[
                35 * mm,
                25 * mm,
                28 * mm,
                22 * mm,
                22 * mm,
                22 * mm,
                23 * mm,
            ],
            repeatRows=1,
        )

        automation_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1E3A8A"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "BACKGROUND",
                        (0, -1),
                        (-1, -1),
                        colors.HexColor("#DBEAFE"),
                    ),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "ALIGN",
                        (2, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(automation_table)

        # Automation percentages

        story.append(Spacer(1, 12))

        automation_percentage = (
            (
                total_automated
                / total_test_cases
                * 100
            )
            if total_test_cases
            else 0
        )

        automation_percentage = (
            (
                    total_automated
                    / total_automatable
                    * 100
            )
            if total_automatable > 0
            else None
        )

        automation_summary = Table(
            [
                [
                    "Automation %",
                    (
                        f"{automation_percentage:.2f}%"
                        if automation_percentage is not None
                        else "—"
                    ),
                    "Automatable",
                    total_automatable,
                    "Automated",
                    total_automated,
                ]
            ],
            colWidths=[
                35 * mm,
                30 * mm,
                35 * mm,
                25 * mm,
                30 * mm,
                25 * mm,
            ],
        )

        automation_summary.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#F8FAFC"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (2, 0),
                        (2, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (1, 0),
                        (1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (3, 0),
                        (3, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "TEXTCOLOR",
                        (1, 0),
                        (1, 0),
                        colors.HexColor("#16A34A"),
                    ),
                    (
                        "TEXTCOLOR",
                        (3, 0),
                        (3, 0),
                        colors.HexColor("#16A34A"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "ALIGN",
                        (1, 0),
                        (1, 0),
                        "CENTER",
                    ),
                    (
                        "ALIGN",
                        (3, 0),
                        (3, 0),
                        "CENTER",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.append(automation_summary)

        # ==========================================================
        # RTM & AUTOMATION DETAIL SUMMARY
        # ==========================================================

        latest_upload = (
            db.query(AutomationUploadBatch)
            .filter(
                AutomationUploadBatch.project_id
                == project_id
            )
            .order_by(
                AutomationUploadBatch.uploaded_at.desc(),
                AutomationUploadBatch.id.desc(),
            )
            .first()
        )

        if latest_upload:

            rtm_rows = (
                db.query(UploadedTestCase)
                .filter(
                    UploadedTestCase.upload_batch_id
                    == latest_upload.id
                )
                .order_by(
                    UploadedTestCase.jira_id,
                    UploadedTestCase.id,
                )
                .all()
            )

            if rtm_rows:

                story.append(PageBreak())

                story.append(
                    Paragraph(
                        "RTM & Automation Detail",
                        section_style,
                    )
                )

                story.append(
                    Paragraph(
                        (
                            f"Source: {latest_upload.filename} "
                            f"| Test Cases: {latest_upload.row_count} "
                            f"| Uploaded: "
                            f"{latest_upload.uploaded_at.strftime('%d-%b-%Y %H:%M')}"
                        ),
                        small_style,
                    )
                )

                story.append(Spacer(1, 8))

                # ------------------------------------------------------
                # Group uploaded test cases by Jira ID
                # ------------------------------------------------------

                jira_summary = defaultdict(
                    lambda: {
                        "total": 0,
                        "automatable": 0,
                        "automated": 0,
                    }
                )

                for test_case in rtm_rows:

                    jira_id = (
                        str(test_case.jira_id).strip()
                        if test_case.jira_id
                        else "NO JIRA ID"
                    )

                    jira_summary[jira_id]["total"] += 1

                    if _is_yes(test_case.automatable):
                        jira_summary[jira_id]["automatable"] += 1

                    if _is_yes(test_case.automated):
                        jira_summary[jira_id]["automated"] += 1

                # ------------------------------------------------------
                # RTM summary table
                # ------------------------------------------------------

                rtm_summary_rows = [
                    [
                        "Jira ID",
                        "Test Cases",
                        "Automatable",
                        "Automated",
                        "Not Automated",
                        "Automation %",
                    ]
                ]

                grand_total = 0
                grand_automatable = 0
                grand_automated = 0

                for jira_id, summary in sorted(
                        jira_summary.items()
                ):
                    total = summary["total"]
                    automatable = summary["automatable"]
                    automated = summary["automated"]

                    not_automated = max(
                        automatable - automated,
                        0,
                    )

                    automation_percentage = (
                        (
                                automated
                                / automatable
                        ) * 100
                        if automatable > 0
                        else None
                    )

                    rtm_summary_rows.append(
                        [
                            jira_id,
                            total,
                            automatable,
                            automated,
                            not_automated,
                            (
                                f"{automation_percentage:.2f}%"
                                if automation_percentage is not None
                                else "—"
                            ),
                        ]
                    )

                    grand_total += total
                    grand_automatable += automatable
                    grand_automated += automated

                grand_not_automated = max(
                    grand_automatable - grand_automated,
                    0,
                )

                grand_automation_percentage = (
                    (
                            grand_automated
                            / grand_automatable
                    ) * 100
                    if grand_automatable > 0
                    else None
                )

                rtm_summary_rows.append(
                    [
                        "TOTAL",
                        grand_total,
                        grand_automatable,
                        grand_automated,
                        grand_not_automated,
                        (
                            f"{grand_automation_percentage:.2f}%"
                            if grand_automation_percentage is not None
                            else "—"
                        ),
                    ]
                )

                rtm_summary_table = Table(
                    rtm_summary_rows,
                    colWidths=[
                        45 * mm,
                        25 * mm,
                        28 * mm,
                        25 * mm,
                        30 * mm,
                        32 * mm,
                    ],
                    repeatRows=1,
                )

                rtm_summary_style = [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1E3A8A"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "BACKGROUND",
                        (0, -1),
                        (-1, -1),
                        colors.HexColor("#DBEAFE"),
                    ),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]

                # Color Automation % column
                for row_index in range(
                        1,
                        len(rtm_summary_rows),
                ):
                    rtm_summary_style.append(
                        (
                            "TEXTCOLOR",
                            (5, row_index),
                            (5, row_index),
                            colors.HexColor("#16A34A"),
                        )
                    )

                    rtm_summary_style.append(
                        (
                            "FONTNAME",
                            (5, row_index),
                            (5, row_index),
                            "Helvetica-Bold",
                        )
                    )

                rtm_summary_table.setStyle(
                    TableStyle(rtm_summary_style)
                )

                story.append(rtm_summary_table)

                story.append(Spacer(1, 15))

                # ------------------------------------------------------
                # Overall RTM summary cards
                # ------------------------------------------------------

                story.append(
                    Paragraph(
                        "RTM Overall Summary",
                        ParagraphStyle(
                            "RTMSummaryHeading",
                            parent=styles["Heading3"],
                            fontSize=11,
                            textColor=colors.HexColor(
                                "#334155"
                            ),
                            spaceBefore=5,
                            spaceAfter=5,
                        ),
                    )
                )

                rtm_overall_table = Table(
                    [
                        [
                            "Total Test Cases",
                            grand_total,
                            "Automatable",
                            grand_automatable,
                            "Automated",
                            grand_automated,
                            "Automation %",
                            (
                                f"{grand_automation_percentage:.2f}%"
                                if grand_automation_percentage
                                   is not None
                                else "—"
                            ),
                        ]
                    ],
                    colWidths=[
                        28 * mm,
                        18 * mm,
                        25 * mm,
                        18 * mm,
                        22 * mm,
                        18 * mm,
                        25 * mm,
                        25 * mm,
                    ],
                )

                rtm_overall_table.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, -1),
                                colors.HexColor("#F8FAFC"),
                            ),
                            (
                                "FONTNAME",
                                (0, 0),
                                (-1, -1),
                                "Helvetica-Bold",
                            ),
                            (
                                "TEXTCOLOR",
                                (7, 0),
                                (7, 0),
                                colors.HexColor("#16A34A"),
                            ),
                            (
                                "GRID",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                colors.HexColor("#CBD5E1"),
                            ),
                            (
                                "ALIGN",
                                (1, 0),
                                (-1, 0),
                                "CENTER",
                            ),
                            (
                                "VALIGN",
                                (0, 0),
                                (-1, -1),
                                "MIDDLE",
                            ),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                8,
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                8,
                            ),
                        ]
                    )
                )

                story.append(rtm_overall_table)

                # ------------------------------------------------------
                # Jira Defect Summary
                # ------------------------------------------------------

                # ================================================================
                # Jira Defect Summary
                # ================================================================

                story.append(
                    Spacer(
                        1,
                        8,
                    )
                )

                story.append(
                    Paragraph(
                        "Jira Defect Summary",
                        section_style,
                    )
                )

                jira_summary_data = [
                    [
                        Paragraph(
                            "<b>SIT Bugs</b>",
                            small_style,
                        ),
                        Paragraph(
                            str(jira_sit),
                            small_style,
                        ),
                        Paragraph(
                            "<b>UAT Bugs</b>",
                            small_style,
                        ),
                        Paragraph(
                            str(jira_uat),
                            small_style,
                        ),
                        Paragraph(
                            "<b>Prod Bugs</b>",
                            small_style,
                        ),
                        Paragraph(
                            str(jira_prod),
                            small_style,
                        ),
                    ]
                ]

                jira_summary_table = Table(
                    jira_summary_data,
                    colWidths=[
                        30 * mm,
                        20 * mm,
                        30 * mm,
                        20 * mm,
                        30 * mm,
                        20 * mm,
                    ],
                )

                jira_summary_table.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor("#EAF2F8"),
                            ),
                            (
                                "GRID",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                colors.grey,
                            ),
                            (
                                "ALIGN",
                                (1, 0),
                                (1, 0),
                                "CENTER",
                            ),
                            (
                                "ALIGN",
                                (3, 0),
                                (3, 0),
                                "CENTER",
                            ),
                            (
                                "ALIGN",
                                (5, 0),
                                (5, 0),
                                "CENTER",
                            ),
                            (
                                "VALIGN",
                                (0, 0),
                                (-1, -1),
                                "MIDDLE",
                            ),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                6,
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                6,
                            ),
                        ]
                    )
                )

                story.append(
                    jira_summary_table
                )

    # ==========================================================
    # FOOTER
    # ==========================================================

    def add_page_number(canvas, doc):
        canvas.saveState()

        canvas.setFont(
            "Helvetica",
            8,
        )

        canvas.setFillColor(
            colors.HexColor("#64748B")
        )

        canvas.drawString(
            15 * mm,
            8 * mm,
            "QE Governance",
        )

        canvas.drawRightString(
            A4[0] - 15 * mm,
            8 * mm,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    buffer.seek(0)

    return buffer
