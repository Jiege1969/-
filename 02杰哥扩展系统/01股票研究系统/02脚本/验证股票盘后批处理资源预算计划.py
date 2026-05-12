# -*- coding: utf-8 -*-
"""
名称：验证股票盘后批处理资源预算计划.py
作用：验证股票盘后批处理资源预算计划已生成，并严格保持禁用态安全边界。
触发方式：python 验证股票盘后批处理资源预算计划.py
依赖：Python标准库；生成股票盘后批处理资源预算计划.py；盘后批处理资源预算规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地预算计划验收；不联网；不抓取真实行情；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建股票盘后批处理资源预算计划验收脚本；2026-04-30 验收2000只标准大股票池定位。
标识：stock-after-hours-batch-resource-plan-verify
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
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票盘后批处理资源预算计划.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "32盘后批处理计划" / "股票盘后批处理资源预算计划_最新.json"
    latest_md = root / "03数据" / "32盘后批处理计划" / "股票盘后批处理资源预算计划_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = report.get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and report.get("批次数估算") == 20, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票盘后批处理资源预算计划" in text, str(latest_md))
    add_check(checks, "明确2000只标准大股票池定位", "2000只标准大股票池" in text and "规律学习" in text, "标准大股票池")
    add_check(checks, "明确2000只盘后轻扫描", "盘后日线级轻扫描" in text, "盘后轻扫描")
    add_check(checks, "明确大模型不全量分析", "不逐只分析2000只" in text, "模型边界")
    add_check(checks, "包含主动推送时间线", report.get("日常执行目标", {}).get("企业微信推送窗口") == "22:00前", report.get("日常执行目标", {}))
    add_check(checks, "包含硬件边界", "CPU" in report.get("硬件边界", {}) and "显存" in report.get("硬件边界", {}), report.get("硬件边界", {}))
    add_check(checks, "高风险动作未执行", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票盘后批处理资源预算计划可用。" if failed == 0 else "股票盘后批处理资源预算计划存在失败项。",
    }
    output_dir = root / "04日志" / "盘后批处理计划"
    output = output_dir / f"stock-after-hours-batch-resource-plan-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-after-hours-batch-resource-plan-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
