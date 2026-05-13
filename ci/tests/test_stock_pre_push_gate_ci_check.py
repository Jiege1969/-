import unittest

import ci.stock_pre_push_gate_ci_check as pre_push


class StockPrePushGateCiCheckTests(unittest.TestCase):
    def test_pre_push_topic_workstreams_include_expected_targets(self):
        report = pre_push.build_pre_push_gate_report()
        targets = {item["term"] for item in report["topic_workstreams"]}

        self.assertTrue(pre_push.EXPECTED_TOPIC_TARGETS.issubset(targets))

    def test_pre_push_topic_has_expected_sample_roles(self):
        report = pre_push.build_pre_push_gate_report()
        topic = next(item for item in report["topic_workstreams"] if item["term"] == "推送")

        self.assertTrue(pre_push.EXPECTED_SAMPLE_ROLES.issubset(pre_push.topic_sample_roles(topic)))

    def test_pre_push_topic_has_required_safety_terms(self):
        report = pre_push.build_pre_push_gate_report()
        topic = next(item for item in report["topic_workstreams"] if item["term"] == "推送")
        names = pre_push.topic_sample_names(topic)

        for required in pre_push.REQUIRED_SAMPLE_TERMS:
            self.assertTrue(any(required in name for name in names))

    def test_build_pre_push_gate_report_passes_for_current_stock_system(self):
        report = pre_push.build_pre_push_gate_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["owner_lane"], "pre_push_gate")
        self.assertGreaterEqual(report["topic_workstreams"][0]["count"], pre_push.MIN_TOPIC_COUNT)

    def test_validate_report_requires_pre_push_topic(self):
        report = pre_push.build_pre_push_gate_report()
        report["topic_workstreams"] = []

        problems = pre_push.validate_report(report)

        self.assertIn("missing_pre_push_topic:推送", problems)

    def test_render_markdown_contains_pre_push_sections(self):
        report = pre_push.build_pre_push_gate_report()
        markdown = pre_push.render_markdown(report)

        self.assertIn("Stock Pre-Push Gate Closure", markdown)
        self.assertIn("Topic Workstreams", markdown)
        self.assertIn("no_real_send_or_n8n_or_webhook", markdown)


if __name__ == "__main__":
    unittest.main()
