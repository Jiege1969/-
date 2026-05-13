import unittest

import ci.stock_consolidation_index_ci_check as consolidation


class StockConsolidationIndexCiCheckTests(unittest.TestCase):
    def test_classify_directory_name_finds_parent_index(self):
        self.assertEqual(
            consolidation.classify_directory_name("149金融专项复核索引"),
            "parent_or_index_candidate",
        )

    def test_classify_directory_name_finds_execution_artifact(self):
        self.assertEqual(
            consolidation.classify_directory_name("195证据核验正式导入执行"),
            "execution_artifact",
        )

    def test_choose_duplicate_action_prefers_existing_index(self):
        roles = consolidation.directory_roles(["149金融专项复核", "149金融专项复核索引"])
        self.assertEqual(
            consolidation.choose_duplicate_action(roles),
            "keep_parent_index_and_link_related_artifacts",
        )

    def test_build_duplicate_index_adds_actions(self):
        maturity_report = {
            "duplicate_number_candidates": [
                {
                    "number": "149",
                    "count": 2,
                    "directories": ["149金融专项复核", "149金融专项复核索引"],
                }
            ]
        }
        index = consolidation.build_duplicate_index(maturity_report)

        self.assertEqual(index[0]["number"], "149")
        self.assertEqual(index[0]["action"], "keep_parent_index_and_link_related_artifacts")

    def test_build_consolidation_index_passes_for_current_stock_system(self):
        index = consolidation.build_consolidation_index()

        self.assertEqual(index["ci_gate_status"], "pass")
        self.assertTrue(index["next_queue"])
        self.assertIn("duplicate_index", index)
        self.assertIn("topic_index", index)

    def test_render_markdown_contains_queue_and_indexes(self):
        index = consolidation.build_consolidation_index()
        markdown = consolidation.render_markdown(index)

        self.assertIn("Next Queue", markdown)
        self.assertIn("Duplicate Number Index", markdown)
        self.assertIn("Topic Index", markdown)


if __name__ == "__main__":
    unittest.main()
