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
                "cloud_ci_boundary": "CircleCI only guards repository commits",
                "integration_principle": "reuse existing local mechanisms before adding new ones",
                "local_workflow_mechanisms": [],
                "stock_gate_status": [],
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

    def test_local_workflow_mechanisms_prefer_reuse(self):
        mechanisms = report.local_workflow_mechanism_status()
        self.assertTrue(mechanisms)
        self.assertTrue(any(item["circleci_logic"] == "trigger" for item in mechanisms))
        self.assertTrue(any(item["action"] == "reuse_existing" for item in mechanisms))

    def test_stock_gate_status_includes_sample_room_and_mainline(self):
        gates = report.stock_gate_status()
        names = {item["name"] for item in gates}

        self.assertIn("stock_sample_room_gate", names)
        self.assertIn("stock_mainline_gate", names)
        self.assertIn("stock_maturity_ci_checker", names)
        self.assertIn("stock_consolidation_index_ci_checker", names)
        self.assertIn("stock_closure_panel_ci_checker", names)
        self.assertIn("stock_quality_evidence_ci_checker", names)
        self.assertIn("stock_sample_pool_ci_checker", names)
        self.assertIn("stock_manual_review_ci_checker", names)
        self.assertIn("stock_pre_push_gate_ci_checker", names)
        self.assertIn("stock_review_loop_ci_checker", names)
        self.assertIn("stock_safe_boundary_ci_checker", names)
        self.assertIn("stock_system_contract_ci_checker", names)
        self.assertIn("stock_change_impact_ci_checker", names)
        self.assertIn("stock_ci_learning_summary", names)
        self.assertTrue(any(item["action"] == "ci_guarded" for item in gates))

    def test_render_markdown_contains_local_absorption_section(self):
        report_data = {
            "branch": "main",
            "head": "abc",
            "tracked_files": 1,
            "dirty_files": 0,
            "dirty_categories": {},
            "gitlinks": [],
            "key_status_files": [],
            "redline_stop_terms": [],
            "cloud_ci_boundary": "CircleCI only guards repository commits",
            "integration_principle": "reuse existing local mechanisms before adding new ones",
            "local_workflow_mechanisms": [
                {
                    "circleci_logic": "trigger",
                    "local_mechanism": "开工触发和施工面板",
                    "path": "00杰哥系统总管/07文档/当前施工面板.md",
                    "reuse_rule": "复用现有施工面板，不新增平行入口。",
                    "exists": True,
                    "action": "reuse_existing",
                }
            ],
            "stock_gate_status": [],
            "recommendation": "continue_low_risk_construction",
        }
        markdown = report.render_markdown(report_data)
        self.assertIn("Local Workflow Absorption", markdown)
        self.assertIn("reuse_existing", markdown)
        self.assertIn("CircleCI only guards repository commits", markdown)

    def test_render_markdown_contains_stock_gate_status(self):
        report_data = {
            "branch": "main",
            "head": "abc",
            "tracked_files": 1,
            "dirty_files": 0,
            "dirty_categories": {},
            "gitlinks": [],
            "key_status_files": [],
            "redline_stop_terms": [],
            "cloud_ci_boundary": "CircleCI only guards repository commits",
            "integration_principle": "reuse existing local mechanisms before adding new ones",
            "local_workflow_mechanisms": [],
            "stock_gate_status": [
                {
                    "name": "stock_mainline_gate",
                    "role": "mainline construction acceptance gate",
                    "path": "02杰哥扩展系统/01股票研究系统/02脚本/生成股票主线施工闸口面板.py",
                    "exists": True,
                    "action": "ci_guarded",
                }
            ],
            "recommendation": "continue_low_risk_construction",
        }
        markdown = report.render_markdown(report_data)
        self.assertIn("Stock Gate Status", markdown)
        self.assertIn("stock_mainline_gate", markdown)
        self.assertIn("ci_guarded", markdown)


if __name__ == "__main__":
    unittest.main()
