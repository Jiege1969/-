# -*- coding: utf-8 -*-
"""
名称：验证规则本地检查项候选.py
作用：验证规则本地检查项候选生成成功，并确认自动执行候选、风险分级候选和硬边界候选完整。
触发方式：python 验证规则本地检查项候选.py
依赖：Python标准库；生成规则本地检查项候选.py。
所属系统：03杰哥进化系统
安全边界：只运行03本地生成和验收；不修改其他系统业务代码，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建规则本地检查项候选验收脚本。
标识：evolution-local-rule-check-candidates-verify
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
    generator = root / "02脚本" / "生成规则本地检查项候选.py"
    latest_json = root / "03数据" / "11本地检查项候选" / "规则本地检查项候选_最新.json"
    latest_md = root / "03数据" / "11本地检查项候选" / "规则本地检查项候选_最新.md"
    log_dir = root / "04日志" / "本地检查项候选验收"

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
    add_check(checks, "最新JSON候选存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown候选存在", latest_md.exists(), str(latest_md))
    report = load_json(latest_json) if latest_json.exists() else {}
    candidates = report.get("检查项候选", [])
    safety = report.get("安全边界", {})
    sample = report.get("小样本验收", {})
    add_check(checks, "候选数量不少于6", int(report.get("候选数量", 0) or 0) >= 6, report.get("候选数量"))
    add_check(checks, "自动执行候选不少于4", int(report.get("自动执行候选数量", 0) or 0) >= 4, report.get("自动执行候选数量"))
    add_check(checks, "硬边界候选存在", int(report.get("硬边界候选数量", 0) or 0) >= 1, report.get("硬边界候选数量"))
    add_check(checks, "检查项ID唯一", len({item.get("检查项ID") for item in candidates}) == len(candidates), candidates)
    add_check(checks, "包含风险分级检查", sample.get("包含风险分级检查") is True, sample)
    add_check(checks, "包含硬边界检查", sample.get("包含硬边界检查") is True, sample)
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
        "类型": "evolution-local-rule-check-candidates-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-local-rule-check-candidates-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-local-rule-check-candidates-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
