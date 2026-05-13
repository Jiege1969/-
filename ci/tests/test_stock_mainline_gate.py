import importlib.util
import unittest
from pathlib import Path

import ci.construction_assistant_report as construction_report


def load_mainline_module():
    gate = next(
        item
        for item in construction_report.STOCK_GATE_PATHS
        if item["name"] == "stock_mainline_gate"
    )
    path = construction_report.ROOT / gate["path"]
    spec = importlib.util.spec_from_file_location("stock_mainline_gate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StockMainlineGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mainline = load_mainline_module()

    def test_build_report_includes_construction_queue(self):
        report = self.mainline.build_report()

        self.assertIn("construction_queue", report)
        self.assertEqual(len(report["construction_queue"]), len(report["主线泳道"]))

    def test_construction_queue_items_have_next_action_fields(self):
        report = self.mainline.build_report()
        item = report["construction_queue"][0]

        self.assertIn("priority", item)
        self.assertIn("lane", item)
        self.assertIn("blocking_reason", item)
        self.assertIn("expected_next", item)

    def test_construction_queue_prioritizes_blocked_lanes(self):
        lanes = [
            {
                "name": "ready lane",
                "status": "pass",
                "expected_next": "continue",
                "assets": [],
                "missing_count": 0,
                "review_count": 0,
                "redline_hit_count": 0,
                "redline_hits": [],
            },
            {
                "name": "blocked lane",
                "status": "fail",
                "expected_next": "fix",
                "assets": [{"path": "missing.json", "status": "missing"}],
                "missing_count": 1,
                "review_count": 0,
                "redline_hit_count": 0,
                "redline_hits": [],
            },
        ]

        queue = self.mainline.build_construction_queue(lanes)

        self.assertEqual(queue[0]["lane"], "blocked lane")
        self.assertEqual(queue[0]["blocking_reason"], "missing_asset")

    def test_render_markdown_contains_construction_queue(self):
        report = self.mainline.build_report()
        markdown = self.mainline.render_markdown(report)

        self.assertIn("Construction Queue", markdown)
        self.assertIn("blocking_reason", str(report["construction_queue"][0]))


if __name__ == "__main__":
    unittest.main()
