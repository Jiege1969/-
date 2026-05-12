# -*- coding: utf-8 -*-
"""
名称：检查股票系统报告安全边界.py
作用：扫描股票系统最新报告，检查是否出现交易指令、价格预测、收益承诺等越界表述。
触发方式：python 检查股票系统报告安全边界.py
依赖：03数据/135分层日报、136推送草稿、149金融专项复核等最新报告。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读报告文件；只写03数据/150报告安全边界检查和05入口工具；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-report-safety-boundary-check
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


FORBIDDEN_PATTERNS = [
    "买入",
    "卖出",
    "持有",
    "目标价",
    "仓位",
    "收益承诺",
    "稳赚",
    "必涨",
    "翻倍",
    "无风险",
    "上涨动力",
    "前景广阔",
    "利好消息",
    "买卖建议",
]

SAFE_CONTEXT_HINTS = [
    "禁止",
    "不得",
    "不提供",
    "不构成",
    "不包含",
    "未发现",
    "禁止词",
    "安全边界",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_safe_context(line: str) -> bool:
    return any(hint in line for hint in SAFE_CONTEXT_HINTS)


def scan_file(path: Path) -> dict[str, Any]:
    text = read_text(path)
    hits: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if is_safe_context(line):
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                hits.append({
                    "行号": idx,
                    "命中词": pattern,
                    "内容": line.strip()[:180],
                })
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "命中数量": len(hits),
        "命中明细": hits,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统报告安全边界检查 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 安全结论：{report['安全结论']}",
        f"- 检查文件数：{report['检查文件数']}",
        f"- 存在文件数：{report['存在文件数']}",
        f"- 命中数量：{report['命中总数']}",
        "",
        "## 二、逐文件结果",
        "",
    ]
    for item in report["文件结果"]:
        lines.append(f"### {item['名称']}")
        lines.append(f"- 路径：`{item['路径']}`")
        lines.append(f"- 存在：{item['存在']}")
        lines.append(f"- 命中数量：{item['命中数量']}")
        if item["命中明细"]:
            for hit in item["命中明细"]:
                lines.append(f"  - 第{hit['行号']}行 `{hit['命中词']}`：{hit['内容']}")
        lines.append("")
    lines.extend([
        "## 三、安全边界",
        "",
        "- 本检查只扫描文本报告。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "股票系统报告安全边界检查_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    targets = [
        ("AI分析报告", root / "03数据" / "135分层日报" / "AI分析报告_最新.md"),
        ("企微推送草案", root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"),
        ("推送前放行包", root / "03数据" / "138推送前放行包" / "股票企微推送前放行包_最新.md"),
        ("金融专项复核", root / "03数据" / "149金融专项复核" / "股票金融专项复核_最新.md"),
    ]
    file_results = []
    for name, path in targets:
        result = scan_file(path)
        result["名称"] = name
        file_results.append(result)

    hit_count = sum(int(item["命中数量"]) for item in file_results)
    existing_count = sum(1 for item in file_results if item["存在"])
    conclusion = "通过" if hit_count == 0 else "需人工复核"
    report = {
        "名称": "股票系统报告安全边界检查",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "检查股票系统报告安全边界.py",
        "安全结论": conclusion,
        "检查文件数": len(file_results),
        "存在文件数": existing_count,
        "命中总数": hit_count,
        "禁用词": FORBIDDEN_PATTERNS,
        "安全上下文提示": SAFE_CONTEXT_HINTS,
        "文件结果": file_results,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "150报告安全边界检查"
    output_json = output_dir / f"股票系统报告安全边界检查_{stamp}.json"
    output_md = output_dir / f"股票系统报告安全边界检查_{stamp}.md"
    latest_json = output_dir / "股票系统报告安全边界检查_最新.json"
    latest_md = output_dir / "股票系统报告安全边界检查_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(latest_md)

    print(json.dumps({
        "状态": "完成",
        "安全结论": conclusion,
        "命中总数": hit_count,
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
