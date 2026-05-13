import unittest

import ci.stock_change_impact_ci_check as impact


class StockChangeImpactCiCheckTests(unittest.TestCase):
    def test_path_category_identifies_stock_script(self):
        path = impact.STOCK_PREFIXES[0] + "02鑴氭湰/mainline.py"

        self.assertEqual(impact.path_category(path), "stock_script")

    def test_mainline_script_impacts_all_contract_stages(self):
        path = impact.STOCK_PREFIXES[0] + "02鑴氭湰/" + impact.contract.MAINLINE_SCRIPT_NAME
        expected = {stage["name"] for stage in impact.contract.CONTRACT_STAGES}

        self.assertEqual(set(impact.impacted_stages(path)), expected)

    def test_high_risk_stock_change_requires_safe_boundary_stage(self):
        changes = [
            {
                "status": "M",
                "path": impact.STOCK_PREFIXES[0] + "02鑴氭湰/n8n_dry_run_gate.py",
            }
        ]
        report = impact.build_change_impact_report(changes)

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertIn("safe_boundary", report["changes"][0]["impacted_stages"])

    def test_unmapped_stock_change_is_review_not_blocking(self):
        changes = [
            {
                "status": "M",
                "path": impact.STOCK_PREFIXES[0] + "03鏁版嵁/XYZ_unknown_asset/unknown.json",
            }
        ]
        report = impact.build_change_impact_report(changes)

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertIn("unmapped_stock_change:", report["review_items"][0])

    def test_build_change_impact_report_passes_for_current_head(self):
        report = impact.build_change_impact_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["scope"], "head_commit_only")

    def test_render_markdown_contains_impact_sections(self):
        report = impact.build_change_impact_report(
            [{"status": "M", "path": "ci/stock_change_impact_ci_check.py"}]
        )
        markdown = impact.render_markdown(report)

        self.assertIn("Stock Change Impact", markdown)
        self.assertIn("Changes", markdown)
        self.assertIn("Guardrails", markdown)


if __name__ == "__main__":
    unittest.main()
