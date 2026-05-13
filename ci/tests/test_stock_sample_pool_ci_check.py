import unittest

import ci.stock_sample_pool_ci_check as sample_pool


class StockSamplePoolCiCheckTests(unittest.TestCase):
    def test_sample_duplicate_workstreams_include_expected_targets(self):
        report = sample_pool.build_sample_pool_report()
        targets = {item["number"] for item in report["duplicate_workstreams"]}

        self.assertTrue(sample_pool.EXPECTED_DUPLICATE_TARGETS.issubset(targets))

    def test_sample_topic_workstreams_include_expected_targets(self):
        report = sample_pool.build_sample_pool_report()
        targets = {item["term"] for item in report["topic_workstreams"]}

        self.assertTrue(sample_pool.expected_topic_targets().issubset(targets))

    def test_build_sample_pool_report_passes_for_current_stock_system(self):
        report = sample_pool.build_sample_pool_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["owner_lane"], "sample_pool")
        self.assertGreaterEqual(report["lane"]["queue_count"], sample_pool.MIN_PANEL_QUEUE_COUNT)

    def test_validate_report_requires_expected_duplicate(self):
        report = sample_pool.build_sample_pool_report()
        report["duplicate_workstreams"] = [
            item for item in report["duplicate_workstreams"] if item["number"] != "01"
        ]

        problems = sample_pool.validate_report(report)

        self.assertIn("missing_sample_duplicate:01", problems)

    def test_render_markdown_contains_sample_sections(self):
        report = sample_pool.build_sample_pool_report()
        markdown = sample_pool.render_markdown(report)

        self.assertIn("Stock Sample Pool Closure", markdown)
        self.assertIn("Duplicate Workstreams", markdown)
        self.assertIn("Topic Workstreams", markdown)
        self.assertIn("no_real_send_or_n8n_or_webhook", markdown)


if __name__ == "__main__":
    unittest.main()
