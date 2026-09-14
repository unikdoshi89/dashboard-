
from alembic import op
import sqlalchemy as sa


def upgrade():
    # ============================================================
    # 1. Update category weights
    # ============================================================

    op.execute("""
        UPDATE metric_categories
        SET
            name = 'Test Design & Coverage',
            weight = 30.00,
            display_order = 1
        WHERE id = 7
    """)

    op.execute("""
        UPDATE metric_categories
        SET
            name = 'Detection Capability',
            weight = 15.00,
            display_order = 2
        WHERE id = 11
    """)

    op.execute("""
        UPDATE metric_categories
        SET
            name = 'Automation Coverage & Stability',
            weight = 15.00,
            display_order = 3
        WHERE id = 8
    """)

    op.execute("""
        UPDATE metric_categories
        SET
            name = 'Effectiveness',
            weight = 15.00,
            display_order = 4
        WHERE id = 12
    """)

    op.execute("""
        UPDATE metric_categories
        SET
            name = 'Production Quality',
            weight = 15.00,
            display_order = 5
        WHERE id = 9
    """)

    op.execute("""
        UPDATE metric_categories
        SET
            name = 'Continuous Improvement',
            weight = 10.00,
            display_order = 6
        WHERE id = 13
    """)

    # ============================================================
    # 2. Move selected Coverage metrics into category 7
    # ============================================================

    op.execute("""
        UPDATE metric_definitions
        SET
            category_id = 7,
            weight = CASE metric_key
                WHEN 'requirements_scenario_coverage' THEN 15.00
                WHEN 'scenario_test_case_coverage' THEN 15.00
                WHEN 'test_execution_coverage' THEN 25.00
                WHEN 'api_interface_coverage' THEN 15.00
                ELSE weight
            END,
            display_order = CASE metric_key
                WHEN 'requirements_scenario_coverage' THEN 2
                WHEN 'scenario_test_case_coverage' THEN 3
                WHEN 'test_execution_coverage' THEN 4
                WHEN 'api_interface_coverage' THEN 5
                ELSE display_order
            END
        WHERE metric_key IN (
            'requirements_scenario_coverage',
            'scenario_test_case_coverage',
            'test_execution_coverage',
            'api_interface_coverage'
        )
    """)

    # ============================================================
    # 3. RTM Completeness
    #
    # It already exists in your current DB according to the
    # database output you provided.
    # ============================================================

    op.execute("""
        UPDATE metric_definitions
        SET
            category_id = 7,
            weight = 30.00,
            display_order = 1
        WHERE metric_key = 'rtm_completeness'
    """)

    # ============================================================
    # 4. Temporarily retain the other old Test Design metrics,
    #    but give them zero weight.
    #
    # They will not affect the score.
    # ============================================================

    op.execute("""
        UPDATE metric_definitions
        SET
            category_id = 7,
            weight = 0.00
        WHERE metric_key IN (
            'negative_test_ratio',
            'integration_test_percentage',
            'risk_coverage',
            'late_test_creation',
            'qe_participation_rate'
        )
    """)

    # ============================================================
    # 5. Move the remaining Coverage metrics to category 7
    #    with zero weight for now.
    # ============================================================

    op.execute("""
        UPDATE metric_definitions
        SET
            category_id = 7,
            weight = 0.00
        WHERE metric_key IN (
            'sit_flow_coverage',
            'uat_business_process_coverage',
            'risk_based_coverage'
        )
    """)

    # ============================================================
    # 6. Remove the now-unused Coverage category.
    # ============================================================

    op.execute("""
        DELETE FROM metric_categories
        WHERE id = 10
    """)


def downgrade():
    # We intentionally do not attempt to reconstruct the previous
    # category structure automatically.
    #
    # A downgrade should be handled with a dedicated migration
    # if rollback is ever required.
    pass
