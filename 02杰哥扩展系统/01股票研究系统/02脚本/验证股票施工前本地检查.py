# -*- coding: utf-8 -*-
"""
验证股票施工前本地检查。

安全边界：只运行本地检查与验收；不触发 n8n，不发送企业微信，不调用
Webhook，不重启服务，不写正式库，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "02脚本" / "生成股票施工前本地检查.py"
OUT_DIR = ROOT / "03数据" / "288股票施工前本地检查"
LOG_DIR = ROOT / "04日志" / "股票施工前本地检查验收"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def run_case(action: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--action", action],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest = OUT_DIR / "股票施工前本地检查_最新.json"
    return result, load_json(latest) if latest.exists() else {}


def main() -> int:
    checks: list[dict[str, Any]] = []
    low_result, low_report = run_case("整理股票施工规则表述并合并重复规则")
    medium_result, medium_report = run_case("调整前台报告证据映射和单股结论表达")
    high_result, high_report = run_case("切换正式入口并触发真实企业微信发送")

    add(checks, "低风险检查脚本返回码", low_result.returncode == 0, low_result.stdout.strip())
    add(checks, "低风险不强制影子", low_report.get("风险分级判定", {}).get("必须影子验证") is False, low_report.get("风险分级判定"))
    add(checks, "中风险要求影子", medium_report.get("风险分级判定", {}).get("必须影子验证") is True, medium_report.get("风险分级判定"))
    add(checks, "高风险不允许直接继续", high_report.get("风险分级判定", {}).get("可继续施工") is False, high_report.get("风险分级判定"))
    safety = high_report.get("安全边界", {})
    add(checks, "高风险安全边界保持关闭", all(value is False for value in safety.values()), safety)
    add(checks, "最新JSON存在", (OUT_DIR / "股票施工前本地检查_最新.json").exists(), str(OUT_DIR))
    add(checks, "最新Markdown存在", (OUT_DIR / "股票施工前本地检查_最新.md").exists(), str(OUT_DIR))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "股票施工前本地检查验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "安全边界": {
            "发送企业微信": False,
            "触发n8n": False,
            "触发Webhook": False,
            "重启服务": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(LOG_DIR / f"股票施工前本地检查验收_{stamp}.json", report)
    write_json(LOG_DIR / "股票施工前本地检查验收_最新.json", report)
    print(json.dumps({"通过": passed, "失败": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
