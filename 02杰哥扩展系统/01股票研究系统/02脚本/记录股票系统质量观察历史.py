# -*- coding: utf-8 -*-
"""
名称：记录股票系统质量观察历史.py
作用：把最新质量观察面板摘要写入历史账本，生成可读趋势摘要。
触发方式：python 记录股票系统质量观察历史.py
依赖：03数据/146质量观察面板/股票系统质量观察面板_最新.json
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读质量观察面板；只写03数据/147质量观察历史；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-system-quality-history-ledger
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def make_record(panel: dict[str, Any]) -> dict[str, Any]:
    l5 = panel.get("L5摘要") or {}
    ai = panel.get("AI摘要") or {}
    finance = panel.get("金融专项复核摘要") or {}
    safety = panel.get("报告安全边界摘要") or {}
    trusted_ip = panel.get("可信IP状态摘要") or {}
    flags = panel.get("质量观察项") or []
    light = panel.get("质量灯号") or {}
    return {
        "记录时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "面板生成时间": panel.get("生成时间"),
        "当前交付层级": panel.get("当前交付层级"),
        "质量结论": panel.get("质量结论"),
        "质量灯号": light.get("灯号"),
        "当前公网IP": panel.get("当前公网IP"),
        "L5输出数量": l5.get("输出数量"),
        "L5目标数量": l5.get("目标数量"),
        "L5最低调整分": l5.get("最低调整分"),
        "L5最高调整分": l5.get("最高调整分"),
        "L5用户增强数量": l5.get("用户增强数量"),
        "L5战略样本数量": l5.get("战略样本数量"),
        "L5成交额估算数量": l5.get("成交额估算数量"),
        "L5风险标记股票数": l5.get("风险标记股票数"),
        "L5最高行业集中数量": l5.get("最高行业集中数量"),
        "AI分析数量": ai.get("分析数量"),
        "AI模型成功数": ai.get("模型成功数"),
        "AI规则兜底数": ai.get("规则兜底数"),
        "AI降级数量": ai.get("降级数量"),
        "AI错误数量": ai.get("错误数量"),
        "AI平均耗时_ms": ai.get("平均耗时_ms"),
        "AI最大耗时_ms": ai.get("最大耗时_ms"),
        "AI本次禁用复杂模型": ai.get("本次禁用复杂模型"),
        "金融专项复核存在": finance.get("是否存在"),
        "金融专项复核股票": finance.get("股票"),
        "金融专项复核主模型": finance.get("主模型"),
        "金融专项复核主模型成功": finance.get("主模型成功"),
        "金融专项复核交叉模型": finance.get("交叉模型"),
        "金融专项复核交叉模型成功": finance.get("交叉模型成功"),
        "金融专项复核禁止词命中": finance.get("禁止词命中") or [],
        "报告安全边界结论": safety.get("安全结论"),
        "报告安全边界命中总数": safety.get("命中总数"),
        "报告安全边界检查文件数": safety.get("检查文件数"),
        "可信IP状态": trusted_ip.get("状态"),
        "可信IP需放行IP": trusted_ip.get("当前需放行IP"),
        "可信IP命中60020": trusted_ip.get("是否命中60020"),
        "可信IP真实发送已通过": trusted_ip.get("企业微信真实发送已通过"),
        "观察项数量": len(flags),
        "阻断项数量": sum(1 for item in flags if item.get("等级") == "阻断"),
        "注意项数量": sum(1 for item in flags if item.get("等级") == "注意"),
        "红灯原因": light.get("红灯原因") or [],
        "黄灯原因": light.get("黄灯原因") or [],
        "观察项": flags,
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    recent = records[-20:]
    if not recent:
        return {}
    return {
        "记录数": len(records),
        "最近记录数": len(recent),
        "最新质量结论": recent[-1].get("质量结论"),
        "最新质量灯号": recent[-1].get("质量灯号"),
        "最新交付层级": recent[-1].get("当前交付层级"),
        "最新L5输出数量": recent[-1].get("L5输出数量"),
        "最新AI模型成功数": recent[-1].get("AI模型成功数"),
        "最近20次平均L5输出数量": round(sum(float(r.get("L5输出数量") or 0) for r in recent) / len(recent), 2),
        "最近20次平均AI成功数": round(sum(float(r.get("AI模型成功数") or 0) for r in recent) / len(recent), 2),
        "最近20次规则兜底合计": sum(int(r.get("AI规则兜底数") or 0) for r in recent),
        "最近20次错误合计": sum(int(r.get("AI错误数量") or 0) for r in recent),
        "最近20次阻断项合计": sum(int(r.get("阻断项数量") or 0) for r in recent),
        "最近20次平均耗时_ms": round(sum(float(r.get("AI平均耗时_ms") or 0) for r in recent) / len(recent), 2),
    }


def build_markdown(summary: dict[str, Any], records: list[dict[str, Any]]) -> str:
    lines = [
        f"# 股票系统质量观察历史 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 一、趋势摘要",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、最近记录", ""])
    lines.append("| 时间 | 质量结论 | L5 | AI成功 | 兜底 | 错误 | 阻断 | 平均耗时ms |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in records[-20:][::-1]:
        lines.append(
            f"| {row.get('面板生成时间')} | {row.get('质量灯号') or ''} {row.get('质量结论')} | {row.get('L5输出数量')} | "
            f"{row.get('AI模型成功数')} | {row.get('AI规则兜底数')} | {row.get('AI错误数量')} | "
            f"{row.get('阻断项数量')} | {row.get('AI平均耗时_ms')} |"
        )
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本账本只记录质量摘要。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    panel_path = root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.json"
    output_dir = root / "03数据" / "147质量观察历史"
    ledger_path = output_dir / "股票系统质量观察历史.jsonl"
    latest_json = output_dir / "股票系统质量观察历史_最新.json"
    latest_md = output_dir / "股票系统质量观察历史_最新.md"

    panel = load_json(panel_path, {})
    if not panel:
        raise FileNotFoundError(f"质量观察面板不存在或为空: {panel_path}")

    new_record = make_record(panel)
    records = load_jsonl(ledger_path)
    existing_keys = {str(item.get("面板生成时间")) for item in records}
    appended = False
    if str(new_record.get("面板生成时间")) not in existing_keys:
        records.append(new_record)
        appended = True

    summary = summarize(records)
    report = {
        "名称": "股票系统质量观察历史",
        "版本": "2026-05-01",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "记录股票系统质量观察历史.py",
        "本次是否新增记录": appended,
        "历史摘要": summary,
        "最新记录": records[-1] if records else None,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    write_jsonl(ledger_path, records)
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(summary, records))

    print(json.dumps({
        "状态": "完成",
        "本次是否新增记录": appended,
        "记录数": len(records),
        "历史面板": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
