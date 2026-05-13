import unittest

import ci.construction_assistant_report as report


class ConstructionAssistantReportTests(unittest.TestCase):
    def test_parse_status_short_categorizes_ci_change(self):
        changes = report.parse_status_short(" M ci/safe_ci_check.py\n")
        self.assertEqual(changes[0].category, "construction_support")

    def test_parse_status_short_categorizes_circleci_change(self):
        changes = report.parse_status_short(" M .circleci/config.yml\n")
        self.assertEqual(changes[0].category, "construction_support")

    def test_parse_status_short_categorizes_runtime_status_change(self):
        changes = report.parse_status_short(" M 00杰哥系统总管/03数据/运行状态/example.json\n")
        self.assertEqual(changes[0].category, "runtime_status")

    def test_recommendation_avoids_runtime_status_files(self):
        changes = report.parse_status_short(" M 00杰哥系统总管/03数据/运行状态/example.json\n")
        self.assertEqual(
            report.recommend_next_step(changes),
            "continue_low_risk_construction_without_touching_runtime_status",
        )

    def test_render_markdown_contains_redline_section(self):
        markdown = report.render_markdown(
            {
                "branch": "main",
                "head": "abc",
                "tracked_files": 1,
                "dirty_files": 0,
                "dirty_categories": {},
                "gitlinks": [],
                "key_status_files": [],
                "redline_stop_terms": ["n8n"],
                "recommendation": "continue_low_risk_construction",
            }
        )
        self.assertIn("Redline Stop Terms", markdown)
        self.assertIn("n8n", markdown)

    def test_key_status_paths_include_readonly_status_sources(self):
        self.assertIn("00杰哥系统总管/07文档/当前施工面板.md", report.KEY_STATUS_PATHS)
        self.assertIn(
            "00杰哥系统总管/03数据/运行状态/全系统只读总检与设计纲领对齐审计_最新.json",
            report.KEY_STATUS_PATHS,
        )


if __name__ == "__main__":
    unittest.main()
