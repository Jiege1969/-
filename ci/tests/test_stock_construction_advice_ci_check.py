import unittest

import ci.stock_construction_advice_ci_check as advice


class StockConstructionAdviceCiCheckTests(unittest.TestCase):
    def test_lane_work_orders_cover_learning_items(self):
        learning_report = advice.learning.build_learning_summary_report()

        orders = advice.lane_work_orders(learning_report)

        self.assertEqual(len(orders), len(learning_report["contract_learning_items"]))
        self.assertTrue(all(order["decision"] for order in orders))

    def test_advice_cards_translate_next_focus(self):
        learning_report = {
            "next_focus": [
                {
                    "priority": "P1",
                    "focus": "ci_contract_layer",
                    "action": "keep_contract_tests_aligned_with_stock_system_reality",
                }
            ]
        }

        cards = advice.advice_cards(learning_report)

        self.assertEqual(cards[0]["mode"], "review_then_continue")
        self.assertEqual(cards[0]["allowed_scope"], "code_tests_docs_ci_only")

    def test_validate_report_rejects_forbidden_advice_term(self):
        report = advice.build_construction_advice_report()
        report["advice_cards"][0]["action"] = "run_n8n"

        problems = advice.validate_report(report)

        self.assertTrue(any(problem.startswith("forbidden_advice_term:run_n8n") for problem in problems))

    def test_build_construction_advice_report_passes_for_current_head(self):
        report = advice.build_construction_advice_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["scope"], "stock_analysis_sample_room")
        self.assertTrue(report["lane_work_orders"])
        self.assertTrue(report["advice_cards"])

    def test_render_markdown_contains_construction_sections(self):
        report = advice.build_construction_advice_report()
        markdown = advice.render_markdown(report)

        self.assertIn("Stock Construction Advice", markdown)
        self.assertIn("Lane Work Orders", markdown)
        self.assertIn("Advice Cards", markdown)


if __name__ == "__main__":
    unittest.main()
