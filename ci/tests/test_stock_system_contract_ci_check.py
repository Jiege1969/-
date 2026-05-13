import unittest

import ci.stock_system_contract_ci_check as contract


class StockSystemContractCiCheckTests(unittest.TestCase):
    def test_stage_contracts_have_source_documents(self):
        report = contract.build_system_contract_report()

        for stage in report["stages"]:
            self.assertGreaterEqual(stage["doc_count"], 1, stage["name"])

    def test_focused_gates_pass_for_all_contract_lanes(self):
        report = contract.build_system_contract_report()

        self.assertEqual(set(report["focused_gate_statuses"]), {stage["name"] for stage in report["stages"]})
        self.assertTrue(all(status == "pass" for status in report["focused_gate_statuses"].values()))

    def test_mainline_contract_includes_construction_queue_and_safety_false(self):
        report = contract.build_system_contract_report()
        mainline = report["mainline_contract"]

        self.assertEqual(mainline["ci_gate_status"], "pass")
        self.assertGreaterEqual(mainline["construction_queue_count"], mainline["lane_count"])
        self.assertTrue(all(mainline["safety_false_keys"].values()))

    def test_dependency_edges_have_known_contract_stages(self):
        report = contract.build_system_contract_report()
        stage_names = {stage["name"] for stage in report["stages"]}

        for source, target, _label in report["dependency_edges"]:
            self.assertIn(source, stage_names)
            self.assertIn(target, stage_names)

    def test_build_system_contract_report_passes_for_current_stock_system(self):
        report = contract.build_system_contract_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertEqual(report["scope"], "stock_analysis_sample_room")

    def test_validate_report_requires_stage_source_document(self):
        report = contract.build_system_contract_report()
        report["stages"][0]["doc_count"] = 0

        problems = contract.validate_report(report)

        self.assertIn(f"missing_stage_source_doc:{report['stages'][0]['name']}", problems)

    def test_render_markdown_contains_contract_sections(self):
        report = contract.build_system_contract_report()
        markdown = contract.render_markdown(report)

        self.assertIn("Stock System Contract", markdown)
        self.assertIn("Dependency Edges", markdown)
        self.assertIn("Focused Gates", markdown)


if __name__ == "__main__":
    unittest.main()
