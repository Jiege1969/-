import unittest

import ci.stock_risk_matrix_ci_check as risk


class StockRiskMatrixCiCheckTests(unittest.TestCase):
    def test_risk_level_for_high_risk_marker_is_high(self):
        change = {
            "category": "stock_doc",
            "impacted_stages": [],
            "high_risk_marker": True,
        }

        self.assertEqual(risk.risk_level_for_change(change), "high")

    def test_required_gates_include_impacted_stage(self):
        change = {
            "category": "stock_doc",
            "impacted_stages": ["sample_pool"],
            "high_risk_marker": False,
        }

        self.assertIn("sample_pool", risk.required_gates_for_change(change))

    def test_gate_statuses_include_focused_lanes(self):
        impact_report = {
            "ci_gate_status": "pass",
            "system_contract": {
                "ci_gate_status": "pass",
                "focused_gate_statuses": {"sample_pool": "pass"},
            },
        }
        dependency_report = {"ci_gate_status": "pass"}

        self.assertEqual(
            risk.gate_statuses(impact_report, dependency_report)["sample_pool"],
            "pass",
        )

    def test_validate_report_rejects_missing_required_gate(self):
        report = {
            "upstream": {
                "change_impact_status": "pass",
                "dependency_order_status": "pass",
            },
            "rows": [
                {
                    "path": "x",
                    "risk_level": "medium",
                    "missing_or_failed_gates": ["sample_pool"],
                    "safe_boundary_required": False,
                    "safe_boundary_present": True,
                    "high_risk_marker": False,
                }
            ],
            "guardrails": risk.GUARDRAILS,
        }

        problems = risk.validate_report(report)

        self.assertIn("risk_required_gate_not_pass:x:sample_pool", problems)

    def test_build_risk_matrix_report_passes_for_current_head(self):
        report = risk.build_risk_matrix_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["upstream"]["change_impact_status"], "pass")
        self.assertEqual(report["upstream"]["dependency_order_status"], "pass")

    def test_render_markdown_contains_risk_sections(self):
        report = risk.build_risk_matrix_report()
        markdown = risk.render_markdown(report)

        self.assertIn("Stock Risk Matrix", markdown)
        self.assertIn("Risk Counts", markdown)
        self.assertIn("Rows", markdown)


if __name__ == "__main__":
    unittest.main()
