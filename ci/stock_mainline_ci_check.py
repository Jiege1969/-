#!/usr/bin/env python3
"""CircleCI wrapper for the stock mainline construction gate."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STOCK_MAINLINE_SCRIPT = (
    ROOT
    / "02杰哥扩展系统"
    / "01股票研究系统"
    / "02脚本"
    / "生成股票主线施工闸口面板.py"
)


def main() -> int:
    if not STOCK_MAINLINE_SCRIPT.exists():
        print(f"FAIL: missing stock mainline checker: {STOCK_MAINLINE_SCRIPT}", file=sys.stderr)
        return 1

    original_argv = sys.argv[:]
    try:
        sys.argv = [str(STOCK_MAINLINE_SCRIPT), "--ci-check", "--no-write"]
        runpy.run_path(str(STOCK_MAINLINE_SCRIPT), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    finally:
        sys.argv = original_argv
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
