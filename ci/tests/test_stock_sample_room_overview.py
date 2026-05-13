import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf"
    / "01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf"
    / "02\u811a\u672c"
    / "stock_sample_room_overview.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("stock_sample_room_overview", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StockSampleRoomOverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_build_overview_covers_six_lanes(self):
        report = self.module.build_overview()

        self.assertEqual(report["lane_count"], 6)
        self.assertEqual({lane["name"] for lane in report["lanes"]}, {lane["name"] for lane in self.module.LANES})

    def test_build_overview_keeps_safety_flags_disabled(self):
        report = self.module.build_overview()

        self.assertTrue(all(value is False for value in report["safety_flags"].values()))
        self.assertNotEqual(report["overview_state"], "blocked")

    def test_lane_evidence_reports_counts(self):
        report = self.module.build_overview()

        self.assertTrue(all("evidence_count" in lane for lane in report["lanes"]))
        self.assertTrue(any(lane["evidence_count"] > 0 for lane in report["lanes"]))

    def test_render_markdown_contains_core_sections(self):
        report = self.module.build_overview()
        markdown = self.module.render_markdown(report)

        self.assertIn("Stock Sample Room Overview", markdown)
        self.assertIn("Safety Flags", markdown)
        self.assertIn("sample_pool", markdown)

    def test_write_outputs_uses_explicit_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "03data").mkdir()
            report = {
                "generated_at": "2026-01-01 00:00:00",
                "overview_state": "continue",
                "lane_count": 0,
                "lanes": [],
                "safety_flags": {},
                "guardrails": [],
            }

            outputs = self.module.write_outputs(report, root=root)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())


if __name__ == "__main__":
    unittest.main()
