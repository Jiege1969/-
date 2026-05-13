import unittest

import ci.stock_ci_traceability_ci_check as traceability


class StockCiTraceabilityCiCheckTests(unittest.TestCase):
    def test_stock_circleci_commands_extracts_only_stock_python_commands(self):
        commands = [
            "python --version",
            "python ci/stock_a_ci_check.py",
            "python ci/safe_ci_check.py",
        ]

        self.assertEqual(
            traceability.stock_circleci_commands(commands),
            ["python ci/stock_a_ci_check.py"],
        )

    def test_expected_test_paths_uses_wrapper_evidence_override(self):
        self.assertIn(
            "ci/tests/test_stock_mainline_gate.py",
            traceability.expected_test_paths("ci/stock_mainline_ci_check.py"),
        )

    def test_duplicate_values_reports_duplicates_once(self):
        self.assertEqual(traceability.duplicate_values(["a", "b", "a", "a"]), ["a"])

    def test_traceability_rows_include_current_gate(self):
        rows = traceability.traceability_rows()
        paths = {row["path"] for row in rows}

        self.assertIn("ci/stock_ci_traceability_ci_check.py", paths)

    def test_build_traceability_report_passes_for_current_chain(self):
        report = traceability.build_traceability_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertTrue(report["rows"])
        self.assertTrue(report["order_pairs"])

    def test_validate_report_rejects_missing_test_evidence(self):
        report = traceability.build_traceability_report()
        report["rows"][0]["has_test_evidence"] = False

        problems = traceability.validate_report(report)

        self.assertTrue(any(problem.startswith("stock_ci_file_without_test_evidence:") for problem in problems))

    def test_render_markdown_contains_traceability_sections(self):
        report = traceability.build_traceability_report()
        markdown = traceability.render_markdown(report)

        self.assertIn("Stock CI Traceability", markdown)
        self.assertIn("Rows", markdown)
        self.assertIn("Order", markdown)


if __name__ == "__main__":
    unittest.main()
