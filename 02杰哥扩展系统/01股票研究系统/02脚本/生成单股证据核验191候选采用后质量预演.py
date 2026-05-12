# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选采用后质量预演.py
作用：不写原191 CSV，基于202候选CSV副本推演“若采用候选值后，191还剩哪些质量缺口”，为正式确认前继续压缩人工判断范围。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：191人工填写CSV表单、202候选填写CSV副本、203候选写入差异预览、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/204单股证据核验191候选采用后质量预演/单股证据核验191候选采用后质量预演_最新.json 与 .md。
安全边界：只读191原CSV、202候选CSV副本和203差异预览；只写204质量预演；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建204候选采用后质量预演，继续落实系统先推演、正式写入前只读验收。
标识：single-stock-evidence-191-candidate-adoption-quality-preview
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        str(row.get("股票代码") or "").strip(),
        str(row.get("股票名称") or "").strip(),
        str(row.get("链路") or "").strip(),
        str(row.get("字段") or "").strip(),
    )


def is_required(row: dict[str, str]) -> bool:
    return str(row.get("是否必填") or "").strip() == "是"


def build_report(root: Path) -> dict[str, Any]:
    original_csv = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    candidate_csv = root / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.csv"
    diff_preview = root / "03数据" / "203单股证据核验191候选写入差异预览" / "单股证据核验191候选写入差异预览_最新.json"
    original_rows = read_csv_rows(original_csv)
    candidate_rows = read_csv_rows(candidate_csv)
    candidate_by_key = {row_key(row): row for row in candidate_rows}

    chain_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "总字段数": 0,
        "必填字段数": 0,
        "候选后已满足必填数": 0,
        "候选后仍缺必填数": 0,
        "候选填入字段数": 0,
        "仍缺必填字段": [],
    })
    adoption_rows: list[dict[str, str]] = []
    adopted_count = 0
    for original in original_rows:
        key = row_key(original)
        candidate = candidate_by_key.get(key, {})
        original_value = str(original.get("填写值") or "").strip()
        candidate_value = str(candidate.get("填写值") or "").strip()
        adopted_value = original_value or candidate_value
        adopted = bool(not original_value and candidate_value)
        adopted_count += 1 if adopted else 0
        chain = str(original.get("链路") or "")
        field = str(original.get("字段") or "")
        required = is_required(original)
        stats = chain_stats[chain]
        stats["总字段数"] += 1
        if required:
            stats["必填字段数"] += 1
            if adopted_value:
                stats["候选后已满足必填数"] += 1
            else:
                stats["候选后仍缺必填数"] += 1
                stats["仍缺必填字段"].append(field)
        if adopted:
            stats["候选填入字段数"] += 1
        adoption_rows.append({
            "股票代码": key[0],
            "股票名称": key[1],
            "链路": chain,
            "字段": field,
            "是否必填": str(original.get("是否必填") or ""),
            "原填写值": original_value,
            "候选填写值": candidate_value,
            "候选后预演值": adopted_value,
            "预演处理": "采用候选值后满足" if adopted_value else "仍缺",
            "是否由候选补足": "是" if adopted else "否",
        })

    missing_required = [
        row for row in adoption_rows
        if row["是否必填"] == "是" and not row["候选后预演值"]
    ]
    target = {}
    if original_rows:
        first = original_rows[0]
        target = {"代码": first.get("股票代码", ""), "名称": first.get("股票名称", "")}

    return {
        "名称": "单股证据核验191候选采用后质量预演",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {
            "原191CSV": str(original_csv),
            "202候选CSV副本": str(candidate_csv),
            "203候选写入差异预览": str(diff_preview),
        },
        "汇总": {
            "原CSV行数": len(original_rows),
            "候选CSV行数": len(candidate_rows),
            "候选可补足字段数": adopted_count,
            "候选后仍缺必填字段数": len(missing_required),
            "是否允许自动写入191": False,
            "是否可直接进入198正式质量闸口": False,
        },
        "链路预演统计": dict(chain_stats),
        "候选后仍缺必填字段": missing_required,
        "候选采用预演明细": adoption_rows,
        "下一步": [
            "优先处理候选后仍缺必填字段；这些字段不是脚本可自动判断的事实或口径。",
            "如人工认可候选值，仍需通过显式确认或手工复制进入原191 CSV。",
            "原191 CSV完成后，必须再运行198正式质量闸口和197完成后预演检查。",
        ],
        "安全边界": {
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "导入正式库": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    summary = report["汇总"]
    lines = [
        f"# 单股证据核验191候选采用后质量预演 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选可补足字段数：{summary['候选可补足字段数']}",
        f"- 候选后仍缺必填字段数：{summary['候选后仍缺必填字段数']}",
        f"- 是否允许自动写入191：{summary['是否允许自动写入191']}",
        f"- 是否可直接进入198正式质量闸口：{summary['是否可直接进入198正式质量闸口']}",
        "",
        "## 二、链路预演统计",
        "",
        "| 链路 | 必填字段数 | 候选后已满足必填数 | 候选后仍缺必填数 | 候选填入字段数 |",
        "|---|---:|---:|---:|---:|",
    ]
    for chain, stats in report["链路预演统计"].items():
        lines.append(f"| {chain} | {stats['必填字段数']} | {stats['候选后已满足必填数']} | {stats['候选后仍缺必填数']} | {stats['候选填入字段数']} |")
    lines.extend(["", "## 三、候选后仍缺必填字段", "", "| 链路 | 字段 | 处理建议 |", "|---|---|---|"])
    for item in report["候选后仍缺必填字段"]:
        lines.append(f"| {item['链路']} | {item['字段']} | 需人工确认后再填191 |")
    lines.extend(["", "## 四、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选采用后质量预演_打开.bat"
    content = "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n'
    write_text(bat, content)


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "204单股证据核验191候选采用后质量预演"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选采用后质量预演_最新.json"
    latest_md = out_dir / "单股证据核验191候选采用后质量预演_最新.md"
    output_json = out_dir / f"单股证据核验191候选采用后质量预演_{stamp}.json"
    output_md = out_dir / f"单股证据核验191候选采用后质量预演_{stamp}.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_open_bat(root, latest_md)
    print(json.dumps({"状态": "完成", "汇总": report["汇总"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
