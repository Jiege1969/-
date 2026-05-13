import unittest

import ci.stock_manual_review_ci_check as manual


class StockManualReviewCiCheckTests(unittest.TestCase):
    def test_manual_topic_workstreams_include_expected_targets(self):
        report = manual.build_manual_review_report()
        targets = {item["term"] for item in report["topic_workstreams"]}

        self.assertTrue(manual.EXPECTED_TOPIC_TARGETS.issubset(targets))

    def test_manual_topic_has_expected_sample_roles(self):
        report = manual.build_manual_review_report()
        topic = next(item for item in report["topic_workstreams"] if item["term"] == "人工核验")

        self.assertTrue(manual.EXPECTED_SAMPLE_ROLES.issubset(manual.topic_sample_roles(topic)))

    def test_build_manual_review_report_passes_for_current_stock_system(self):
        report = manual.build_manual_review_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["owner_lane"], "manual_review")
        self.assertGreaterEqual(report["topic_workstreams"][0]["count"], manual.MIN_TOPIC_COUNT)

    def test_validate_report_requires_manual_topic(self):
        report = manual.build_manual_review_report()
        report["topic_workstreams"] = []

        problems = manual.validate_report(report)

        self.assertIn("missing_manual_topic:人工核验", problems)

    def test_render_markdown_contains_manual_sections(self):
        report = manual.build_manual_review_report()
        markdown = manual.render_markdown(report)

        self.assertIn("Stock Manual Review Closure", markdown)
        self.assertIn("Topic Workstreams", markdown)
        self.assertIn("no_real_send_or_n8n_or_webhook", markdown)


if __name__ == "__main__":
    unittest.main()
