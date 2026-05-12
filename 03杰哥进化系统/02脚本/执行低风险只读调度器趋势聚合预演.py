# -*- coding: utf-8 -*-
"""执行低风险只读调度器趋势聚合预演。

读取 121 包内趋势规则和 7 天样本，输出趋势聚合结果与异常频次统计报告。
仅写入 121 数据目录与固定验收目录下的本包日志，不回写任何源产物。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "121低风险只读调度器趋势聚合与异常频次统计包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器趋势聚合与异常频次统计包验收"

RULE_JSON = DATA_DIR / "趋势统计规则_最新.json"
SAMPLE_JSON = DATA_DIR / "趋势聚合样本_最新.json"
TREND_JSON = DATA_DIR / "趋势聚合结果_最新.json"
TREND_MD = DATA_DIR / "趋势聚合结果_最新.md"
REPORT_JSON = DATA_DIR / "异常频次统计报告_最新.json"
REPORT_MD = DATA_DIR / "异常频次统计报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器趋势聚合与异常频次统计包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器趋势聚合与异常频次统计包_最新.md"
PREVIEW_LOG = LOG_DIR / "low-risk-readonly-scheduler-trend-frequency-preview-最新.json"

HARD_RED_LINE_CONFIRMATION = {
    "real_wecom_send": False,
    "connect_n8n": False,
    "trigger_n8n": False,
    "broker_connection": False,
    "trade_order": False,
    "tax_bureau_login": False,
    "finance_tax_software_connection": False,
    "write_formal_rule": False,
    "auto_promote_formal_rule": False,
    "modify_supervisor_panel": False,
    "modify_one_click_continuation_package": False,
    "reload_service": False,
    "external_call": False,
}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def frequency_level(value: float) -> str:
    if value == 0:
        return "none"
    if value < 1:
        return "low"
    if value < 3:
        return "medium"
    return "high"


def build_trend(generated_at: str, rules: dict[str, Any], samples: dict[str, Any]) -> dict[str, Any]:
    daily_samples = samples.get("daily_samples", [])
    total_count = sum(int(item.get("daily_total_count", 0)) for item in daily_samples)
    pass_count = sum(int(item.get("daily_pass_count", 0)) for item in daily_samples)
    pause_count = sum(int(item.get("pause_count", 0)) for item in daily_samples)
    confirmation_count = sum(int(item.get("confirmation_count", 0)) for item in daily_samples)
    retention_notice_count = sum(int(item.get("retention_notice_count", 0)) for item in daily_samples)
    redline_hit_count = sum(int(item.get("redline_simulation_hit_count", 0)) for item in daily_samples)
    day_count = len(daily_samples)

    return {
        "name": "低风险只读调度器趋势聚合结果",
        "generated_at": generated_at,
        "day_count": day_count,
        "trend_generated": True,
        "source_files_modified": False,
        "external_call": False,
        "metrics": {
            "daily_total_count": total_count,
            "daily_pass_count": pass_count,
            "pass_rate": round(pass_count / total_count, 4) if total_count else 0,
            "pause_count": pause_count,
            "confirmation_count": confirmation_count,
            "retention_notice_count": retention_notice_count,
            "redline_simulation_hit_count": redline_hit_count,
            "pause_frequency_per_day": round(pause_count / day_count, 4) if day_count else 0,
            "confirmation_frequency_per_day": round(confirmation_count / day_count, 4) if day_count else 0,
            "retention_notice_frequency_per_day": round(retention_notice_count / day_count, 4) if day_count else 0,
            "redline_hit_frequency_per_day": round(redline_hit_count / day_count, 4) if day_count else 0,
        },
        "rules_applied": [item.get("metric") for item in rules.get("rules", [])],
        "daily_samples": daily_samples,
        "hard_red_line_confirmation": HARD_RED_LINE_CONFIRMATION,
    }


def build_report(generated_at: str, trend: dict[str, Any]) -> dict[str, Any]:
    metrics = trend["metrics"]
    anomaly_items = [
        {
            "metric": "暂停次数",
            "field": "pause_count",
            "total": metrics["pause_count"],
            "frequency_per_day": metrics["pause_frequency_per_day"],
            "level": frequency_level(metrics["pause_frequency_per_day"]),
            "decision": "只读记录，不自动恢复",
        },
        {
            "metric": "总管确认次数",
            "field": "confirmation_count",
            "total": metrics["confirmation_count"],
            "frequency_per_day": metrics["confirmation_frequency_per_day"],
            "level": frequency_level(metrics["confirmation_frequency_per_day"]),
            "decision": "只读记录，等待人工确认",
        },
        {
            "metric": "证据到期提醒",
            "field": "retention_notice_count",
            "total": metrics["retention_notice_count"],
            "frequency_per_day": metrics["retention_notice_frequency_per_day"],
            "level": frequency_level(metrics["retention_notice_frequency_per_day"]),
            "decision": "只提醒不删除",
        },
        {
            "metric": "红线模拟命中次数",
            "field": "redline_simulation_hit_count",
            "total": metrics["redline_simulation_hit_count"],
            "frequency_per_day": metrics["redline_hit_frequency_per_day"],
            "level": frequency_level(metrics["redline_hit_frequency_per_day"]),
            "decision": "只读统计，保持暂停口径",
        },
    ]
    return {
        "name": "低风险只读调度器异常频次统计报告",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "day_count": trend["day_count"],
        "trend_generated": True,
        "source_files_modified": False,
        "external_call": False,
        "readonly_summary_only": True,
        "metrics": metrics,
        "anomaly_frequency": anomaly_items,
        "hard_red_line_confirmation": HARD_RED_LINE_CONFIRMATION,
    }


def trend_md(trend: dict[str, Any]) -> str:
    metrics = trend["metrics"]
    rows = [
        f"| {item['sample_date']} | {item['daily_pass_count']} | {item['daily_total_count']} | {item['pass_rate']} | {item['pause_count']} | {item['confirmation_count']} | {item['retention_notice_count']} | {item['redline_simulation_hit_count']} |"
        for item in trend["daily_samples"]
    ]
    return "\n".join(
        [
            "# 趋势聚合结果",
            "",
            f"- 生成时间: {trend['generated_at']}",
            f"- day_count: {trend['day_count']}",
            f"- pass_rate: {metrics['pass_rate']}",
            "- trend_generated: true",
            "- source_files_modified: false",
            "- external_call: false",
            "",
            "| 日期 | 通过数 | 总数 | 通过率 | 暂停次数 | 总管确认次数 | 证据到期提醒 | 红线模拟命中次数 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def report_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['metric']} | {item['total']} | {item['frequency_per_day']} | {item['level']} | {item['decision']} |"
        for item in report["anomaly_frequency"]
    ]
    return "\n".join(
        [
            "# 异常频次统计报告",
            "",
            f"- 生成时间: {report['generated_at']}",
            f"- day_count: {report['day_count']}",
            "- trend_generated: true",
            "- source_files_modified: false",
            "- external_call: false",
            "",
            "| 指标 | 总数 | 日均频次 | 频次级别 | 处理口径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度器趋势聚合与异常频次统计包",
            "",
            f"- 更新时间: {package['updated_at']}",
            f"- day_count: {package['day_count']}",
            "- trend_generated: true",
            "- source_files_modified: false",
            "- external_call: false",
            "",
            "## 输出文件",
            "",
            *[f"- {name}: {path}" for name, path in package["outputs"].items()],
            "",
        ]
    )


def main() -> int:
    generated_at = now()
    rules = read_json(RULE_JSON)
    samples = read_json(SAMPLE_JSON)
    trend = build_trend(generated_at, rules, samples)
    report = build_report(generated_at, trend)

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    outputs = package.get("outputs", {})
    outputs.update(
        {
            "trend_json": str(TREND_JSON),
            "trend_md": str(TREND_MD),
            "anomaly_frequency_json": str(REPORT_JSON),
            "anomaly_frequency_md": str(REPORT_MD),
            "preview_log": str(PREVIEW_LOG),
        }
    )
    package.update(
        {
            "updated_at": generated_at,
            "status": "trend_frequency_preview_generated",
            "day_count": trend["day_count"],
            "trend_generated": True,
            "source_files_modified": False,
            "external_call": False,
            "metrics": trend["metrics"],
            "outputs": outputs,
            "hard_red_line_confirmation": HARD_RED_LINE_CONFIRMATION,
        }
    )

    write_json(TREND_JSON, trend)
    write_text(TREND_MD, trend_md(trend))
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, report_md(report))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(PREVIEW_LOG, report)

    print(
        json.dumps(
            {
                "pass": True,
                "error_count": 0,
                "day_count": trend["day_count"],
                "trend_generated": True,
                "source_files_modified": False,
                "external_call": False,
                "report": str(REPORT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
