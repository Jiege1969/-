import unittest

import ci.stock_frontend_message_contract_ci_check as frontend_contract


class StockFrontendMessageContractCiCheckTests(unittest.TestCase):
    def test_build_report_passes_for_current_contract(self):
        report = frontend_contract.build_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["contract_version"], "v1.0")
        self.assertTrue(report["strong_focus"]["uses_star_expression"])
        self.assertTrue(report["method_kernel_over_template"])

    def test_numeric_requirements_cover_computed_conditions(self):
        report = frontend_contract.build_report()

        self.assertTrue(report["numeric_output_coverage"]["最近5日平均成交量"])
        self.assertTrue(report["numeric_output_coverage"]["放量达标线"])
        self.assertTrue(report["numeric_output_coverage"]["风险线"])
        self.assertTrue(report["numeric_output_coverage"]["连续入选天数"])

    def test_message_types_cover_two_robot_frontends(self):
        report = frontend_contract.build_report()

        self.assertTrue(report["message_type_coverage"]["单股主动询问"])
        self.assertTrue(report["message_type_coverage"]["短线主动推送"])
        self.assertTrue(report["message_type_coverage"]["专家主动推送"])
        self.assertTrue(report["bot_coverage"]["杰哥股票短线分析助手"])
        self.assertTrue(report["bot_coverage"]["杰哥股票分析专家"])

    def test_governance_keeps_single_current_rule_source(self):
        report = frontend_contract.build_report()

        self.assertTrue(report["governance"]["single_current_contract"])
        self.assertTrue(report["governance"]["single_current_document"])
        self.assertTrue(report["governance"]["mentions_absorb_replace_or_deprecate"])
        self.assertEqual(report["governance"]["legacy_backup_files"], [])

    def test_validate_report_rejects_missing_star_expression(self):
        report = frontend_contract.build_report()
        report["strong_focus"]["uses_star_expression"] = False

        problems = frontend_contract.validate_report(report)

        self.assertIn("strong_focus_does_not_reuse_star_expression", problems)

    def test_validate_report_rejects_missing_numeric_output(self):
        report = frontend_contract.build_report()
        report["numeric_output_coverage"]["放量达标线"] = False

        problems = frontend_contract.validate_report(report)

        self.assertIn("missing_numeric_output_requirement:放量达标线", problems)

    def test_validate_report_rejects_remaining_legacy_backup(self):
        report = frontend_contract.build_report()
        report["governance"]["legacy_backup_files"] = [
            "02杰哥扩展系统/01股票研究系统/07文档/旧规则.md.before-rename-stock-advisor-20260510-2220"
        ]

        problems = frontend_contract.validate_report(report)

        self.assertIn(
            "legacy_frontend_backup_file_remaining:02杰哥扩展系统/01股票研究系统/07文档/旧规则.md.before-rename-stock-advisor-20260510-2220",
            problems,
        )

    def test_render_markdown_contains_contract_sections(self):
        report = frontend_contract.build_report()
        markdown = frontend_contract.render_markdown(report)

        self.assertIn("Stock Frontend Message Contract", markdown)
        self.assertIn("Message Types", markdown)
        self.assertIn("Computed Conditions", markdown)
        self.assertIn("Legacy Cleanup", markdown)


if __name__ == "__main__":
    unittest.main()
