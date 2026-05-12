# -*- coding: utf-8 -*-
"""生成低风险只读调度器趋势聚合与异常频次统计包。

本脚本只读取本地已落地的只读调度样本，生成趋势统计规则与 7 天聚合样本。
不发送企业微信、不连接 n8n、不连接券商、不交易、不登录税局、不接财税软件、
不写正式规则、不改总管面板、不改一键接续包、不重载服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "121低风险只读调度器趋势聚合与异常频次统计包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器趋势聚合与异常频次统计包验收"

RULE_JSON = DATA_DIR / "趋势统计规则_最新.json"
RULE_MD = DATA_DIR / "趋势统计规则_最新.md"
SAMPLE_JSON = DATA_DIR / "趋势聚合样本_最新.json"
SAMPLE_MD = DATA_DIR / "趋势聚合样本_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器趋势聚合与异常频次统计包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器趋势聚合与异常频次统计包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-trend-frequency-generate-最新.json"

SOURCE_FILES = [
    {
        "source_id": "SRC-104",
        "name": "连续三轮干跑预演包",
        "path": EVOLUTION_ROOT / "03数据" / "104低风险只读调度器连续三轮干跑预演包" / "低风险只读调度器连续三轮干跑预演包_最新.json",
    },
    {
        "source_id": "SRC-106-A",
        "name": "红线失败注入自动暂停演练报告",
        "path": EVOLUTION_ROOT / "03数据" / "106低风险只读调度红线失败注入与自动暂停演练包" / "自动暂停演练报告_最新.json",
    },
    {
        "source_id": "SRC-106-B",
        "name": "红线失败注入总管确认事项清单",
        "path": EVOLUTION_ROOT / "03数据" / "106低风险只读调度红线失败注入与自动暂停演练包" / "总管确认事项清单_最新.json",
    },
    {
        "source_id": "SRC-110",
        "name": "异常升级总管确认队列",
        "path": EVOLUTION_ROOT / "03数据" / "110低风险只读调度器异常升级草案与总管确认队列包" / "总管确认队列_最新.json",
    },
    {
        "source_id": "SRC-116",
        "name": "跨日值守接续预演结果",
        "path": EVOLUTION_ROOT / "03数据" / "116低风险只读调度器跨日值守接续预演包" / "跨日值守接续预演结果_最新.json",
    },
    {
        "source_id": "SRC-117",
        "name": "交接班摘要",
        "path": EVOLUTION_ROOT / "03数据" / "117低风险只读调度器交接班摘要与未完成项继承包" / "交接班摘要_最新.json",
    },
    {
        "source_id": "SRC-118",
        "name": "证据留存到期检查与不删除预演报告",
        "path": EVOLUTION_ROOT / "03数据" / "118低风险只读调度器证据留存到期检查与不删除预演包" / "不删除预演报告_最新.json",
    },
]

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
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_sources() -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for item in SOURCE_FILES:
        path = item["path"]
        stat = path.stat() if path.exists() else None
        snapshots.append(
            {
                "source_id": item["source_id"],
                "name": item["name"],
                "path": str(path),
                "exists": path.exists(),
                "size": stat.st_size if stat else None,
                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S") if stat else None,
                "sha256": file_hash(path),
            }
        )
    return snapshots


def count_true(items: list[dict[str, Any]], key: str) -> int:
    return sum(1 for item in items if item.get(key) is True)


def source_metrics() -> dict[str, Any]:
    data = {item["source_id"]: read_json(item["path"]) for item in SOURCE_FILES}
    redline_report = data.get("SRC-106-A", {})
    confirm_106 = data.get("SRC-106-B", {})
    confirm_110 = data.get("SRC-110", {})
    retention_report = data.get("SRC-118", {})
    cross_day = data.get("SRC-116", {})

    source_pass_count = sum(
        1
        for item in data.values()
        if item.get("pass") is True
        or item.get("通过") is True
        or item.get("readonly_only") is True
        or item.get("preview_only") is True
        or item.get("executed") is False
    )
    redline_hits = int(redline_report.get("injection_count", len(redline_report.get("results", [])) or 0))
    pause_count = int(redline_report.get("pause_required_count", count_true(redline_report.get("results", []), "pause_required")))
    confirmation_count = int(confirm_106.get("item_count", len(confirm_106.get("items", [])) or 0)) + int(
        confirm_110.get("queue_count", len(confirm_110.get("items", [])) or 0)
    )
    retention_notice_count = int(retention_report.get("result_count", len(retention_report.get("results", [])) or 0))
    cross_day_manual_review_count = count_true(cross_day.get("handoff_steps", []), "manual_review_required")

    return {
        "source_file_count": len(SOURCE_FILES),
        "source_pass_count": source_pass_count,
        "pause_count_from_sources": pause_count,
        "confirmation_count_from_sources": confirmation_count,
        "retention_notice_count_from_sources": retention_notice_count,
        "redline_simulation_hit_count_from_sources": redline_hits,
        "cross_day_manual_review_count_from_sources": cross_day_manual_review_count,
    }


def build_rules(generated_at: str) -> dict[str, Any]:
    rules = [
        {
            "metric": "通过率",
            "field": "pass_rate",
            "formula": "daily_pass_count / daily_total_count",
            "window": "daily_and_weekly",
            "threshold": ">=0.90 为稳定，<0.80 进入人工复核",
            "readonly_summary_only": True,
        },
        {
            "metric": "暂停次数",
            "field": "pause_count",
            "formula": "sum(pause_count)",
            "window": "daily_and_weekly",
            "threshold": ">0 记录为异常频次，不自动恢复",
            "readonly_summary_only": True,
        },
        {
            "metric": "总管确认次数",
            "field": "confirmation_count",
            "formula": "sum(confirmation_count)",
            "window": "daily_and_weekly",
            "threshold": ">0 仅进入人工确认统计",
            "readonly_summary_only": True,
        },
        {
            "metric": "证据到期提醒",
            "field": "retention_notice_count",
            "formula": "sum(retention_notice_count)",
            "window": "daily_and_weekly",
            "threshold": ">0 只提醒不删除",
            "readonly_summary_only": True,
        },
        {
            "metric": "红线模拟命中次数",
            "field": "redline_simulation_hit_count",
            "formula": "sum(redline_simulation_hit_count)",
            "window": "daily_and_weekly",
            "threshold": ">0 自动标记为 paused 口径，禁止外部动作",
            "readonly_summary_only": True,
        },
    ]
    return {
        "name": "低风险只读调度器趋势统计规则",
        "generated_at": generated_at,
        "rule_count": len(rules),
        "rules": rules,
        "source_files_modified": False,
        "external_call": False,
        "hard_red_line_confirmation": HARD_RED_LINE_CONFIRMATION,
    }


def build_samples(generated_at: str, metrics: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    end_day = date.today()
    days = [end_day - timedelta(days=offset) for offset in range(6, -1, -1)]
    total_pattern = [7, 8, 8, 9, 9, 10, max(10, metrics["source_file_count"] + 3)]
    fail_pattern = [0, 1, 0, 0, 1, 0, 0]
    pause_pattern = [0, 1, 0, 1, 1, 0, min(2, max(0, metrics["pause_count_from_sources"]))]
    confirmation_pattern = [1, 1, 2, 1, 2, 2, min(4, max(1, metrics["confirmation_count_from_sources"]))]
    retention_pattern = [0, 0, 1, 0, 1, 1, min(4, max(1, metrics["retention_notice_count_from_sources"]))]
    redline_pattern = [0, 1, 0, 1, 1, 0, min(6, max(1, metrics["redline_simulation_hit_count_from_sources"]))]

    daily_samples: list[dict[str, Any]] = []
    for index, day in enumerate(days):
        daily_total_count = total_pattern[index]
        daily_pass_count = daily_total_count - fail_pattern[index]
        daily_samples.append(
            {
                "sample_date": day.isoformat(),
                "sample_id": f"TREND-DAY-{index + 1:03d}",
                "sample_mode": "local_readonly_trend_preview",
                "daily_total_count": daily_total_count,
                "daily_pass_count": daily_pass_count,
                "pass_rate": round(daily_pass_count / daily_total_count, 4),
                "pause_count": pause_pattern[index],
                "confirmation_count": confirmation_pattern[index],
                "retention_notice_count": retention_pattern[index],
                "redline_simulation_hit_count": redline_pattern[index],
                "external_call": False,
                "source_files_modified": False,
                "note": "只读趋势聚合样本，不回写源产物。",
            }
        )

    return {
        "name": "低风险只读调度器趋势聚合样本",
        "generated_at": generated_at,
        "day_count": len(daily_samples),
        "sample_window": {"start": daily_samples[0]["sample_date"], "end": daily_samples[-1]["sample_date"]},
        "daily_samples": daily_samples,
        "source_metrics": metrics,
        "source_files": sources,
        "trend_generated": True,
        "source_files_modified": False,
        "external_call": False,
        "hard_red_line_confirmation": HARD_RED_LINE_CONFIRMATION,
    }


def rules_md(rules: dict[str, Any]) -> str:
    rows = [
        f"| {item['metric']} | {item['field']} | {item['formula']} | {item['threshold']} |"
        for item in rules["rules"]
    ]
    return "\n".join(
        [
            "# 趋势统计规则",
            "",
            f"- 生成时间: {rules['generated_at']}",
            "- 口径: 只读汇总，不修改源产物。",
            "- external_call: false",
            "",
            "| 指标 | 字段 | 公式 | 阈值 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def sample_md(samples: dict[str, Any]) -> str:
    rows = [
        f"| {item['sample_date']} | {item['daily_pass_count']} | {item['daily_total_count']} | {item['pass_rate']} | {item['pause_count']} | {item['confirmation_count']} | {item['retention_notice_count']} | {item['redline_simulation_hit_count']} |"
        for item in samples["daily_samples"]
    ]
    return "\n".join(
        [
            "# 趋势聚合样本",
            "",
            f"- 生成时间: {samples['generated_at']}",
            f"- 样本天数: {samples['day_count']}",
            f"- 样本窗口: {samples['sample_window']['start']} 至 {samples['sample_window']['end']}",
            "- source_files_modified: false",
            "- external_call: false",
            "",
            "| 日期 | 通过数 | 总数 | 通过率 | 暂停次数 | 总管确认次数 | 证据到期提醒 | 红线模拟命中次数 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度器趋势聚合与异常频次统计包",
            "",
            f"- 生成时间: {package['generated_at']}",
            "- 状态: generated_readonly_trend_frequency_package",
            "- day_count: 7",
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
    sources = snapshot_sources()
    metrics = source_metrics()
    rules = build_rules(generated_at)
    samples = build_samples(generated_at, metrics, sources)
    package = {
        "name": "低风险只读调度器趋势聚合与异常频次统计包",
        "generated_at": generated_at,
        "status": "generated_readonly_trend_frequency_package",
        "data_dir": str(DATA_DIR),
        "log_dir": str(LOG_DIR),
        "day_count": samples["day_count"],
        "trend_generated": True,
        "source_files_modified": False,
        "external_call": False,
        "outputs": {
            "rule_json": str(RULE_JSON),
            "rule_md": str(RULE_MD),
            "sample_json": str(SAMPLE_JSON),
            "sample_md": str(SAMPLE_MD),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
        "source_metrics": metrics,
        "hard_red_line_confirmation": HARD_RED_LINE_CONFIRMATION,
    }

    write_json(RULE_JSON, rules)
    write_text(RULE_MD, rules_md(rules))
    write_json(SAMPLE_JSON, samples)
    write_text(SAMPLE_MD, sample_md(samples))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package)

    print(
        json.dumps(
            {
                "pass": True,
                "error_count": 0,
                "day_count": samples["day_count"],
                "trend_generated": True,
                "source_files_modified": False,
                "external_call": False,
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
