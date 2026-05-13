import unittest

import ci.stock_safe_boundary_ci_check as safe_boundary


class StockSafeBoundaryCiCheckTests(unittest.TestCase):
    def test_safe_duplicate_workstreams_include_expected_targets(self):
        report = safe_boundary.build_safe_boundary_report()
        targets = {item["number"] for item in report["duplicate_workstreams"]}

        self.assertTrue(safe_boundary.EXPECTED_DUPLICATE_TARGETS.issubset(targets))

    def test_safe_duplicate_has_expected_roles_and_preconditions(self):
        report = safe_boundary.build_safe_boundary_report()
        item = next(item for item in report["duplicate_workstreams"] if item["number"] == "243")

        self.assertTrue(
            safe_boundary.EXPECTED_DUPLICATE_ROLES.issubset(
                safe_boundary.duplicate_directory_roles(item)
            )
        )
        for precondition in safe_boundary.REQUIRED_MERGE_PRECONDITIONS:
            self.assertIn(precondition, item["merge_preconditions"])

    def test_safe_topic_workstreams_include_acceptance_topic(self):
        report = safe_boundary.build_safe_boundary_report()
        topics = {item["term"]: item for item in report["topic_workstreams"]}
        topic = topics["\u9a8c\u6536"]

        self.assertGreaterEqual(topic["count"], safe_boundary.MIN_TOPIC_COUNT)
        self.assertTrue(
            safe_boundary.EXPECTED_TOPIC_ROLES.issubset(
                safe_boundary.topic_sample_roles(topic)
            )
        )

    def test_build_safe_boundary_report_passes_for_current_stock_system(self):
        report = safe_boundary.build_safe_boundary_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["owner_lane"], "safe_boundary")
        self.assertGreaterEqual(report["lane"]["precondition_count"], 2)

    def test_validate_report_requires_safe_duplicate(self):
        report = safe_boundary.build_safe_boundary_report()
        report["duplicate_workstreams"] = []

        problems = safe_boundary.validate_report(report)

        self.assertIn("missing_safe_duplicate:243", problems)

    def test_render_markdown_contains_safe_boundary_sections(self):
        report = safe_boundary.build_safe_boundary_report()
        markdown = safe_boundary.render_markdown(report)

        self.assertIn("Stock Safe Boundary Closure", markdown)
        self.assertIn("Duplicate Workstreams", markdown)
        self.assertIn("no_auto_trade_or_broker_interface", markdown)


if __name__ == "__main__":
    unittest.main()
