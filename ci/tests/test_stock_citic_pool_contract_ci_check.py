import unittest

import ci.stock_citic_pool_contract_ci_check as citic


class StockCiticPoolContractCiCheckTests(unittest.TestCase):
    def test_report_preserves_four_visible_boards(self):
        report = citic.build_report()

        self.assertEqual(report["visible_boards"], citic.VISIBLE_BOARDS)

    def test_system_manages_only_three_result_pools(self):
        report = citic.build_report()

        self.assertEqual(report["system_managed_boards"], citic.SYSTEM_MANAGED_BOARDS)
        self.assertNotIn("杰哥的临时选股", report["system_managed_boards"])

    def test_contract_validation_passes(self):
        report = citic.build_report()
        problems = citic.validate_report(report)

        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
