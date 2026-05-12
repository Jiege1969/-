# -*- coding: utf-8 -*-
"""
名称：生成行业景气证据补全底稿.py
作用：把报告可信度面板中的 L5 股票映射到行业景气结论，生成行业景气证据待核验底稿。
安全边界：只读本地可信度面板和行业景气结论；只写 03数据/177行业景气证据补全底稿；不抓正文、不写正式库、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
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


def build_industry_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = data.get("行业景气结论", []) if isinstance(data, dict) else []
    return {str(item.get("行业", "")).strip(): item for item in items if str(item.get("行业", "")).strip()}


def build_item(row: dict[str, Any], industry_item: dict[str, Any] | None) -> dict[str, Any]:
    industry_item = industry_item or {}
    return {
        **row,
        "当前行业景气估算": {
            "是否匹配行业结论": bool(industry_item),
            "景气状态": industry_item.get("景气状态", "待补充"),
            "行业排名": industry_item.get("排名"),
            "行业强度分": industry_item.get("行业强度分"),
            "近5日平均涨跌幅": industry_item.get("近5日平均涨跌幅"),
            "近20日平均涨跌幅": industry_item.get("近20日平均涨跌幅"),
            "近20日相对强弱": industry_item.get("近20日相对强弱"),
            "数据状态": industry_item.get("数据状态", "待补充"),
            "现有结论": industry_item.get("前台结论", ""),
            "现有限制": industry_item.get("说明", "尚未接入正式申万行业指数和行业价格数据。"),
        },
        "建议核验证据": [
            "正式行业指数或申万行业指数强弱",
            "行业核心价格或产品价格",
            "政策、供需、库存、订单等景气线索",
            "行业龙头公司公告或财报中对景气的描述",
        ],
        "建议核验入口": [
            {"入口名称": "申万行业指数/行情终端", "来源级别": "行业指数或行情数据", "用途": "核验行业相对强弱，降低L6样本等权估算偏差"},
            {"入口名称": "国家统计局/行业协会/产业价格网站", "来源级别": "官方或行业数据", "用途": "核验产品价格、产销、库存、开工率等景气证据"},
            {"入口名称": "行业龙头公司定期报告", "来源级别": "上市公司正式披露", "用途": "核验行业景气是否被经营数据或管理层讨论支持"},
        ],
        "待核验问题": [
            "当前行业景气结论是否被正式行业指数或行业价格数据支持？",
            "L6样本等权估算是否可能因样本少、行业映射粗而偏高或偏低？",
            "行业景气是否足以支持前台维持推荐、观察等待或降低关注？",
            "是否需要在前台报告中增加“行业数据仍待核验”的提示？",
        ],
        "底稿状态": "待人工核验",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 行业景气证据补全底稿 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 覆盖 L5 股票：{report['股票数量']} 只",
        f"- 已匹配行业景气结论：{report['已匹配行业数量']} 只",
        "- 本底稿只把现有L6等权估算转成待核验问题，不把估算直接升级为正式行业结论。",
        "",
        "## 二、优先核验清单",
        "",
        "| 优先级 | 代码 | 名称 | 行业 | 景气状态 | 行业强度分 | 数据状态 |",
        "|---:|---|---|---|---|---:|---|",
    ]
    for item in report["股票"]:
        info = item["当前行业景气估算"]
        score = info.get("行业强度分")
        score_text = "" if score is None else f"{float(score):.2f}"
        lines.append(f"| {item['优先级']} | {item['代码']} | {item['名称']} | {item['行业']} | {info.get('景气状态')} | {score_text} | {info.get('数据状态')} |")

    lines.extend(["", "## 三、逐股核验问题", ""])
    for item in report["股票"]:
        info = item["当前行业景气估算"]
        lines.extend([
            f"### {item['名称']}({item['代码']})",
            "",
            f"- 行业：{item['行业']}",
            f"- 现有景气估算：{info.get('现有结论') or '暂无匹配行业景气结论'}",
            f"- 现有限制：{info.get('现有限制')}",
            "- 待核验问题：",
        ])
        for question in item["待核验问题"]:
            lines.append(f"  - {question}")
        lines.append("- 建议核验证据：")
        for evidence in item["建议核验证据"]:
            lines.append(f"  - {evidence}")
        lines.append("")

    lines.extend([
        "## 四、安全边界",
        "",
        "- 不抓取正文，不写正式库。",
        "- 不改评分、不改推荐、不改前台结论。",
        "- 不触发 n8n，不真实发送企业微信。",
        "- 不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    confidence_path = root / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.md"
    industry_path = root / "03数据" / "167行业景气结论" / "行业景气结论_最新.json"
    rows = parse_l5_rows(read_text(confidence_path))
    industry_map = build_industry_map(load_json(industry_path, {}))
    stocks = [build_item(row, industry_map.get(row["行业"])) for row in rows]

    report = {
        "名称": "行业景气证据补全底稿",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成行业景气证据补全底稿.py",
        "输入文件": {"报告可信度面板": str(confidence_path), "行业景气结论": str(industry_path)},
        "股票数量": len(stocks),
        "已匹配行业数量": sum(1 for item in stocks if item["当前行业景气估算"]["是否匹配行业结论"]),
        "股票": stocks,
        "安全边界": {
            "是否抓取正文": False,
            "是否写正式库": False,
            "是否改变评分或推荐": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "177行业景气证据补全底稿"
    latest_json = output_dir / "行业景气证据补全底稿_最新.json"
    latest_md = output_dir / "行业景气证据补全底稿_最新.md"
    markdown = build_markdown(report)
    write_json(output_dir / f"行业景气证据补全底稿_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(output_dir / f"行业景气证据补全底稿_{stamp}.md", markdown)
    write_text(latest_md, markdown)

    print(json.dumps({"状态": "完成", "股票数量": len(stocks), "已匹配行业数量": report["已匹配行业数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
