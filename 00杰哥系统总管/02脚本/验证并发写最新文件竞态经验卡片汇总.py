# -*- coding: utf-8 -*-
"""
名称：验证并发写最新文件竞态经验卡片汇总.py
作用：由00总管统一验证03进化系统并发写最新文件竞态经验卡片。
触发方式：python 验证并发写最新文件竞态经验卡片汇总.py
依赖：Python标准库；03进化系统/02脚本/验证并发写最新文件竞态经验卡片.py。
所属系统：00杰哥系统总管
安全边界：只运行本地经验卡片汇总验收；不删除文件；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建并发写最新文件竞态经验卡片总管验收汇总。
标识：evolution-concurrent-latest-write-experience-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = system_root()
    verify = root / "03杰哥进化系统" / "02脚本" / "验证并发写最新文件竞态经验卡片.py"
    result = subprocess.run([sys.executable, str(verify)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    checks = [
        {"名称": "经验卡片验收脚本存在", "通过": verify.exists(), "详情": str(verify)},
        {"名称": "经验卡片验收通过", "通过": result.returncode == 0, "详情": {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}},
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "并发写最新文件竞态经验卡片已纳入总管统一验收。" if failed == 0 else "并发写最新文件竞态经验卡片总管验收存在失败项。",
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "并发写最新文件竞态经验卡片"
    output = output_dir / f"evolution-concurrent-latest-write-experience-summary-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "evolution-concurrent-latest-write-experience-summary-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
