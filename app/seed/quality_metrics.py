from app.core.database import SessionLocal
from app.models import (
    MetricCategory,
    MetricDefinition,
)


CATEGORIES = [
    {
        "name": "Coverage Indicators",
        "display_order": 1,
        "weight": 35,
    },
    {
        "name": "Detection Capability",
        "display_order": 2,
        "weight": 30,
    },
    {
        "name": "Effectiveness",
        "display_order": 3,
        "weight": 25,
    },
    {
        "name": "Continuous Improvement",
        "display_order": 4,
        "weight": 10,
    },
]

METRICS = [
    # ==================================================
    # COVERAGE INDICATORS
    # ==================================================

    {
        "category": "Coverage Indicators",
        "metric_key": "requirements_scenario_coverage",
        "name": "Requirements → Scenario Coverage",
        "description": (
            "Requirements with mapped scenarios "
            "divided by total requirements."
        ),
        "unit": "%",
        "default_target": 95,
        "warning_threshold": 80,
        "critical_threshold": 60,
        "direction": "higher_is_better",
        "display_order": 1,
        "weight": 15,
    },

    {
        "category": "Coverage Indicators",
        "metric_key": "scenario_test_case_coverage",
        "name": "Scenario → Test Case Coverage",
        "description": (
            "Scenarios with mapped test cases "
            "divided by total scenarios."
        ),
        "unit": "%",
        "default_target": 95,
        "warning_threshold": 80,
        "critical_threshold": 60,
        "direction": "higher_is_better",
        "display_order": 2,
        "weight": 15,
    },

    {
        "category": "Coverage Indicators",
        "metric_key": "test_execution_coverage",
        "name": "Test Execution Coverage",
        "description": (
            "Executed test cases divided by "
            "total planned test cases."
        ),
        "unit": "%",
        "default_target": 95,
        "warning_threshold": 80,
        "critical_threshold": 60,
        "direction": "higher_is_better",
        "display_order": 3,
        "weight": 15,
    },

    {
        "category": "Coverage Indicators",
        "metric_key": "sit_flow_coverage",
        "name": "SIT Flow Coverage",
        "description": (
            "Executed SIT flows divided by "
            "total identified SIT flows."
        ),
        "unit": "%",
        "default_target": 95,
        "warning_threshold": 80,
        "critical_threshold": 60,
        "direction": "higher_is_better",
        "display_order": 4,
        "weight": 10,
    },

    {
        "category": "Coverage Indicators",
        "metric_key": "api_interface_coverage",
        "name": "API / Interface Coverage",
        "description": (
            "APIs or interfaces tested divided by "
            "total identified APIs or interfaces."
        ),
        "unit": "%",
        "default_target": 95,
        "warning_threshold": 80,
        "critical_threshold": 60,
        "direction": "higher_is_better",
        "display_order": 5,
        "weight": 10,
    },

    {
        "category": "Coverage Indicators",
        "metric_key": "uat_business_process_coverage",
        "name": "UAT Business Process Coverage",
        "description": (
            "Business processes tested divided by "
            "total identified business processes."
        ),
        "unit": "%",
        "default_target": 95,
        "warning_threshold": 80,
        "critical_threshold": 60,
        "direction": "higher_is_better",
        "display_order": 6,
        "weight": 10,
    },

    {
        "category": "Coverage Indicators",
        "metric_key": "risk_based_coverage",
        "name": "Risk-Based Coverage",
        "description": (
            "High-risk items tested divided by "
            "total high-risk items."
        ),
        "unit": "%",
        "default_target": 100,
        "warning_threshold": 85,
        "critical_threshold": 70,
        "direction": "higher_is_better",
        "display_order": 7,
        "weight": 15,
    },


    # ==================================================
    # DETECTION CAPABILITY
    # ==================================================

    {
        "category": "Detection Capability",
        "metric_key": "sit_defect_leakage",
        "name": "Defect Leakage from SIT",
        "description": (
            "Defects found in SIT divided by "
            "total defects from SIT and UAT."
        ),
        "unit": "%",
        "default_target": 10,
        "warning_threshold": 20,
        "critical_threshold": 30,
        "direction": "lower_is_better",
        "display_order": 1,
        "weight": 20,
    },

    {
        "category": "Detection Capability",
        "metric_key": "uat_defect_leakage",
        "name": "Defect Leakage from UAT",
        "description": (
            "Defects found in UAT divided by "
            "total defects from UAT."
        ),
        "unit": "%",
        "default_target": 10,
        "warning_threshold": 20,
        "critical_threshold": 30,
        "direction": "lower_is_better",
        "display_order": 2,
        "weight": 15,
    },

    {
        "category": "Detection Capability",
        "metric_key": "regression_automation_detection",
        "name": "Regression Automation Detection %",
        "description": (
            "Defects found by regression automation "
            "divided by total regression defects found "
            "pre-release."
        ),
        "unit": "%",
        "default_target": 80,
        "warning_threshold": 60,
        "critical_threshold": 40,
        "direction": "higher_is_better",
        "display_order": 3,
        "weight": 20,
    },

    {
        "category": "Detection Capability",
        "metric_key": "detection_per_100_automated_tests",
        "name": "Detection per 100 Automated Tests",
        "description": (
            "Defects found by automation per "
            "100 automated tests executed."
        ),
        "unit": "%",
        "default_target": 5,
        "warning_threshold": 2,
        "critical_threshold": 1,
        "direction": "higher_is_better",
        "display_order": 4,
        "weight": 10,
    },

    {
        "category": "Detection Capability",
        "metric_key": "high_risk_detection",
        "name": "High-Risk Detection %",
        "description": (
            "High-risk regression defects caught by "
            "automation divided by total high-risk "
            "regression defects."
        ),
        "unit": "%",
        "default_target": 90,
        "warning_threshold": 70,
        "critical_threshold": 50,
        "direction": "higher_is_better",
        "display_order": 5,
        "weight": 20,
    },

    {
        "category": "Detection Capability",
        "metric_key": "missed_regression_defects",
        "name": "Missed Regression Defects",
        "description": (
            "Regression defects not detected "
            "before release."
        ),
        "unit": "count",
        "default_target": 0,
        "warning_threshold": 2,
        "critical_threshold": 5,
        "direction": "lower_is_better",
        "display_order": 6,
        "weight": 15,
    },


    # ==================================================
    # EFFECTIVENESS
    # ==================================================

    {
        "category": "Effectiveness",
        "metric_key": "defect_severity_mix_late_stage",
        "name": "Defect Severity Mix - Late Stage",
        "description": (
            "Severity distribution of defects found "
            "in UAT or Production."
        ),
        "unit": "%",
        "default_target": 5,
        "warning_threshold": 10,
        "critical_threshold": 20,
        "direction": "lower_is_better",
        "display_order": 1,
        "weight": 35,
    },

    {
        "category": "Effectiveness",
        "metric_key": "test_case_reopen_rate",
        "name": "Test Case Reopen Rate",
        "description": (
            "Reopened test cases divided by "
            "total executed test cases."
        ),
        "unit": "%",
        "default_target": 5,
        "warning_threshold": 10,
        "critical_threshold": 20,
        "direction": "lower_is_better",
        "display_order": 2,
        "weight": 30,
    },

    {
        "category": "Effectiveness",
        "metric_key": "production_incident_volume",
        "name": "Production Incident Volume",
        "description": (
            "Total production incidents raised "
            "after go-live."
        ),
        "unit": "count",
        "default_target": 0,
        "warning_threshold": 3,
        "critical_threshold": 5,
        "direction": "lower_is_better",
        "display_order": 3,
        "weight": 35,
    },
]


