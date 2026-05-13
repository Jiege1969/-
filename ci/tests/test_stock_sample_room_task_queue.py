import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf"
    / "01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf"
    / "02\u811a\u672c"
    / "stock_sample_room_task_queue.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("stock_sample_room_task_queue", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StockSampleRoomTaskQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_build_task_queue_covers_ordered_lanes(self):
        report = self.module.build_task_queue()

        self.assertEqual(report["queue_state"], "ready")
        self.assertEqual([task["lane"] for task in report["tasks"]], self.module.QUEUE_ORDER)
        self.assertEqual(report["task_count"], len(self.module.QUEUE_ORDER))

    def test_tasks_keep_safe_scope_and_prohibited_actions(self):
        report = self.module.build_task_queue()

        for task in report["tasks"]:
            self.assertEqual(task["allowed_scope"], self.module.ALLOWED_SCOPE)
            self.assertEqual(task["prohibited_actions"], self.module.PROHIBITED_ACTIONS)

    def test_dependencies_keep_pre_push_behind_review_and_safety(self):
        report = self.module.build_task_queue()
        task_by_lane = {task["lane"]: task for task in report["tasks"]}

        self.assertIn("manual_review", task_by_lane["pre_push_gate"]["dependencies"])
        self.assertIn("safe_boundary", task_by_lane["pre_push_gate"]["dependencies"])
        self.assertEqual(task_by_lane["safe_boundary"]["dependencies"], [])

    def test_acceptance_checks_reuse_existing_ci_gates(self):
        report = self.module.build_task_queue()

        checks = {task["acceptance_check"] for task in report["tasks"]}
        self.assertIn("python ci/stock_safe_boundary_ci_check.py", checks)
        self.assertIn("python ci/stock_review_loop_ci_check.py", checks)
        self.assertTrue(all(check.startswith("python ci/stock_") for check in checks))

    def test_validate_queue_rejects_enabled_safety_flag(self):
        report = self.module.build_task_queue()
        report["safety_flags"] = dict(report["safety_flags"])
        report["safety_flags"]["webhook"] = True

        self.assertIn("safety_flag_enabled", self.module.validate_queue(report))

    def test_render_markdown_contains_queue_sections(self):
        report = self.module.build_task_queue()
        markdown = self.module.render_markdown(report)

        self.assertIn("Stock Sample Room Task Queue", markdown)
        self.assertIn("pre_push_gate", markdown)
        self.assertIn("Guardrails", markdown)


if __name__ == "__main__":
    unittest.main()
