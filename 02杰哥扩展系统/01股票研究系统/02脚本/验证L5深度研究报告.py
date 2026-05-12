# -*- coding: utf-8 -*-
"""
名称：验证L5深度研究报告.py
作用：验证L5深度研究报告和候选池日报生成链路可运行且不越权。
触发方式：python 验证L5深度研究报告.py
依赖：Python标准库；生成L5深度研究报告.py；L5深度研究报告规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地报告生成；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建L5深度研究报告验收脚本。
标识：stock-l5-deep-research-report-verify
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
    generator = root / "02脚本" / "生成L5深度研究报告.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report = load_json(root / "03数据" / "15深度研究" / "L5深度研究报告_最新.json")
    markdown = root / "03数据" / "03研究报告" / "L5深度研究候选日报_最新.md"
    text = markdown.read_text(encoding="utf-8") if markdown.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "报告脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "结构化报告已生成", bool(report.get("候选池")), list(report.keys()))
    add_check(checks, "Markdown日报已生成", markdown.exists() and "L5深度研究候选日报" in text, str(markdown))
    add_check(checks, "包含人工确认入口", "确认L4" in text or "继续观察" in text, text[:500])
    add_check(checks, "包含数据健康度", "数据健康度" in text and report.get("数据健康度", {}).get("健康等级") in {"优秀", "可用", "降级", "暂停"}, report.get("数据健康度", {}))
    add_check(checks, "真实动作关闭", all(item is False for item in report.get("安全边界", {}).values()), report.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "L5深度研究报告生成链路可运行。" if failed == 0 else "L5深度研究报告生成链路存在失败项。",
    }
    output_dir = root / "04日志" / "深度研究"
    output = output_dir / f"stock-l5-deep-research-report-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-l5-deep-research-report-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
