# -*- coding: utf-8 -*-
"""
名称：生成股票复盘反馈样本接入候选包.py
作用：只读股票系统复盘账和到期提醒，生成进化系统可学习的真实复盘反馈样本候选包。
触发方式：python 生成股票复盘反馈样本接入候选包.py
依赖：Python标准库；股票系统04日志/复盘/判断复盘账_最新.json。
所属系统：03杰哥进化系统
安全边界：只读股票系统复盘结果，只写03进化系统本地候选包；不回填股票系统，不改股票脚本，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票复盘反馈样本接入候选包脚本。
标识：evolution-stock-review-feedback-candidates-generate
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return system_root().parents[0]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stock_root() -> Path:
    return project_root() / "02杰哥扩展系统" / "01股票研究系统"


def cycle_fields(record: dict[str, Any]) -> list[str]:
    fields = []
    for key in ["T1", "T3", "T5", "T20", "T60", "T120"]:
        if f"验证结果_{key}" in record or key in record.get("应验证周期", []):
            fields.append(key)
    return fields


def has_feedback(record: dict[str, Any]) -> bool:
    for key in ["T1", "T3", "T5", "T20", "T60", "T120"]:
        if record.get(f"验证结果_{key}") not in [None, "", []]:
            return True
    return record.get("人工评价") not in [None, "", []]


def candidate_status(record: dict[str, Any]) -> str:
    if has_feedback(record):
        return "可进入经验提炼"
    if record.get("应验证周期"):
        return "待复盘反馈"
    return "待补验证周期"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票复盘反馈样本接入候选包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 复盘账记录数：{report['复盘账记录数']}",
        f"- 可进入经验提炼：{report['可进入经验提炼数量']}",
        f"- 待复盘反馈：{report['待复盘反馈数量']}",
        f"- 样本候选：{report['样本候选数量']}",
        "",
        "## 样本候选摘要",
        "",
    ]
    for item in report["样本候选"][:20]:
        lines.append(f"- {item['股票名称']}({item['股票代码']})：{item['样本状态']}，周期 {','.join(item['验证周期'])}")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    ledger_path = stock_root() / "04日志" / "复盘" / "判断复盘账_最新.json"
    reminder_path = stock_root() / "03数据" / "114复盘到期提醒与人工填写清单" / "300只候选复盘到期提醒与人工填写清单_最新.json"
    ledger = load_json(ledger_path, [])
    reminder = load_json(reminder_path, {})
    if isinstance(ledger, dict):
        records = ledger.get("记录", ledger.get("复盘账", ledger.get("items", [])))
    else:
        records = ledger
    records = [item for item in records if isinstance(item, dict)]

    status_counter = Counter(candidate_status(item) for item in records)
    cycle_counter: Counter[str] = Counter()
    candidates = []
    for item in records:
        cycles = cycle_fields(item)
        cycle_counter.update(cycles)
        candidates.append(
            {
                "股票代码": item.get("股票代码", ""),
                "股票名称": item.get("股票名称", ""),
                "报告日期": item.get("报告日期", ""),
                "报告类型": item.get("报告类型", ""),
                "判断主因": item.get("判断主因", ""),
                "分层状态": item.get("分层状态", ""),
                "系统评分": item.get("系统评分", item.get("L5调整分")),
                "证据完整度": item.get("证据完整度", ""),
                "验证周期": cycles,
                "样本状态": candidate_status(item),
                "人工评价": item.get("人工评价"),
                "原始报告路径": item.get("原始报告路径", ""),
                "经验提炼建议": "已有复盘反馈，可提炼判断有效性经验。" if has_feedback(item) else "暂不提炼结论，等待复盘结果或人工评价回填。",
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-review-feedback-candidates",
        "所属系统": "03杰哥进化系统",
        "输入来源": {
            "复盘账": str(ledger_path),
            "复盘到期提醒": str(reminder_path),
            "复盘到期提醒存在": bool(reminder),
        },
        "复盘账记录数": len(records),
        "样本候选数量": len(candidates),
        "可进入经验提炼数量": status_counter.get("可进入经验提炼", 0),
        "待复盘反馈数量": status_counter.get("待复盘反馈", 0),
        "待补验证周期数量": status_counter.get("待补验证周期", 0),
        "验证周期统计": dict(cycle_counter),
        "样本状态统计": dict(status_counter),
        "样本候选": candidates,
        "小样本验收": {
            "复盘账存在": ledger_path.exists(),
            "复盘账记录数大于0": len(records) > 0,
            "候选数量大于0": len(candidates) > 0,
            "不写回股票系统": True,
            "判定": "通过" if len(candidates) > 0 else "需等待样本"
        },
        "安全边界": {
            "写回股票系统": False,
            "修改股票脚本": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }

    out_dir = root / "03数据" / "13股票复盘反馈样本"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票复盘反馈样本接入候选包_{timestamp}.json"
    latest_json = out_dir / "股票复盘反馈样本接入候选包_最新.json"
    output_md = out_dir / f"股票复盘反馈样本接入候选包_{timestamp}.md"
    latest_md = out_dir / "股票复盘反馈样本接入候选包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"样本候选数量": len(candidates), "输出": str(output_json), "判定": report["小样本验收"]["判定"]}, ensure_ascii=True))
    return 0 if report["小样本验收"]["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
