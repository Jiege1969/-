# -*- coding: utf-8 -*-
"""
名称：生成股票金融专项复核索引.py
作用：汇总03数据/149金融专项复核中的金融复核报告，生成索引和统计摘要。
触发方式：python 生成股票金融专项复核索引.py
依赖：03数据/149金融专项复核/股票金融专项复核_*.json
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读金融专项复核报告；只写03数据/149金融专项复核索引；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-finance-special-review-index
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def collect_reports(input_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("股票金融专项复核_*.json")):
        if path.name == "股票金融专项复核_最新.json":
            continue
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001
            rows.append({
                "文件": str(path),
                "读取成功": False,
                "错误": str(exc),
            })
            continue
        stock = data.get("股票") or {}
        main_result = data.get("主模型结果") or {}
        cross_result = data.get("交叉对照结果")
        rows.append({
            "文件": str(path),
            "读取成功": True,
            "生成时间": data.get("生成时间"),
            "代码": stock.get("代码"),
            "展示代码": stock.get("展示代码"),
            "名称": stock.get("名称"),
            "行业": stock.get("行业"),
            "细分领域": stock.get("细分领域"),
            "主模型": main_result.get("model_used"),
            "主模型成功": bool(main_result.get("success")),
            "主模型耗时_ms": main_result.get("latency_ms"),
            "主模型错误": main_result.get("error_msg"),
            "是否启用交叉对照": bool(data.get("是否启用交叉对照")),
            "交叉模型": cross_result.get("model_used") if isinstance(cross_result, dict) else None,
            "交叉模型成功": bool(cross_result.get("success")) if isinstance(cross_result, dict) else None,
        })
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("读取成功")]
    stocks = {(row.get("代码"), row.get("名称")) for row in valid}
    success_count = sum(1 for row in valid if row.get("主模型成功"))
    latencies = [int(row.get("主模型耗时_ms") or 0) for row in valid if row.get("主模型耗时_ms") is not None]
    return {
        "报告文件数": len(rows),
        "有效报告数": len(valid),
        "覆盖股票数": len(stocks),
        "主模型成功数": success_count,
        "主模型失败数": len(valid) - success_count,
        "平均耗时_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "最大耗时_ms": max(latencies) if latencies else None,
        "行业分布": [{"行业": key, "数量": value} for key, value in Counter(str(row.get("行业") or "未分类") for row in valid).most_common()],
        "模型分布": [{"模型": key, "数量": value} for key, value in Counter(str(row.get("主模型") or "未知") for row in valid).most_common()],
    }


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["摘要"]
    lines = [
        f"# 股票金融专项复核索引 - {report['生成时间']}",
        "",
        "## 一、摘要",
        "",
    ]
    for key, value in summary.items():
        if isinstance(value, list):
            continue
        lines.append(f"- {key}：{value}")
    lines.extend(["", "行业分布："])
    for item in summary["行业分布"]:
        lines.append(f"- {item['行业']}：{item['数量']}")
    lines.extend(["", "模型分布："])
    for item in summary["模型分布"]:
        lines.append(f"- {item['模型']}：{item['数量']}")
    lines.extend([
        "",
        "## 二、最近报告",
        "",
        "| 生成时间 | 股票 | 行业 | 主模型 | 成功 | 耗时ms |",
        "|---|---|---|---|---:|---:|",
    ])
    valid = [row for row in report["索引"] if row.get("读取成功")]
    for row in valid[-20:][::-1]:
        lines.append(
            f"| {row.get('生成时间')} | {row.get('名称')}({row.get('展示代码')}) | {row.get('行业')} | "
            f"{row.get('主模型')} | {row.get('主模型成功')} | {row.get('主模型耗时_ms')} |"
        )
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本索引只汇总本地复核报告。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, target: Path) -> Path:
    entry_dir = root / "05入口工具"
    bat = entry_dir / "股票金融专项复核索引_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    input_dir = root / "03数据" / "149金融专项复核"
    output_dir = root / "03数据" / "149金融专项复核索引"
    rows = collect_reports(input_dir)
    report = {
        "名称": "股票金融专项复核索引",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票金融专项复核索引.py",
        "输入目录": str(input_dir),
        "摘要": summarize(rows),
        "索引": rows,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_json = output_dir / f"股票金融专项复核索引_{stamp}.json"
    output_md = output_dir / f"股票金融专项复核索引_{stamp}.md"
    latest_json = output_dir / "股票金融专项复核索引_最新.json"
    latest_md = output_dir / "股票金融专项复核索引_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    entry_bat = write_entry_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "有效报告数": report["摘要"]["有效报告数"],
        "覆盖股票数": report["摘要"]["覆盖股票数"],
        "索引": str(latest_md),
        "入口工具": str(entry_bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
