# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选填写CSV副本.py
作用：读取200填写建议草案，生成独立的191候选填写CSV副本，把可复制候选预填到“填写值”列，供人工确认后参考，不覆盖原191 CSV。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：200单股证据核验191填写建议草案、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/202单股证据核验191候选填写CSV副本/单股证据核验191候选填写CSV副本_最新.csv|json|md。
安全边界：只读200填写建议草案；只写202候选CSV副本；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-191-candidate-filled-csv-copy
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def build_report(root: Path) -> dict[str, Any]:
    draft_path = root / "03数据" / "200单股证据核验191填写建议草案" / "单股证据核验191填写建议草案_最新.json"
    original_csv = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    draft = load_json(draft_path, {}) or {}
    rows = draft.get("建议明细", []) if isinstance(draft.get("建议明细"), list) else []
    candidate_rows: list[dict[str, str]] = []
    for row in rows:
        can_copy = row.get("是否可直接复制") is True
        value = str(row.get("建议填写值") or "") if can_copy else str(row.get("填写值") or "")
        candidate_rows.append({
            "股票代码": str(row.get("股票代码") or ""),
            "股票名称": str(row.get("股票名称") or ""),
            "链路": str(row.get("链路") or ""),
            "字段": str(row.get("字段") or ""),
            "是否必填": str(row.get("是否必填") or ""),
            "填写值": value,
            "填写说明": str(row.get("填写说明") or ""),
            "候选来源": str(row.get("建议依据") or ""),
            "候选置信": str(row.get("建议置信") or ""),
            "候选处理": "已预填候选" if value else "保留空白待人工确认",
        })
    return {
        "名称": "单股证据核验191候选填写CSV副本",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": draft.get("目标股票", {}),
        "输入文件": {
            "200填写建议草案": str(draft_path),
            "原191CSV": str(original_csv),
        },
        "汇总": {
            "总行数": len(candidate_rows),
            "已预填候选行数": sum(1 for row in candidate_rows if row["填写值"]),
            "保留空白待人工确认行数": sum(1 for row in candidate_rows if not row["填写值"]),
        },
        "候选CSV行": candidate_rows,
        "使用原则": [
            "本CSV是候选副本，不是正式191 CSV。",
            "人工确认后如需使用，应把确认后的值复制到191原CSV填写值列，再运行198质量闸口。",
            "核验状态、核验人、核验日期、风险判断和前台处理建议仍需人工确认。",
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


def write_candidate_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["股票代码", "股票名称", "链路", "字段", "是否必填", "填写值", "填写说明", "候选来源", "候选置信", "候选处理"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    summary = report["汇总"]
    lines = [
        f"# 单股证据核验191候选填写CSV副本 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、总览",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总行数：{summary['总行数']}",
        f"- 已预填候选行数：{summary['已预填候选行数']}",
        f"- 保留空白待人工确认行数：{summary['保留空白待人工确认行数']}",
        "",
        "## 二、使用原则",
        "",
    ]
    for item in report["使用原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path, csv_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选填写CSV副本_打开.bat"
    content = "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n' f'start "" "{csv_path}"\r\n'
    write_text(bat, content)


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "202单股证据核验191候选填写CSV副本"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选填写CSV副本_最新.json"
    latest_md = out_dir / "单股证据核验191候选填写CSV副本_最新.md"
    latest_csv = out_dir / "单股证据核验191候选填写CSV副本_最新.csv"
    write_json(out_dir / f"单股证据核验191候选填写CSV副本_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验191候选填写CSV副本_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_candidate_csv(out_dir / f"单股证据核验191候选填写CSV副本_{stamp}.csv", report["候选CSV行"])
    write_candidate_csv(latest_csv, report["候选CSV行"])
    write_open_bat(root, latest_md, latest_csv)
    print(json.dumps({"状态": "完成", "汇总": report["汇总"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
