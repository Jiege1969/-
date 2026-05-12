# -*- coding: utf-8 -*-
"""
名称：验证股票复盘反馈待回填观察报告.py
作用：验证股票复盘反馈待回填观察报告生成成功，并确认不把未回填样本误提炼为经验结论。
触发方式：python 验证股票复盘反馈待回填观察报告.py
依赖：Python标准库；生成股票复盘反馈待回填观察报告.py。
所属系统：03杰哥进化系统
安全边界：只运行03本地生成和验收；不写回股票系统，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票复盘反馈待回填观察报告验收脚本。
标识：evolution-stock-review-feedback-pending-observe-verify
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
    generator = root / "02脚本" / "生成股票复盘反馈待回填观察报告.py"
    latest_json = root / "03数据" / "14复盘反馈观察" / "股票复盘反馈待回填观察报告_最新.json"
    latest_md = root / "03数据" / "14复盘反馈观察" / "股票复盘反馈待回填观察报告_最新.md"
    log_dir = root / "04日志" / "复盘反馈观察验收"
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
    add_check(checks, "最新JSON观察报告存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown观察报告存在", latest_md.exists(), str(latest_md))
    report = load_json(latest_json) if latest_json.exists() else {}
    safety = report.get("安全边界", {})
    sample = report.get("小样本验收", {})
    add_check(checks, "来源候选包存在", sample.get("来源候选包存在") is True, sample)
    add_check(checks, "转经验条件存在", len(report.get("转经验条件", [])) >= 4, report.get("转经验条件", []))
    add_check(checks, "待回填样本数量可统计", isinstance(report.get("待回填样本数量"), int), report.get("待回填样本数量"))
    add_check(checks, "未写回股票系统", safety.get("写回股票系统") is False, safety)
    add_check(checks, "未修改股票脚本", safety.get("修改股票脚本") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-review-feedback-pending-observe-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-stock-review-feedback-pending-observe-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-stock-review-feedback-pending-observe-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
