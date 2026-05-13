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


if __name__ == "__main__":
    unittest.main()
