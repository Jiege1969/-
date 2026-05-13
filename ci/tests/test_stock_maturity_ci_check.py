import unittest
from pathlib import Path

import ci.stock_maturity_ci_check as maturity


class StockMaturityCiCheckTests(unittest.TestCase):
    def test_leading_code_extracts_numeric_prefix(self):
        self.assertEqual(maturity.leading_code("149金融专项复核"), "149")
        self.assertEqual(maturity.leading_code("130X综合候选池"), "130X")
        self.assertIsNone(maturity.leading_code("股票池"))

    def test_duplicate_number_candidates_groups_same_prefix(self):
        directories = [
            Path("149金融专项复核"),
            Path("149金融专项复核索引"),
            Path("150报告安全边界检查"),
        ]
        candidates = maturity.duplicate_number_candidates(directories)

        self.assertEqual(candidates[0]["number"], "149")
        self.assertEqual(candidates[0]["count"], 2)

    def test_lane_status_reports_review_without_failing_for_missing_term(self):
        lane = {
            "name": "demo",
            "label": "demo",
            "purpose": "demo",
            "required_terms": ["人工核验", "不存在的词"],
            "closure_terms": {
                "input": ["人工核验"],
                "analysis": ["预演"],
            },
        }
        status = maturity.lane_status(
            lane,
            [Path("103人工核验结果填写"), Path("120人工核验批量导入预演")],
        )

        self.assertEqual(status["status"], "review")
        self.assertIn("不存在的词", status["missing_required_terms"])

    def test_build_report_keeps_findings_as_review_items(self):
        report = maturity.build_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertTrue(report["lanes"])
        self.assertIn("duplicate_number_candidates", report)
        self.assertIn("semantic_overlap_candidates", report)

    def test_render_markdown_contains_closure_sections(self):
        report = maturity.build_report()
        markdown = maturity.render_markdown(report)

        self.assertIn("Workflow Closure", markdown)
        self.assertIn("Duplicate Number Candidates", markdown)
        self.assertIn("Semantic Overlap Candidates", markdown)


if __name__ == "__main__":
    unittest.main()
