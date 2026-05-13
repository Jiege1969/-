import unittest

import ci.stock_ci_learning_summary as learning


class StockCiLearningSummaryTests(unittest.TestCase):
    def test_impacted_stage_counts_counts_all_stages(self):
        changes = [
            {"impacted_stages": ["sample_pool", "safe_boundary"]},
            {"impacted_stages": ["sample_pool"]},
        ]

        self.assertEqual(
            learning.impacted_stage_counts(changes),
            {"sample_pool": 2, "safe_boundary": 1},
        )

    def test_contract_learning_items_cover_all_contract_stages(self):
        report = learning.contract.build_system_contract_report()
        items = learning.contract_learning_items(report)

        self.assertEqual(len(items), len(learning.contract.CONTRACT_STAGES))
        self.assertTrue(all(item["learning"] == "contract_lane_understood" for item in items))

    def test_next_focus_prefers_blocking_contract_problem(self):
        contract_report = {"blocking_problems": ["x"]}
        impact_report = {"blocking_problems": [], "review_items": [], "changes": []}

        focus = learning.next_focus_items(contract_report, impact_report)

        self.assertEqual(focus[0]["priority"], "P0")
        self.assertEqual(focus[0]["focus"], "contract_blocking_problems")

    def test_build_learning_summary_report_passes_for_current_head(self):
        report = learning.build_learning_summary_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["scope"], "stock_analysis_sample_room")

    def test_validate_report_requires_next_focus(self):
        report = learning.build_learning_summary_report()
        report["next_focus"] = []

        problems = learning.validate_report(report)

        self.assertIn("missing_next_focus", problems)

    def test_render_markdown_contains_learning_sections(self):
        report = learning.build_learning_summary_report()
        markdown = learning.render_markdown(report)

        self.assertIn("Stock CI Learning Summary", markdown)
        self.assertIn("Learned Contract Lanes", markdown)
        self.assertIn("Next Focus", markdown)


if __name__ == "__main__":
    unittest.main()
