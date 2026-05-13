import unittest

import ci.stock_closure_panel_ci_check as panel


class StockClosurePanelCiCheckTests(unittest.TestCase):
    def test_summarize_lanes_groups_queue_by_owner(self):
        index = {
            "next_queue": [
                {
                    "kind": "duplicate_number",
                    "target": "149",
                    "action": "keep_parent_index_and_link_related_artifacts",
                    "owner_lane": "quality_evidence",
                },
                {
                    "kind": "semantic_overlap",
                    "target": "人工核验",
                    "action": "build_topic_parent_index_before_merging",
                    "owner_lane": "manual_review",
                },
            ],
            "duplicate_index": [
                {
                    "number": "149",
                    "merge_preconditions": ["link_financial_review_outputs_to_existing_index"],
                }
            ],
        }
        lanes = panel.summarize_lanes(index)
        quality = next(item for item in lanes if item["owner_lane"] == "quality_evidence")
        manual = next(item for item in lanes if item["owner_lane"] == "manual_review")

        self.assertEqual(quality["queue_count"], 1)
        self.assertEqual(quality["precondition_count"], 1)
        self.assertEqual(manual["topic_count"], 1)

    def test_validate_panel_requires_owner_lane(self):
        index = {
            "blocking_problems": [],
            "next_queue": [{"kind": "duplicate_number", "target": "149", "action": "demo"}],
            "duplicate_index": [{"number": "149", "merge_preconditions": ["demo"]}],
        }
        problems = panel.validate_panel(index, [panel.empty_lane_summary("sample_pool")])

        self.assertIn("missing_owner_lane:duplicate_number:149", problems)

    def test_validate_panel_requires_duplicate_preconditions(self):
        index = {
            "blocking_problems": [],
            "next_queue": [
                {
                    "kind": "duplicate_number",
                    "target": "149",
                    "action": "demo",
                    "owner_lane": "quality_evidence",
                }
            ],
            "duplicate_index": [{"number": "149", "merge_preconditions": []}],
        }
        problems = panel.validate_panel(index, [panel.empty_lane_summary("quality_evidence")])

        self.assertIn("missing_merge_preconditions:149", problems)

    def test_build_closure_panel_passes_for_current_stock_system(self):
        current_panel = panel.build_closure_panel()

        self.assertEqual(current_panel["ci_gate_status"], "pass")
        self.assertGreater(current_panel["total_queue_count"], 0)
        self.assertTrue(any(item["owner_lane"] == "quality_evidence" for item in current_panel["lanes"]))

    def test_render_markdown_contains_lane_queue_and_guardrails(self):
        current_panel = panel.build_closure_panel()
        markdown = panel.render_markdown(current_panel)

        self.assertIn("Lane Queue", markdown)
        self.assertIn("Guardrails", markdown)
        self.assertIn("no_real_send_or_n8n_or_webhook", markdown)


if __name__ == "__main__":
    unittest.main()
