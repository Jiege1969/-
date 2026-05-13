import unittest

import ci.stock_dependency_order_ci_check as dependency


class StockDependencyOrderCiCheckTests(unittest.TestCase):
    def test_required_chain_edges_follow_stage_sequence(self):
        self.assertEqual(
            dependency.required_chain_edges()[0],
            ("sample_pool", "manual_review"),
        )
        self.assertEqual(
            dependency.required_chain_edges()[-1],
            ("pre_push_gate", "review_loop"),
        )

    def test_required_safe_edges_cover_all_construction_stages(self):
        edges = dependency.required_safe_edges()

        self.assertEqual(len(edges), len(dependency.CONSTRUCTION_STAGE_SEQUENCE))
        self.assertTrue(all(source == dependency.SAFE_STAGE for source, _target in edges))

    def test_topological_order_detects_cycle(self):
        graph = {"a": ["b"], "b": ["a"]}

        self.assertTrue(dependency.has_cycle(graph))

    def test_build_dependency_order_report_passes_for_current_contract(self):
        report = dependency.build_dependency_order_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertFalse(report["graph_has_cycle"])
        self.assertEqual(report["system_contract_status"], "pass")
        self.assertEqual(report["traceability_status"], "pass")

    def test_validate_report_requires_safe_boundary_edge(self):
        report = dependency.build_dependency_order_report()
        report["edge_pairs"] = [
            edge
            for edge in report["edge_pairs"]
            if edge != ["safe_boundary", "sample_pool"]
        ]

        problems = dependency.validate_report(report)

        self.assertIn("missing_safe_boundary_edge:safe_boundary->sample_pool", problems)

    def test_validate_report_requires_meta_ci_order(self):
        report = dependency.build_dependency_order_report()
        before, after = dependency.META_CI_ORDER[0], dependency.META_CI_ORDER[1]
        report["ci_positions"][before], report["ci_positions"][after] = (
            report["ci_positions"][after],
            report["ci_positions"][before],
        )

        problems = dependency.validate_report(report)

        self.assertIn(f"meta_ci_order_violation:{before}->{after}", problems)

    def test_render_markdown_contains_dependency_sections(self):
        report = dependency.build_dependency_order_report()
        markdown = dependency.render_markdown(report)

        self.assertIn("Stock Dependency Order", markdown)
        self.assertIn("Required Chain Edges", markdown)
        self.assertIn("Safe Boundary Edges", markdown)


if __name__ == "__main__":
    unittest.main()
