# -*- coding: utf-8 -*-
"""验证低风险只读调度器趋势聚合与异常频次统计包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "121低风险只读调度器趋势聚合与异常频次统计包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器趋势聚合与异常频次统计包验收"

RULE_JSON = DATA_DIR / "趋势统计规则_最新.json"
RULE_MD = DATA_DIR / "趋势统计规则_最新.md"
SAMPLE_JSON = DATA_DIR / "趋势聚合样本_最新.json"
SAMPLE_MD = DATA_DIR / "趋势聚合样本_最新.md"
TREND_JSON = DATA_DIR / "趋势聚合结果_最新.json"
TREND_MD = DATA_DIR / "趋势聚合结果_最新.md"
REPORT_JSON = DATA_DIR / "异常频次统计报告_最新.json"
REPORT_MD = DATA_DIR / "异常频次统计报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器趋势聚合与异常频次统计包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器趋势聚合与异常频次统计包_最新.md"
LATEST_LOG = LOG_DIR / "low-risk-readonly-scheduler-trend-frequency-verify-最新.json"

REQUIRED_METRICS = {"通过率", "暂停次数", "总管确认次数", "证据到期提醒", "红线模拟命中次数"}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def validate_hard_red_lines(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key, value in data.get("hard_red_line_confirmation", {}).items():
        if value is not False:
            errors.append(f"{scope}.hard_red_line_confirmation.{key} 必须为 false")


def main() -> int:
    errors: list[str] = []
    required_files = [
        RULE_JSON,
        RULE_MD,
        SAMPLE_JSON,
        SAMPLE_MD,
        TREND_JSON,
        TREND_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    rules = read_json(RULE_JSON) if RULE_JSON.exists() else {"rules": []}
    samples = read_json(SAMPLE_JSON) if SAMPLE_JSON.exists() else {"daily_samples": []}
    trend = read_json(TREND_JSON) if TREND_JSON.exists() else {"metrics": {}}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {"metrics": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    rule_metrics = {item.get("metric") for item in rules.get("rules", [])}
    missing_metrics = sorted(REQUIRED_METRICS - rule_metrics)
    if missing_metrics:
        errors.append(f"趋势统计规则缺少指标: {missing_metrics}")

    daily_samples = samples.get("daily_samples", [])
    if len(daily_samples) < 7:
        errors.append("趋势聚合样本必须至少包含 7 天")
    for index, item in enumerate(daily_samples, start=1):
        for key in ["daily_pass_count", "pause_count", "confirmation_count", "retention_notice_count"]:
            if key not in item:
                errors.append(f"第 {index} 天样本缺少字段 {key}")
        require_false(errors, item, "source_files_modified", f"sample[{index}]")
        require_false(errors, item, "external_call", f"sample[{index}]")

    for scope, data in [
        ("rules", rules),
        ("samples", samples),
        ("trend", trend),
        ("report", report),
        ("package", package),
    ]:
        require_false(errors, data, "source_files_modified", scope)
        require_false(errors, data, "external_call", scope)
        validate_hard_red_lines(errors, data, scope)

    require_true(errors, samples, "trend_generated", "samples")
    require_true(errors, trend, "trend_generated", "trend")
    require_true(errors, report, "trend_generated", "report")
    require_true(errors, package, "trend_generated", "package")

    if report.get("pass") is not True:
        errors.append("异常频次统计报告 pass 必须为 true")
    if report.get("error_count") != 0:
        errors.append("异常频次统计报告 error_count 必须为 0")
    if report.get("day_count", 0) < 7:
        errors.append("异常频次统计报告 day_count 必须 >= 7")
    if trend.get("day_count", 0) < 7:
        errors.append("趋势聚合结果 day_count 必须 >= 7")

    metric_fields = report.get("metrics", {})
    for key in [
        "daily_pass_count",
        "pause_count",
        "confirmation_count",
        "retention_notice_count",
        "redline_simulation_hit_count",
    ]:
        if key not in metric_fields:
            errors.append(f"异常频次统计报告 metrics 缺少 {key}")

    verification = {
        "name": "低风险只读调度器趋势聚合与异常频次统计包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "day_count": report.get("day_count", len(daily_samples)),
        "trend_generated": report.get("trend_generated") is True and trend.get("trend_generated") is True,
        "source_files_modified": False,
        "external_call": False,
        "target_data_dir": str(DATA_DIR),
        "log": str(LATEST_LOG),
        "metrics": {
            "required_file_count": len(required_files),
            "existing_file_count": sum(1 for path in required_files if path.exists()),
            "rule_metric_count": len(rule_metrics),
            "day_count": len(daily_samples),
            "pause_count": metric_fields.get("pause_count"),
            "confirmation_count": metric_fields.get("confirmation_count"),
            "retention_notice_count": metric_fields.get("retention_notice_count"),
            "redline_simulation_hit_count": metric_fields.get("redline_simulation_hit_count"),
            "error_count": len(errors),
        },
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    write_json(LATEST_LOG, verification)
    print(
        json.dumps(
            {
                "pass": verification["pass"],
                "error_count": verification["error_count"],
                "day_count": verification["day_count"],
                "trend_generated": verification["trend_generated"],
                "source_files_modified": verification["source_files_modified"],
                "external_call": verification["external_call"],
                "log": str(LATEST_LOG),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