def get_or_create_category(
    db,
    name,
    display_order,
    weight,
):
    category = (
        db.query(MetricCategory)
        .filter(
            MetricCategory.name == name
        )
        .first()
    )

    if category:
        category.display_order = display_order
        category.weight = weight
        return category

    category = MetricCategory(
        name=name,
        display_order=display_order,
        weight=weight,
    )

    db.add(category)
    db.flush()

    return category


def seed_categories():

    db = SessionLocal()

    try:

        category_map = {}

        for category_data in CATEGORIES:

            category = get_or_create_category(
                db,
                category_data["name"],
                category_data["display_order"],
                category_data["weight"],
            )

            category_map[
                category.name
            ] = category

        db.commit()

        print(
            "Quality metric categories seeded successfully."
        )

        for category in category_map.values():
            print(
                f"{category.id}: "
                f"{category.name} "
                f"({category.weight}%)"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def seed_metrics(db):
    for metric_data in METRICS:

        category = (
            db.query(MetricCategory)
            .filter(
                MetricCategory.name ==
                metric_data["category"]
            )
            .first()
        )

        if not category:
            raise RuntimeError(
                f"Category not found: "
                f"{metric_data['category']}"
            )

        metric = (
            db.query(MetricDefinition)
            .filter(
                MetricDefinition.metric_key ==
                metric_data["metric_key"]
            )
            .first()
        )

        if metric:

            metric.category_id = category.id
            metric.name = metric_data["name"]
            metric.description = metric_data["description"]
            metric.unit = metric_data["unit"]
            metric.default_target = metric_data["default_target"]
            metric.warning_threshold = metric_data["warning_threshold"]
            metric.critical_threshold = metric_data["critical_threshold"]
            metric.direction = metric_data["direction"]
            metric.display_order = metric_data["display_order"]
            metric.weight = metric_data["weight"]

        else:

            metric = MetricDefinition(
                category_id=category.id,
                metric_key=metric_data["metric_key"],
                name=metric_data["name"],
                description=metric_data["description"],
                unit=metric_data["unit"],
                default_target=metric_data["default_target"],
                warning_threshold=metric_data["warning_threshold"],
                critical_threshold=metric_data["critical_threshold"],
                direction=metric_data["direction"],
                display_order=metric_data["display_order"],
                weight=metric_data["weight"],
            )

            db.add(metric)


def seed_quality_metrics():

    db = SessionLocal()

    try:

        category_map = {}

        # ------------------------------------------
        # Categories
        # ------------------------------------------

        for category_data in CATEGORIES:

            category = get_or_create_category(
                db,
                category_data["name"],
                category_data["display_order"],
                category_data["weight"],
            )

            category_map[
                category.name
            ] = category

        db.flush()

        # ------------------------------------------
        # Metrics
        # ------------------------------------------

        seed_metrics(db)

        db.commit()

        print(
            "\nQuality Governance metrics "
            "seeded successfully.\n"
        )

        for category in category_map.values():

            count = (
                db.query(MetricDefinition)
                .filter(
                    MetricDefinition.category_id ==
                    category.id
                )
                .count()
            )

            print(
                f"{category.name}: "
                f"{count} metrics | "
                f"Weight: {category.weight}%"
            )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    seed_quality_metrics()
