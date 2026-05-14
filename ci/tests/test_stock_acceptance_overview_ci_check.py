import unittest
from pathlib import Path

import ci.stock_acceptance_overview_ci_check as overview


class StockAcceptanceOverviewCiCheckTests(unittest.TestCase):
    def test_readiness_score_penalizes_failing_upstream_and_risk(self):
        statuses = {name: "pass" for name in overview.UPSTREAM_WEIGHTS}
        statuses["risk_matrix"] = "fail"

        score = overview.readiness_score(statuses, {"low": 1, "medium": 2, "high": 1})

        self.assertLess(score, 70)

    def test_acceptance_state_blocks_on_failing_upstream(self):
        statuses = {name: "pass" for name in overview.UPSTREAM_WEIGHTS}
        statuses["dependency_order"] = "fail"

        self.assertEqual(
            overview.acceptance_state(95, {"high": 0}, statuses),
            "blocked",
        )

    def test_acceptance_state_requires_human_review_for_high_risk(self):
        statuses = {name: "pass" for name in overview.UPSTREAM_WEIGHTS}

        self.assertEqual(
            overview.acceptance_state(95, {"high": 1}, statuses),
            "human_review_required",
        )

    def test_next_action_for_continue_is_safe_scope(self):
        self.assertEqual(
            overview.next_action_for_state("continue"),
            "continue_stock_system_construction_under_current_ci_gates",
        )

    def test_build_acceptance_overview_report_passes_for_current_head(self):
        report = overview.build_acceptance_overview_report()

        self.assertEqual(report["ci_gate_status"], "pass")
        self.assertIn(report["state"], {"continue", "review_before_continue", "human_review_required", "blocked"})
        self.assertTrue(report["advice_modes"])
        self.assertEqual(report["upstream_statuses"]["runtime_artifact_governance"], "pass")
        self.assertGreaterEqual(report["runtime_artifact_governance"]["live_runtime_status_count"], 1)
        self.assertEqual(report["delivery_truthfulness"]["status"], "pass")
        self.assertEqual(report["wecom_ip_consistency"]["status"], "pass")
        self.assertEqual(report["wecom_status_command"]["status"], "pass")
        self.assertEqual(report["wecom_fixed_public_egress"]["status"], "pass")
        self.assertEqual(report["wecom_legacy_ip_residue"]["status"], "pass")

    def test_delivery_truthfulness_rejects_complete_claim_when_wecom_ip_blocked(self):
        result = overview.delivery_truthfulness_status(
            final_text="结论：完全交付通过\n企业微信真实主动推送通过 | 未通过 | 最新受控发送被可信IP拦截",
            wecom_text="主动推送受可信IP限制",
        )

        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["claims_complete"])
        self.assertTrue(result["active_push_blocked"])

    def test_delivery_truthfulness_allows_incomplete_claim_when_wecom_ip_blocked(self):
        result = overview.delivery_truthfulness_status(
            final_text="结论：未完全交付：仍有外部或本地验收项未通过",
            wecom_text="主动推送受可信IP限制",
        )

        self.assertEqual(result["status"], "pass")

    def test_wecom_status_command_requires_status_help_terms(self):
        result = overview.wecom_status_command_status(
            "状态帮助短答可用\n问答入口：可用\n主动推送：受控白名单可用"
        )

        self.assertEqual(result["status"], "pass")

    def test_wecom_status_command_requires_ip_only_when_push_blocked(self):
        result = overview.wecom_status_command_status(
            "状态帮助短答可用\n问答入口：可用\n主动推送：受可信IP限制\n需放行IP：183.227.145.167"
        )

        self.assertEqual(result["status"], "pass")

    def test_wecom_ip_consistency_rejects_mismatched_current_ips(self):
        result = overview.wecom_ip_consistency_status(
            final_text="当前需放行IP：183.227.145.167",
            wecom_text="需放行IP：183.227.145.167",
            trusted_status={"当前需放行IP": "183.227.144.47"},
            allow_status={"最近企业微信返回": {"识别到的公网IP": "183.227.145.167"}},
        )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["ips"], ["183.227.144.47", "183.227.145.167"])

    def test_wecom_ip_consistency_accepts_current_ip_across_reports(self):
        result = overview.wecom_ip_consistency_status(
            final_text="当前需放行IP：183.227.145.167",
            wecom_text="图形报告：http://43.167.210.211/report.png\n需放行IP：183.227.145.167",
            trusted_status={"当前需放行IP": "183.227.145.167"},
            allow_status={"最近企业微信返回": {"识别到的公网IP": "183.227.145.167"}},
        )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["ips"], ["183.227.145.167"])

    def test_wecom_status_command_rejects_missing_status_help(self):
        result = overview.wecom_status_command_status("短线机器人本地stream回复可用")

        self.assertEqual(result["status"], "fail")
        self.assertIn("状态帮助短答可用", result["missing_terms"])

    def test_wecom_fixed_public_egress_contract_requires_stock_real_send_fixed_mode(self):
        result = overview.wecom_fixed_public_egress_contract_status(
            sender_text="--fixed-public-egress\nsend_message_via_fixed_public_egress",
            stock_gray_text="fixed_public_egress = bool(args.real_send and not args.local_egress)",
            retest_text='send_args = ["--real-send", "--fixed-public-egress"]',
            send_config={"固定公网出口": {"公网IP": "43.167.210.211", "SSH主机": "43.167.210.211"}},
        )

        self.assertEqual(result["status"], "pass")

    def test_wecom_fixed_public_egress_contract_rejects_local_only_real_send(self):
        result = overview.wecom_fixed_public_egress_contract_status(
            sender_text="local sender only",
            stock_gray_text='send_args = ["--real-send"]',
            retest_text='send_args = ["--real-send"]',
            send_config={"固定公网出口": {"公网IP": "183.227.145.167", "SSH主机": "183.227.145.167"}},
        )

        self.assertEqual(result["status"], "fail")
        self.assertIn("common_sender_supports_fixed_mode", result["missing"])
        self.assertIn("stock_real_send_defaults_to_fixed_mode", result["missing"])

    def test_wecom_legacy_ip_residue_rejects_old_broadband_ip(self):
        original_read_text = overview.read_text
        try:
            overview.read_text = lambda path: "企业微信后台加入可信IP 183.227.144.47 后再复测"
            result = overview.wecom_legacy_ip_residue_status(paths=[Path("交付提示.py")])
        finally:
            overview.read_text = original_read_text

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["hits"][0]["needle"], "183.227.")

    def test_wecom_legacy_ip_residue_accepts_fixed_public_ip(self):
        original_read_text = overview.read_text
        try:
            overview.read_text = lambda path: "企业微信后台加入固定公网出口IP 43.167.210.211 后再复测"
            result = overview.wecom_legacy_ip_residue_status(paths=[Path("操作卡.py")])
        finally:
            overview.read_text = original_read_text

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["hits"], [])

    def test_validate_report_rejects_continue_with_high_risk(self):
        report = overview.build_acceptance_overview_report()
        report["state"] = "continue"
        report["risk_counts"]["high"] = 1

        problems = overview.validate_report(report)

        self.assertIn("continue_state_with_high_risk_items", problems)

    def test_render_markdown_contains_overview_sections(self):
        report = overview.build_acceptance_overview_report()
        markdown = overview.render_markdown(report)

        self.assertIn("Stock Acceptance Overview", markdown)
        self.assertIn("Upstream Statuses", markdown)
        self.assertIn("runtime_artifact_governance", markdown)
        self.assertIn("Risk Counts", markdown)
        self.assertIn("WeCom Trusted IP Consistency", markdown)
        self.assertIn("WeCom Status Command", markdown)
        self.assertIn("WeCom Fixed Public Egress", markdown)
        self.assertIn("WeCom Legacy IP Residue", markdown)


if __name__ == "__main__":
    unittest.main()
