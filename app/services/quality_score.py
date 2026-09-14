from decimal import Decimal

from app.models.metric_category import MetricCategory
from app.models.metric_definition import MetricDefinition
from app.models.project_metric import ProjectMetric
from app.models.metric_value import MetricValue


def calculate_metric_score(
    value,
    metric_definition,
):
    if value is None:
        return None

    value = Decimal(str(value))

    target = Decimal(
        str(metric_definition.default_target)
    )
    warning = Decimal(
        str(metric_definition.warning_threshold)
    )
    critical = Decimal(
        str(metric_definition.critical_threshold)
    )
    direction = metric_definition.direction

    # ================================================================
    # Automation Coverage
    #
    # Actual automation percentage = score
    #
    # Example:
    # 86% automation = 86 score
    # 75% automation = 75 score
    # 100% automation = 100 score
    # ================================================================
    if metric_definition.metric_key == "automation_coverage":
        return max(
            Decimal("0"),
            min(Decimal("100"), value),
        )

    # ================================================================
    # Production Quality:
    # Every production bug reduces the score by 10 percentage points
    #
    # 0 bugs  = 100
    # 1 bug   = 90
    # 2 bugs  = 80
    # ...
    # 10 bugs = 0
    # 10+ bugs = 0
    # ================================================================
    if metric_definition.metric_key in (
        "prod_bugs_3_months",
        "prod_bugs_1_month",
    ):
        score = Decimal("100") - (
            value * Decimal("10")
        )

        return max(
            Decimal("0"),
            min(Decimal("100"), score),
        )

    if direction == "higher_is_better":

        if value >= target:
            return Decimal("100")

        if value >= warning:

            if target == warning:
                return Decimal("75")

            return Decimal("75") + (
                (value - warning)
                / (target - warning)
            ) * Decimal("25")

        if value >= critical:

            if warning == critical:
                return Decimal("40")

            return Decimal("40") + (
                (value - critical)
                / (warning - critical)
            ) * Decimal("35")

        return max(
            Decimal("0"),
            (value / critical) * Decimal("40")
        )

    if direction == "lower_is_better":

        if value <= target:
            return Decimal("100")

        if value <= warning:

            if warning == target:
                return Decimal("75")

            return Decimal("75") + (
                (warning - value)
                / (warning - target)
            ) * Decimal("25")

        if value <= critical:

            if critical == warning:
                return Decimal("40")

            return Decimal("40") + (
                (critical - value)
                / (critical - warning)
            ) * Decimal("35")

        return Decimal("0")

    return Decimal("0")

def calculate_category_score(
    db,
    project_id,
    category,
):
    """
    Calculate weighted score for one metric category.
    """

    project_metrics = (
        db.query(ProjectMetric)
        .join(
            MetricDefinition,
            ProjectMetric.metric_definition_id
            == MetricDefinition.id,
        )
        .filter(
            ProjectMetric.project_id == project_id,
            ProjectMetric.enabled == True,
            MetricDefinition.category_id == category.id,
        )
        .all()
    )

    weighted_score = Decimal("0")
    total_weight = Decimal("0")

    for project_metric in project_metrics:

        metric_definition = (
            db.query(MetricDefinition)
            .filter(
                MetricDefinition.id
                == project_metric.metric_definition_id
            )
            .first()
        )

        if not metric_definition:
            continue

        metric_value = (
            db.query(MetricValue)
            .filter(
                MetricValue.project_metric_id
                == project_metric.id
            )
            .order_by(
                MetricValue.updated_at.desc()
            )
            .first()
        )

        print(
            "QUALITY SCORE DEBUG:",
            {
                "project_id": project_id,
                "category": category.name,
                "metric": metric_definition.name,
                "project_metric_id": project_metric.id,
                "enabled": project_metric.enabled,
                "value": (
                    metric_value.value
                    if metric_value
                    else None
                ),
                "metric_weight":
                    metric_definition.weight,
                "category_weight":
                    category.weight,
                "direction":
                    metric_definition.direction,
                "target":
                    metric_definition.default_target,
                "warning":
                    metric_definition.warning_threshold,
                "critical":
                    metric_definition.critical_threshold,
            }
        )

        if not metric_value:
            continue

        score = calculate_metric_score(
            metric_value.value,
            metric_definition,
        )

        print(
            "QUALITY SCORE RESULT:",
            {
                "metric": metric_definition.name,
                "value": metric_value.value,
                "score": score,
            }
        )

        if score is None:
            continue

        weight = Decimal(
            str(metric_definition.weight)
        )

        if weight <= 0:
            continue

        weighted_score += (
            score * weight
        )

        total_weight += weight

    if total_weight == 0:
        return None

    return (
        weighted_score
        / total_weight
    )
def calculate_quality_confidence_score(
    db,
    project_id,
):
    categories = (
        db.query(MetricCategory)
        .order_by(
            MetricCategory.display_order
        )
        .all()
    )

    category_results = []

    total_score = Decimal("0")
    total_weight = Decimal("0")

    for category in categories:

        score = calculate_category_score(
            db,
            project_id,
            category,
        )

        weight = Decimal(
            str(category.weight)
        )

        category_results.append(
            {
                "category_id": category.id,
                "category_name": category.name,
                "score": (
                    float(score)
                    if score is not None
                    else None
                ),
                "weight": float(weight),
            }
        )

        if score is not None and weight > 0:

            total_score += (
                score * weight
            )

            total_weight += weight

    if total_weight == 0:

        overall_score = None

    else:

        overall_score = (
            total_score / total_weight
        )

    return {
        "project_id": project_id,
        "score": (
            round(float(overall_score), 2)
            if overall_score is not None
            else None
        ),
        "status": get_score_status(
            overall_score
        ),
        "categories": category_results,
    }

def get_score_status(score):

    if score is None:
        return "NO_DATA"

    score = Decimal(str(score))

    if score >= 80:
        return "STRONG"

    if score >= 60:
        return "MODERATE"

    return "LOW"
