# -*- coding: utf-8 -*-
"""
名称：生成事件风险证据补全底稿.py
作用：从股票报告可信度面板提取 L5 股票，生成事件与风险证据待核验底稿。
安全边界：只读本地 Markdown；只写 03数据/174事件风险证据补全底稿；不抓正文、不写正式库、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def exchange_name(code: str) -> str:
    if code.startswith("sh"):
        return "上交所"
    if code.startswith("sz"):
        return "深交所"
    return "待确认"


def cninfo_url(code: str) -> str:
    return f"http://www.cninfo.com.cn/new/disclosure/stock?stockCode={code[2:] if len(code) > 2 else code}"


def exchange_url(code: str) -> str:
    number = code[2:] if len(code) > 2 else code
    if code.startswith("sh"):
        return f"https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?productId={number}"
    if code.startswith("sz"):
        return "https://www.szse.cn/disclosure/listed/fixed/index.html"
    return ""


def parse_l5_rows(markdown: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|$")
    for line in markdown.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        priority, code, name, industry, confidence, grade, gaps = match.groups()
        rows.append({
            "优先级": int(priority),
            "代码": code.strip(),
            "名称": name.strip(),
            "行业": industry.strip(),
            "可信度": int(confidence),
            "等级": grade.strip(),
            "主要缺口": gaps.strip(),
        })
    return rows


def build_item(row: dict[str, Any]) -> dict[str, Any]:
    code = row["代码"]
    return {
        **row,
        "证据缺口": [
            "公告事件",
            "解禁减持",
            "行业价格或景气变化",
            "监管问询或诉讼风险",
        ],
        "建议核验入口": [
            {
                "入口名称": "巨潮资讯公告入口",
                "来源级别": "官方/交易所指定信息披露入口",
                "URL": cninfo_url(code),
                "用途": "核验公告、定期报告、临时公告、减持、质押、诉讼等事件线索",
            },
            {
                "入口名称": f"{exchange_name(code)}公告入口",
                "来源级别": "交易所官方入口",
                "URL": exchange_url(code),
                "用途": "复核交易所公告和监管相关披露",
            },
        ],
        "待核验问题": [
            "最近是否有业绩预告、定期报告或重大事项公告影响前台判断？",
            "是否存在减持、解禁、质押、诉讼、监管问询、处罚等风险事件？",
            "行业价格、政策或供需变化是否会强化或削弱当前策略结论？",
            "现有前台结论是否需要增加风险观察线或降低关注等级？",
        ],
        "底稿状态": "待人工核验",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 事件与风险证据补全底稿 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 覆盖 L5 股票：{report['股票数量']} 只",
        "- 本底稿只列待核验证据入口和问题，不抓取公告正文，不形成事实结论。",
        "- 后续只有人工核验状态为“已核验”的记录，才允许进入预览层。",
        "",
        "## 二、优先核验清单",
        "",
        "| 优先级 | 代码 | 名称 | 行业 | 可信度 | 证据缺口 |",
        "|---:|---|---|---|---:|---|",
    ]
    for item in report["股票"]:
        gaps = "、".join(item["证据缺口"])
        lines.append(f"| {item['优先级']} | {item['代码']} | {item['名称']} | {item['行业']} | {item['可信度']} | {gaps} |")

    lines.extend(["", "## 三、逐股核验入口", ""])
    for item in report["股票"]:
        lines.extend([
            f"### {item['名称']}({item['代码']})",
            "",
            f"- 当前主要缺口：{item['主要缺口']}",
            "- 待核验问题：",
        ])
        for question in item["待核验问题"]:
            lines.append(f"  - {question}")
        lines.append("- 建议核验入口：")
        for entry in item["建议核验入口"]:
            lines.append(f"  - {entry['入口名称']}：{entry['URL']}")
        lines.append("")

    lines.extend([
        "## 四、安全边界",
        "",
        "- 不抓取公告正文。",
        "- 不写公司品质档案、公司经营快照或正式库。",
        "- 不触发 n8n，不真实发送企业微信。",
        "- 不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    source_path = root / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.md"
    rows = parse_l5_rows(read_text(source_path))
    stocks = [build_item(row) for row in rows]
    report = {
        "名称": "事件与风险证据补全底稿",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成事件风险证据补全底稿.py",
        "输入文件": str(source_path),
        "股票数量": len(stocks),
        "股票": stocks,
        "安全边界": {
            "是否抓取正文": False,
            "是否写正式库": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "174事件风险证据补全底稿"
    latest_json = output_dir / "事件风险证据补全底稿_最新.json"
    latest_md = output_dir / "事件风险证据补全底稿_最新.md"
    write_json(output_dir / f"事件风险证据补全底稿_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(output_dir / f"事件风险证据补全底稿_{stamp}.md", build_markdown(report))
    write_text(latest_md, build_markdown(report))

    print(json.dumps({"状态": "完成", "股票数量": len(stocks), "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
