import unittest

import ci.stock_acceptance_overview_ci_check as overview


class StockAcceptanceOverviewCiCheckTests(unittest.TestCase):
    def test_readiness_score_penalizes_failing_upstream_and_risk(self):
        statuses = {name: "pass" for name in overview.UPSTREAM_WEIGHTS}
        statuses["risk_matrix"] = "fail"

        score = overview.readiness_score(statuses, {"low": 1, "medium": 2, "high": 1})

        self.assertLess(score, 70)

    def test_acceptance_state_blocks_on_failing_upstream(self):
        statuses = {name: "pass" for name in overview.UPSTREAM_WEIGHTS}
        statuses["dependency_order"] = "fail"

        self.assertEqual(
            overview.acceptance_state(95, {"high": 0}, statuses),
            "blocked",
        )

    def test_acceptance_state_requires_human_review_for_high_risk(self):
        statuses = {name: "pass" for name in overview.UPSTREAM_WEIGHTS}

        self.assertEqual(
            overview.acceptance_state(95, {"high": 1}, statuses),
            "human_review_required",
        )

    def test_next_action_for_continue_is_safe_scope(self):
        self.assertEqual(
            overview.next_action_for_state("continue"),
            "continue_stock_system_construction_under_current_ci_gates",
        )

    def test_build_acceptance_overview_report_passes_for_current_head(self):
        report = overview.build_acceptance_overview_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertIn(report["state"], {"continue", "review_before_continue", "human_review_required", "blocked"})
        self.assertTrue(report["advice_modes"])
        self.assertEqual(report["upstream_statuses"]["runtime_artifact_governance"], "pass")
        self.assertGreaterEqual(report["runtime_artifact_governance"]["live_runtime_status_count"], 1)

    def test_validate_report_rejects_continue_with_high_risk(self):
        report = overview.build_acceptance_overview_report()
        report["state"] = "continue"
        report["risk_counts"]["high"] = 1

        problems = overview.validate_report(report)

        self.assertIn("continue_state_with_high_risk_items", problems)

    def test_render_markdown_contains_overview_sections(self):
        report = overview.build_acceptance_overview_report()
        markdown = overview.render_markdown(report)

        self.assertIn("Stock Acceptance Overview", markdown)
        self.assertIn("Upstream Statuses", markdown)
        self.assertIn("runtime_artifact_governance", markdown)
        self.assertIn("Risk Counts", markdown)


if __name__ == "__main__":
    unittest.main()
