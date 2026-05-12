# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验正式回执填写前自检.py
作用：只读核对205正式回执草案、210状态、212样例副本和214待办卡，生成正式填写205前的自检报告。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：205确认回执草案CSV/JSON、210确认回执状态面板、212确认回执填写样例副本、214正式回执待办卡、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/215单股证据核验正式回执填写前自检/单股证据核验正式回执填写前自检_最新.json|md。
安全边界：只读205/210/212/214；只写215自检报告；不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建215正式回执填写前自检，防止样例副本、待办卡和正式回执混用。
标识：single-stock-evidence-formal-confirmation-receipt-prefill-check
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ["确认结果", "核验状态", "核验人", "核验日期"]
EXPECTED_VALUES = {"确认结果": "确认采用", "核验状态": "已核验"}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def row_status(row: dict[str, str], todo: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if not str(row.get(field, "")).strip()]
    mismatched = []
    for field, expected in EXPECTED_VALUES.items():
        value = str(row.get(field, "")).strip()
        if value and value != expected:
            mismatched.append({"字段": field, "当前值": value, "期望值": expected})
    todo_format = todo.get("建议填写格式", {}) if isinstance(todo.get("建议填写格式"), dict) else {}
    return {
        "链路": row.get("链路", ""),
        "当前缺失字段": missing,
        "当前异常字段": mismatched,
        "214建议填写格式": {field: todo_format.get(field, "") for field in REQUIRED_FIELDS},
        "是否已达到确认完成格式": not missing and not mismatched,
    }


def build_report(root: Path) -> dict[str, Any]:
    receipt_csv_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv"
    receipt_json_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    status_path = root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.json"
    example_path = root / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.json"
    todo_path = root / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.json"
    receipt_json = load_json(receipt_json_path, {}) or {}
    status = load_json(status_path, {}) or {}
    example = load_json(example_path, {}) or {}
    todo = load_json(todo_path, {}) or {}
    rows = load_csv(receipt_csv_path)
    todo_by_chain = {item.get("链路", ""): item for item in todo.get("待办事项", []) if isinstance(item, dict)}
    details = [row_status(row, todo_by_chain.get(row.get("链路", ""), {})) for row in rows]
    completed = sum(1 for item in details if item["是否已达到确认完成格式"])
    missing_count = sum(len(item["当前缺失字段"]) for item in details)
    abnormal_count = sum(len(item["当前异常字段"]) for item in details)
    return {
        "名称": "单股证据核验正式回执填写前自检",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": receipt_json.get("目标股票", {}) if isinstance(receipt_json.get("目标股票"), dict) else {},
        "输入文件": {
            "205正式回执CSV": str(receipt_csv_path),
            "205正式回执JSON": str(receipt_json_path),
            "210确认回执状态面板": str(status_path),
            "212样例副本": str(example_path),
            "214正式回执待办卡": str(todo_path),
        },
        "汇总": {
            "正式回执行数": len(rows),
            "214待办链路数": len(todo_by_chain),
            "212样例链路数": (example.get("汇总", {}) or {}).get("样例链路数"),
            "210确认完成链路数": (status.get("汇总", {}) or {}).get("确认完成链路数"),
            "当前达到确认完成格式链路数": completed,
            "当前缺失字段总数": missing_count,
            "当前异常字段总数": abnormal_count,
            "是否允许进入206闸口": completed == 3 and missing_count == 0 and abnormal_count == 0,
            "本报告是否写入205": False,
        },
        "链路自检": details,
        "填写前提醒": [
            "只填写正式205 CSV，不填写212样例副本。",
            "三条链路都需要填写：确认结果=确认采用、核验状态=已核验、核验人=真实核验人、核验日期=当天或实际核验日期。",
            "填写完成后先刷新210状态面板；210未显示三链路确认完成前，206仍应阻断。",
            "本报告只判断当前状态，不自动写205、不自动写191。",
        ],
        "安全边界": {
            "覆盖205": False,
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    summary = report["汇总"]
    lines = [
        f"# 单股证据核验正式回执填写前自检 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、当前状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 正式回执行数：{summary['正式回执行数']}",
        f"- 214待办链路数：{summary['214待办链路数']}",
        f"- 210确认完成链路数：{summary['210确认完成链路数']}",
        f"- 当前缺失字段总数：{summary['当前缺失字段总数']}",
        f"- 是否允许进入206闸口：{summary['是否允许进入206闸口']}",
        "",
        "## 二、链路自检",
        "",
        "| 链路 | 当前缺失字段 | 当前异常字段 | 是否已达到确认完成格式 |",
        "|---|---|---|---|",
    ]
    for item in report["链路自检"]:
        abnormal = "；".join(f"{x['字段']}={x['当前值']}（应为{x['期望值']}）" for x in item["当前异常字段"]) or "无"
        lines.append(f"| {item['链路']} | {'、'.join(item['当前缺失字段']) or '无'} | {abnormal} | {item['是否已达到确认完成格式']} |")
    lines.extend(["", "## 三、填写前提醒", ""])
    for item in report["填写前提醒"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "215单股证据核验正式回执填写前自检"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验正式回执填写前自检_最新.json"
    latest_md = out_dir / "单股证据核验正式回执填写前自检_最新.md"
    write_json(out_dir / f"单股证据核验正式回执填写前自检_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验正式回执填写前自检_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": "完成", "当前缺失字段总数": report["汇总"]["当前缺失字段总数"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
