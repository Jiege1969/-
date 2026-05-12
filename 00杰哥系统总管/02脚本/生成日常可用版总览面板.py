# -*- coding: utf-8 -*-
"""
名称：生成日常可用版总览面板.py
作用：汇总日常可用版入口检查、轻量资源巡检和当前总体进度报告，生成用户可读的总管状态总览。
触发方式：python 生成日常可用版总览面板.py
依赖：Python标准库；日常可用版入口检查最新日志；轻量资源巡检最新日志；当前总体进度报告。
所属系统：00杰哥系统总管
安全边界：只读取总管本地状态日志和进度报告；只写入03数据/日常可用版总览；不触发n8n；不发送企业微信；不写旧系统；不执行真实业务。
创建/修改记录：2026-04-29 创建日常可用版总览面板生成脚本；2026-04-29 排除总览面板自检循环依赖，避免读取上一轮状态导致误判；2026-04-29 修正进度读取口径并纳入四大系统和重点子系统进度；2026-04-29 修正入口展示口径，面板显示与日常入口注册表一致；2026-05-06 落实总览面板自检排除逻辑，避免自身上一轮状态造成永久差1。
标识：daily-usable-overview-dashboard-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return manager_root().parent


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def latest_by_pattern(path: Path, pattern: str) -> Path | None:
    files = sorted(path.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    return files[0] if files else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    progress = report["进度"]
    lines = [
        "# 日常可用版总览面板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['状态']}",
        f"- 日常入口：{report['汇总']['日常入口可用']}/{report['汇总']['日常入口总数']} 可用",
        f"- 资源巡检：{report['汇总']['资源巡检状态']}",
        f"- 整体杰哥智能化系统进度：{progress['整体进度']}",
        f"- 基础可用版阶段：{progress['基础可用版阶段']}",
        f"- 股票研究系统：{progress['股票研究系统']}",
        "",
        "## 四大系统进度",
        "",
    ]
    for item in report.get("四大系统进度", []):
        lines.append(f"- {item['系统']}：{item['当前进度']}，还需有效工作时间 {item['可交付使用还需有效工作时间']}")
    lines.extend([
        "",
        "## 重点子系统进度",
        "",
    ])
    for item in report.get("重点子系统进度", []):
        lines.append(f"- {item['子系统']}：{item['当前进度']}，还需有效工作时间 {item['可交付使用还需有效工作时间']}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 总览面板只读取最新状态日志，不触发真实业务。",
        "- 不发送企业微信、不触发n8n、不写旧系统、不执行交易。",
    ])
    return "\n".join(lines) + "\n"


def summarize_daily_entries(daily: dict[str, Any]) -> dict[str, int]:
    entries = daily.get("入口状态", [])
    if not isinstance(entries, list):
        summary = daily.get("汇总", {})
        return {
            "total": int(summary.get("必检入口数", 0) or summary.get("入口总数", 0) or 0),
            "ok": int(summary.get("可用", 0) or 0),
        }
    required = [
        item for item in entries
        if item.get("是否必检") is True
        and item.get("名称") != "日常可用版总览面板"
    ]
    return {
        "total": len(required),
        "ok": sum(1 for item in required if item.get("可用") is True),
    }


def format_range(value: Any) -> str:
    if isinstance(value, dict) and "下限" in value and "上限" in value:
        return f"{value.get('下限', '未知')}%-{value.get('上限', '未知')}%"
    return "未知%-未知%"


def main() -> int:
    manager = manager_root()
    output_dir = manager / "03数据" / "日常可用版总览"
    daily_path = manager / "04日志" / "日常可用版" / "daily-usable-entry-check-最新.json"
    resource_path = manager / "04日志" / "轻量资源巡检" / "lightweight-resource-check-最新.json"
    progress_path = manager / "03数据" / "阶段判定" / "当前总体进度报告_最新.json"

    daily = load_json(daily_path, {})
    resource = load_json(resource_path, {})
    progress = load_json(progress_path, {}) if progress_path else {}
    progress_standard = load_json(manager / "01配置" / "进度回答标准.json", {})
    resource_summary = resource.get("汇总", {})
    progress_estimate = progress.get("进度估算", {})
    overall = progress_estimate.get("多功能智能体总体", {})
    foundation = progress_estimate.get("基础可用版阶段", {})
    stock = progress_estimate.get("股票研究系统", {})
    daily_counts = summarize_daily_entries(daily)
    daily_total = daily_counts["total"]
    daily_ok = daily_counts["ok"]
    resource_status = resource_summary.get("状态", "unknown")
    status = "healthy" if daily_total > 0 and daily_ok == daily_total and resource_status == "healthy" else "degraded"

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "daily-usable-overview-dashboard",
        "汇总": {
            "状态": status,
            "日常入口总数": daily_total,
            "日常入口可用": daily_ok,
            "资源巡检状态": resource_status,
        },
        "进度": {
            "整体进度": format_range(overall),
            "基础可用版阶段": format_range(foundation),
            "股票研究系统": format_range(stock),
        },
        "四大系统进度": progress_standard.get("四大系统", []),
        "重点子系统进度": progress_standard.get("重点子系统", []),
        "来源": {
            "日常入口检查": str(daily_path),
            "轻量资源巡检": str(resource_path),
            "当前总体进度报告": str(progress_path) if progress_path else "",
            "进度回答标准": str(manager / "01配置" / "进度回答标准.json"),
        },
        "安全边界": {
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "执行真实业务": False,
            "交易接口": False,
        },
    }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = output_dir / "daily-usable-overview-dashboard-最新.json"
    latest_json = output_dir / "daily-usable-overview-dashboard-最新.json"
    output_md = output_dir / "日常可用版总览面板_最新.md"
    latest_md = output_dir / "日常可用版总览面板_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
