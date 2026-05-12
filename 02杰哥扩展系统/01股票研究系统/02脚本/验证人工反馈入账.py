# -*- coding: utf-8 -*-
"""
名称：验证人工反馈入账.py
作用：验证用户自然语言反馈能够解析并写入人工决策账。
触发方式：python 验证人工反馈入账.py
依赖：Python标准库；记录人工反馈到决策账.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新股票系统人工决策账验收样例；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建人工反馈入账验收脚本。
标识：stock-human-feedback-ledger-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "记录人工反馈到决策账.py"
    result = subprocess.run(
        [sys.executable, str(script), "--sample", "--feedback", "继续观察：新易盛，原因：验收样例，等待回踩确认"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest = root / "03数据" / "10复盘闭环" / "02人工决策账" / "人工决策账记录_最新.json"
    record = load_json(latest)
    feedback = record.get("反馈记录", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "反馈脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "股票识别为新易盛", feedback.get("股票名称") == "新易盛", feedback)
    add_check(checks, "反馈识别为继续观察", feedback.get("用户反馈") == "继续观察", feedback)
    add_check(checks, "未自动升级到L4", feedback.get("是否进入L4及以上") is False, feedback)
    add_check(checks, "真实动作关闭", all(item is False for item in record.get("安全边界", {}).values()), record.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "人工反馈可入账。" if failed == 0 else "人工反馈入账存在失败项。",
    }
    output_dir = root / "04日志" / "复盘闭环"
    output = output_dir / f"stock-human-feedback-ledger-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_report = output_dir / "stock-human-feedback-ledger-verify-最新.json"
    write_json(output, report)
    write_json(latest_report, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
