# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选写入差异预览.py
作用：对比原191 CSV与202候选填写CSV副本，生成“如果采用候选值会填入什么、仍缺什么”的差异预览，不写原191。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：191人工填写CSV表单、202单股证据核验191候选填写CSV副本、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/203单股证据核验191候选写入差异预览/单股证据核验191候选写入差异预览_最新.json 与 .md。
安全边界：只读191原CSV和202候选CSV副本；只写203差异预览；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建203候选写入差异预览，落实“系统先干活、正式写入前先预览差异”。
标识：single-stock-evidence-191-candidate-write-diff-preview
"""

from __future__ import annotations

import csv
import json
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
    original_rows = read_csv_rows(original_csv)
    candidate_rows = read_csv_rows(candidate_csv)
    candidate_by_key = {row_key(row): row for row in candidate_rows}

    fillable: list[dict[str, str]] = []
    already_filled_same: list[dict[str, str]] = []
    conflict_or_changed: list[dict[str, str]] = []
    still_missing_required: list[dict[str, str]] = []
    still_missing_optional: list[dict[str, str]] = []

    for original in original_rows:
        key = row_key(original)
        candidate = candidate_by_key.get(key, {})
        original_value = str(original.get("填写值") or "").strip()
        candidate_value = str(candidate.get("填写值") or "").strip()
        item = {
            "股票代码": key[0],
            "股票名称": key[1],
            "链路": key[2],
            "字段": key[3],
            "是否必填": str(original.get("是否必填") or ""),
            "原填写值": original_value,
            "候选填写值": candidate_value,
            "候选来源": str(candidate.get("候选来源") or ""),
            "候选置信": str(candidate.get("候选置信") or ""),
            "处理建议": "",
        }
        if not original_value and candidate_value:
            item["处理建议"] = "候选可填入，正式写入前仍需确认"
            fillable.append(item)
        elif original_value and candidate_value and original_value == candidate_value:
            item["处理建议"] = "原191已填写且与候选一致"
            already_filled_same.append(item)
        elif original_value and candidate_value and original_value != candidate_value:
            item["处理建议"] = "原191已填写但与候选不同，需人工比对"
            conflict_or_changed.append(item)
        elif is_required(original):
            item["处理建议"] = "必填字段仍缺候选值，需人工判断"
            still_missing_required.append(item)
        else:
            item["处理建议"] = "非必填字段仍为空"
            still_missing_optional.append(item)

    target = {}
    if original_rows:
        first = original_rows[0]
        target = {"代码": first.get("股票代码", ""), "名称": first.get("股票名称", "")}

    return {
        "名称": "单股证据核验191候选写入差异预览",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {
            "原191CSV": str(original_csv),
            "202候选CSV副本": str(candidate_csv),
        },
        "汇总": {
            "原CSV行数": len(original_rows),
            "候选CSV行数": len(candidate_rows),
            "候选可填入字段数": len(fillable),
            "原已填写且与候选一致数": len(already_filled_same),
            "原已填写但候选不同数": len(conflict_or_changed),
            "仍缺必填字段数": len(still_missing_required),
            "仍缺非必填字段数": len(still_missing_optional),
            "是否允许自动写入191": False,
        },
        "候选可填入字段": fillable,
        "仍缺必填字段": still_missing_required,
        "候选冲突字段": conflict_or_changed,
        "原已填写且候选一致字段": already_filled_same,
        "仍缺非必填字段": still_missing_optional,
        "下一步": [
            "先阅读本203差异预览，确认候选值是否适合进入191。",
            "仍缺必填字段需要在201最小人工确认清单中完成链路级确认。",
            "正式191 CSV不会被本脚本修改；只有另行显式确认后，才能进入候选采用或手工复制流程。",
            "191完成后必须先运行198质量闸口，再运行197完成后预演检查。",
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
        f"# 单股证据核验191候选写入差异预览 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 原CSV行数：{summary['原CSV行数']}",
        f"- 候选CSV行数：{summary['候选CSV行数']}",
        f"- 候选可填入字段数：{summary['候选可填入字段数']}",
        f"- 仍缺必填字段数：{summary['仍缺必填字段数']}",
        f"- 是否允许自动写入191：{summary['是否允许自动写入191']}",
        "",
        "## 二、可填入候选字段",
        "",
        "| 链路 | 字段 | 候选置信 | 候选来源 | 候选填写值摘要 |",
        "|---|---|---|---|---|",
    ]
    for item in report["候选可填入字段"][:30]:
        value = item["候选填写值"].replace("\n", " ")
        if len(value) > 90:
            value = value[:90] + "..."
        source = item["候选来源"].replace("|", "｜")
        lines.append(f"| {item['链路']} | {item['字段']} | {item['候选置信']} | {source} | {value} |")
    lines.extend([
        "",
        "## 三、仍缺必填字段",
        "",
        "| 链路 | 字段 | 处理建议 |",
        "|---|---|---|",
    ])
    for item in report["仍缺必填字段"]:
        lines.append(f"| {item['链路']} | {item['字段']} | {item['处理建议']} |")
    lines.extend([
        "",
        "## 四、下一步",
        "",
    ])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选写入差异预览_打开.bat"
    content = "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n'
    write_text(bat, content)


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "203单股证据核验191候选写入差异预览"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选写入差异预览_最新.json"
    latest_md = out_dir / "单股证据核验191候选写入差异预览_最新.md"
    output_json = out_dir / f"单股证据核验191候选写入差异预览_{stamp}.json"
    output_md = out_dir / f"单股证据核验191候选写入差异预览_{stamp}.md"
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
