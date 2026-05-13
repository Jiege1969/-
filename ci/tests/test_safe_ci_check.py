import tempfile
import unittest
from pathlib import Path

import ci.safe_ci_check as safe_ci_check


class SafeCiCheckTests(unittest.TestCase):
    def test_should_compile_includes_regular_python_file(self):
        path = safe_ci_check.ROOT / "ci" / "safe_ci_check.py"
        self.assertTrue(safe_ci_check.should_compile(path))

    def test_should_compile_excludes_backup_and_temp_dirs(self):
        backup_path = safe_ci_check.ROOT / "03杰哥进化系统" / "05备份" / "old.py"
        temp_path = safe_ci_check.ROOT / "02杰哥扩展系统" / "06临时" / "scratch.py"
        self.assertFalse(safe_ci_check.should_compile(backup_path))
        self.assertFalse(safe_ci_check.should_compile(temp_path))

    def test_read_text_safely_ignores_binary_suffix(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.bin"
            path.write_bytes(b"abc")
            self.assertIsNone(safe_ci_check.read_text_safely(path))

    def test_redline_patterns_catch_real_send_true(self):
        text = "REAL" + "_SEND = " + "True"
        self.assertTrue(any(pattern.search(text) for pattern in safe_ci_check.REDLINE_TRUE_PATTERNS))

    def test_secret_scan_catches_github_token_shape(self):
        fake_token = "gh" + "p_" + ("A" * 36)
        self.assertIn("GitHub classic token", safe_ci_check.secret_labels_in_text(fake_token))

    def test_secret_scan_ignores_public_ssh_key(self):
        public_key = "ssh-ed25519 " + ("A" * 68) + " user@example.invalid"
        self.assertEqual(safe_ci_check.secret_labels_in_text(public_key), [])

    def test_circleci_executable_lines_extracts_only_commands(self):
        text = "name: demo\ncommand: |\n  python --version\n  echo hello\n  git --version\n"
        self.assertEqual(
            safe_ci_check.circleci_executable_lines(text),
            ["python --version", "git --version"],
        )

    def test_circleci_allowed_commands_match_current_config(self):
        config = safe_ci_check.ROOT / ".circleci" / "config.yml"
        commands = safe_ci_check.circleci_executable_lines(config.read_text(encoding="utf-8"))
        self.assertTrue(commands)
        self.assertIn("python ci/stock_sample_room_ci_check.py", commands)
        self.assertIn("python ci/stock_mainline_ci_check.py", commands)
        self.assertIn("python ci/stock_maturity_ci_check.py", commands)
        self.assertIn("python ci/stock_consolidation_index_ci_check.py", commands)
        self.assertIn("python ci/stock_closure_panel_ci_check.py", commands)
        self.assertIn("python ci/stock_quality_evidence_ci_check.py", commands)
        self.assertIn("python ci/safe_ci_check.py", commands)
        self.assertTrue(set(commands).issubset(safe_ci_check.ALLOWED_CIRCLECI_COMMANDS))

    def test_stock_sample_room_ci_wrapper_exists(self):
        wrapper = safe_ci_check.ROOT / "ci" / "stock_sample_room_ci_check.py"
        self.assertTrue(wrapper.exists())

    def test_stock_mainline_ci_wrapper_exists(self):
        wrapper = safe_ci_check.ROOT / "ci" / "stock_mainline_ci_check.py"
        self.assertTrue(wrapper.exists())

    def test_stock_maturity_ci_checker_exists(self):
        checker = safe_ci_check.ROOT / "ci" / "stock_maturity_ci_check.py"
        self.assertTrue(checker.exists())

    def test_stock_consolidation_index_ci_checker_exists(self):
        checker = safe_ci_check.ROOT / "ci" / "stock_consolidation_index_ci_check.py"
        self.assertTrue(checker.exists())

    def test_stock_closure_panel_ci_checker_exists(self):
        checker = safe_ci_check.ROOT / "ci" / "stock_closure_panel_ci_check.py"
        self.assertTrue(checker.exists())

    def test_stock_quality_evidence_ci_checker_exists(self):
        checker = safe_ci_check.ROOT / "ci" / "stock_quality_evidence_ci_check.py"
        self.assertTrue(checker.exists())


if __name__ == "__main__":
    unittest.main()
