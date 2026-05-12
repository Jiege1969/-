# -*- coding: utf-8 -*-
"""
名称：验证规则自动评审与去重评分报告.py
作用：验证规则自动评审与去重评分报告生成成功，并确认规则评分、重复度、纠偏判定和安全边界完整。
触发方式：python 验证规则自动评审与去重评分报告.py
依赖：Python标准库；生成规则自动评审与去重评分报告.py。
所属系统：03杰哥进化系统
安全边界：只运行本地生成和验收；不修改其他系统业务代码，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建规则自动评审与去重评分报告验收脚本。
标识：evolution-rule-auto-review-dedupe-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = system_root()
    generator = root / "02脚本" / "生成规则自动评审与去重评分报告.py"
    latest_json = root / "03数据" / "10自动评审" / "规则自动评审与去重评分报告_最新.json"
    latest_md = root / "03数据" / "10自动评审" / "规则自动评审与去重评分报告_最新.md"
    log_dir = root / "04日志" / "规则自动评审验收"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON评审报告存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown评审报告存在", latest_md.exists(), str(latest_md))

    report = load_json(latest_json) if latest_json.exists() else {}
    reviews = report.get("规则评审", [])
    safety = report.get("安全边界", {})
    sample = report.get("小样本验收", {})
    add_check(checks, "评审规则数量不少于8", int(report.get("评审规则数量", 0) or 0) >= 8, report.get("评审规则数量"))
    add_check(checks, "每条规则都有价值分", all(isinstance(item.get("价值分"), int) for item in reviews), reviews)
    add_check(checks, "每条规则都有重复等级", all(item.get("重复等级") for item in reviews), reviews)
    add_check(checks, "每条规则都有建议动作", all(item.get("建议动作") for item in reviews), reviews)
    add_check(checks, "高价值规则不少于6", int(report.get("高价值数量", 0) or 0) >= 6, report.get("高价值数量"))
    add_check(checks, "未发现未纠偏过时闸口", int(report.get("过时闸口风险数量", 0) or 0) == 0, report.get("过时闸口风险数量"))
    add_check(checks, "小样本验收通过", sample.get("判定") == "通过", sample)
    add_check(checks, "未修改其他系统业务代码", safety.get("修改其他系统业务代码") is False, safety)
    add_check(checks, "未修改总管进度口径", safety.get("修改总管进度口径") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-rule-auto-review-dedupe-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-rule-auto-review-dedupe-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-rule-auto-review-dedupe-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
