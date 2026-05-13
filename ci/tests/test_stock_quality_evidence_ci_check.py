import unittest

import ci.stock_quality_evidence_ci_check as quality


class StockQualityEvidenceCiCheckTests(unittest.TestCase):
    def test_quality_duplicate_workstreams_include_expected_targets(self):
        report = quality.build_quality_evidence_report()
        targets = {item["number"] for item in report["duplicate_workstreams"]}

        self.assertTrue(quality.EXPECTED_DUPLICATE_TARGETS.issubset(targets))

    def test_quality_topic_workstreams_include_expected_targets(self):
        report = quality.build_quality_evidence_report()
        targets = {item["term"] for item in report["topic_workstreams"]}

        self.assertTrue(quality.expected_topic_targets().issubset(targets))

    def test_build_quality_evidence_report_passes_for_current_stock_system(self):
        report = quality.build_quality_evidence_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["owner_lane"], "quality_evidence")
        self.assertGreaterEqual(report["lane"]["queue_count"], quality.MIN_NEXT_QUEUE_COUNT)

    def test_validate_report_requires_expected_duplicate(self):
        report = quality.build_quality_evidence_report()
        report["duplicate_workstreams"] = [
            item for item in report["duplicate_workstreams"] if item["number"] != "149"
        ]

        problems = quality.validate_report(report)

        self.assertIn("missing_quality_duplicate:149", problems)

    def test_render_markdown_contains_quality_sections(self):
        report = quality.build_quality_evidence_report()
        markdown = quality.render_markdown(report)

        self.assertIn("Stock Quality Evidence Closure", markdown)
        self.assertIn("Duplicate Workstreams", markdown)
        self.assertIn("Topic Workstreams", markdown)
        self.assertIn("no_real_send_or_n8n_or_webhook", markdown)


if __name__ == "__main__":
    unittest.main()
