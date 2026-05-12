# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信报告反馈改版候选.py
作用：只读验收企业微信报告反馈是否已进入进化候选层。
边界：不写正式规则、不触发n8n、不发送企业微信、不接券商、不交易。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    now = datetime.now()
    root = root_dir()
    generator = root / "02脚本" / "生成股票企业微信报告反馈改版候选.py"
    sample_json = root / "03数据" / "13股票复盘反馈样本" / "股票企业微信报告反馈样本_最新.json"
    candidate_json = root / "03数据" / "15复盘转经验候选" / "股票企业微信报告反馈改版候选_最新.json"
    candidate_md = root / "03数据" / "15复盘转经验候选" / "股票企业微信报告反馈改版候选_最新.md"
    log_dir = root / "04日志" / "股票企业微信报告反馈改版候选验收"

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
    add_check(checks, "反馈样本最新JSON存在", sample_json.exists(), str(sample_json))
    add_check(checks, "改版候选最新JSON存在", candidate_json.exists(), str(candidate_json))
    add_check(checks, "改版候选最新Markdown存在", candidate_md.exists(), str(candidate_md))

    report = read_json(candidate_json) if candidate_json.exists() else {}
    candidates = report.get("候选", []) if isinstance(report.get("候选"), list) else []
    safety = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    types = {str(item.get("候选类型", "")) for item in candidates if isinstance(item, dict)}
    add_check(checks, "候选数量大于0", len(candidates) > 0, len(candidates))
    add_check(checks, "包含股票名称可点击详情候选", "stock_report_clickable_detail_link" in types, sorted(types))
    add_check(checks, "所有候选禁止自动转正式规则", all(item.get("是否自动转正式规则") is False for item in candidates), len(candidates))
    add_check(checks, "所有候选禁止写正式规则库", all(item.get("是否写正式规则库") is False for item in candidates), len(candidates))
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未真实发送企业微信", safety.get("企业微信真实发送") is False, safety)
    add_check(checks, "未接券商", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)
    add_check(checks, "未重载19310", safety.get("重载19310") is False, safety)
    add_check(checks, "未重载19302", safety.get("重载19302") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "名称": "股票企业微信报告反馈改版候选验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(candidate_json),
    }
    output_json = log_dir / f"stock-wecom-report-feedback-candidate-verify-{now.strftime('%Y%m%d-%H%M%S')}.json"
    latest_json = log_dir / "stock-wecom-report-feedback-candidate-verify-最新.json"
    latest_md = log_dir / "stock-wecom-report-feedback-candidate-verify-最新.md"
    write_json(output_json, verify)
    write_json(latest_json, verify)
    md = [
        "# 股票企业微信报告反馈改版候选验收",
        "",
        f"- 生成时间：{verify['生成时间']}",
        f"- 通过：{passed}",
        f"- 失败：{failed}",
        f"- 验收对象：{candidate_json}",
    ]
    write_text(latest_md, "\n".join(md))
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
