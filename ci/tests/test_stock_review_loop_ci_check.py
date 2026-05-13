import unittest

import ci.stock_review_loop_ci_check as review


class StockReviewLoopCiCheckTests(unittest.TestCase):
    def test_review_topic_workstreams_include_expected_targets(self):
        report = review.build_review_loop_report()
        targets = {item["term"] for item in report["topic_workstreams"]}

        self.assertTrue(review.EXPECTED_TOPIC_TARGETS.issubset(targets))

    def test_review_topic_has_expected_sample_roles(self):
        report = review.build_review_loop_report()
        topic = next(item for item in report["topic_workstreams"] if item["term"] == "复盘")

        self.assertTrue(review.EXPECTED_SAMPLE_ROLES.issubset(review.topic_sample_roles(topic)))

    def test_review_topic_has_required_loop_terms(self):
        report = review.build_review_loop_report()
        topic = next(item for item in report["topic_workstreams"] if item["term"] == "复盘")
        names = review.topic_sample_names(topic)

        for required in review.REQUIRED_SAMPLE_TERMS:
            self.assertTrue(any(required in name for name in names))

    def test_build_review_loop_report_passes_for_current_stock_system(self):
        report = review.build_review_loop_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["owner_lane"], "review_loop")
        self.assertGreaterEqual(report["topic_workstreams"][0]["count"], review.MIN_TOPIC_COUNT)

    def test_validate_report_requires_review_topic(self):
        report = review.build_review_loop_report()
        report["topic_workstreams"] = []

        problems = review.validate_report(report)

        self.assertIn("missing_review_topic:复盘", problems)

    def test_render_markdown_contains_review_sections(self):
        report = review.build_review_loop_report()
        markdown = review.render_markdown(report)

        self.assertIn("Stock Review Loop Closure", markdown)
        self.assertIn("Topic Workstreams", markdown)
        self.assertIn("no_real_send_or_n8n_or_webhook", markdown)


if __name__ == "__main__":
    unittest.main()
