import unittest

import ci.stock_runtime_artifact_governance_ci_check as governance


class StockRuntimeArtifactGovernanceTests(unittest.TestCase):
    def test_classify_live_runtime_status_files(self):
        for path in governance.LIVE_RUNTIME_STATUS_FILES:
            self.assertEqual(governance.classify_path(path), "live_runtime_status")

    def test_classify_stock_latest_and_dated_evidence(self):
        latest = (
            "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf/01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf/"
            "03\u6570\u636e/280\u6770\u54e5\u63a8\u8350\u5206\u6790\u65b9\u6cd5v1/"
            "\u6770\u54e5\u63a8\u8350\u5206\u6790\u65b9\u6cd5v1\u62a5\u544a_\u6700\u65b0.json"
        )
        dated = latest.replace("_\u6700\u65b0.json", "_20260513_210537.json")

        self.assertEqual(governance.classify_path(latest), "latest_stock_evidence")
        self.assertEqual(governance.classify_path(dated), "dated_stock_evidence")

    def test_build_report_passes_for_current_repository(self):
        report = governance.build_runtime_artifact_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertGreater(report["category_counts"].get("latest_stock_evidence", 0), 0)
        self.assertGreater(report["category_counts"].get("dated_stock_evidence", 0), 0)

    def test_build_report_accepts_local_skip_worktree_markers(self):
        paths = list(governance.LIVE_RUNTIME_STATUS_FILES)
        paths.append(
            "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf/01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf/"
            "03\u6570\u636e/01\u80a1\u7968\u6c60/\u5168A\u57fa\u7840\u80a1\u7968\u6c60_\u6700\u65b0.json"
        )
        paths.append(
            "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf/01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf/"
            "03\u6570\u636e/01\u80a1\u7968\u6c60/\u5168A\u57fa\u7840\u80a1\u7968\u6c60_20260513_153028.json"
        )

        report = governance.build_runtime_artifact_report(paths=paths, skip_paths={paths[0]})

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertTrue(report["live_runtime_status_files"][0]["local_skip_worktree"])

    def test_validate_report_rejects_missing_live_status(self):
        paths = [
            "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf/01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf/"
            "03\u6570\u636e/01\u80a1\u7968\u6c60/\u5168A\u57fa\u7840\u80a1\u7968\u6c60_\u6700\u65b0.json",
            "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf/01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf/"
            "03\u6570\u636e/01\u80a1\u7968\u6c60/\u5168A\u57fa\u7840\u80a1\u7968\u6c60_20260513_153028.json",
        ]

        report = governance.build_runtime_artifact_report(paths=paths, skip_paths=set())

        self.assertEqual(report["ci_gate_status"], "fail")
        self.assertTrue(
            any(problem.startswith("live_runtime_status_not_tracked") for problem in report["blocking_problems"])
        )

    def test_render_markdown_contains_governance_sections(self):
        report = governance.build_runtime_artifact_report()
        markdown = governance.render_markdown(report)

        self.assertIn("Stock Runtime Artifact Governance", markdown)
        self.assertIn("Live Runtime Status Files", markdown)
        self.assertIn("Recommendations", markdown)


if __name__ == "__main__":
    unittest.main()
