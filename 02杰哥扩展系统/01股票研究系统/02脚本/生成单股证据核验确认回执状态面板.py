# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验确认回执状态面板.py
作用：读取205确认回执草案JSON/CSV，判断三条链路是否已完成确认，并给出下一步受控流转状态。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：205候选采用确认回执草案、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/210单股证据核验确认回执状态面板/单股证据核验确认回执状态面板_最新.json|md。
安全边界：只读205确认回执草案；只写210状态面板；不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建210确认回执状态面板，让总管系统自主识别确认回执是否具备后续流转条件。
标识：single-stock-evidence-confirmation-receipt-status-panel
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CHAINS = ["公司概况", "事件风险", "行业景气"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


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


def is_positive_confirmation(text: str) -> bool:
    value = text.strip()
    return value in {"确认", "同意", "采用", "已确认", "确认采用", "是"}


def evaluate_row(row: dict[str, str]) -> dict[str, Any]:
    chain = str(row.get("链路") or "").strip()
    result = str(row.get("确认结果") or "").strip()
    status = str(row.get("核验状态") or "").strip()
    reviewer = str(row.get("核验人") or "").strip()
    date_value = str(row.get("核验日期") or "").strip()
    issues: list[str] = []
    if chain not in CHAINS:
        issues.append("链路名称不在三条标准链路内")
    if not is_positive_confirmation(result):
        issues.append("确认结果未明确为确认/同意/采用")
    if status != "已核验":
        issues.append("核验状态必须为已核验")
    if not reviewer:
        issues.append("核验人为空")
    if not DATE_PATTERN.match(date_value):
        issues.append("核验日期必须为YYYY-MM-DD")
    return {
        "链路": chain,
        "确认结果": result,
        "核验状态": status,
        "核验人": reviewer,
        "核验日期": date_value,
        "是否确认完成": not issues,
        "问题": issues,
    }


def build_report(root: Path) -> dict[str, Any]:
    json_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    csv_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv"
    draft = load_json(json_path, {}) or {}
    csv_rows = read_csv_rows(csv_path)
    rows_source = "CSV" if csv_rows else "JSON"
    rows = csv_rows
    if not rows:
        rows = draft.get("确认回执草案", []) if isinstance(draft.get("确认回执草案"), list) else []
    evaluated = [evaluate_row({key: str(value or "") for key, value in row.items()}) for row in rows]
    completed = sum(1 for item in evaluated if item["是否确认完成"])
    missing_chains = [chain for chain in CHAINS if chain not in {item["链路"] for item in evaluated}]
    all_confirmed = completed == 3 and not missing_chains
    return {
        "名称": "单股证据核验确认回执状态面板",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": draft.get("目标股票", {}) if isinstance(draft.get("目标股票"), dict) else {},
        "输入文件": {
            "205确认回执JSON": str(json_path),
            "205确认回执CSV": str(csv_path),
        },
        "汇总": {
            "读取来源": rows_source,
            "识别链路数": len(evaluated),
            "确认完成链路数": completed,
            "缺失链路": missing_chains,
            "是否三链路确认完成": all_confirmed,
            "是否允许重跑206采用前闸口": all_confirmed,
            "是否允许进入208带值预览": all_confirmed,
            "是否允许触发197写191": False,
            "当前状态": "确认回执已完成，可重跑206/208生成后续预览" if all_confirmed else "确认回执未完成，继续阻断写191和模板同步",
        },
        "链路状态": evaluated,
        "下一步": [
            "若未完成：只补205确认回执CSV中的确认结果、核验状态、核验人、核验日期。",
            "若三链路均完成：重跑206采用前闸口，再跑208候选采用预览和209受控写入命令草案。",
            "210本身不写191，也不替用户确认事实。",
        ],
        "安全边界": {
            "覆盖205": False,
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
        f"# 单股证据核验确认回执状态面板 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、当前状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 读取来源：{summary['读取来源']}",
        f"- 确认完成链路数：{summary['确认完成链路数']} / 3",
        f"- 是否三链路确认完成：{summary['是否三链路确认完成']}",
        f"- 当前状态：{summary['当前状态']}",
        "",
        "## 二、链路状态",
        "",
        "| 链路 | 是否确认完成 | 问题 |",
        "|---|---|---|",
    ]
    for item in report["链路状态"]:
        issues = "；".join(item["问题"]) or "无"
        lines.append(f"| {item['链路']} | {item['是否确认完成']} | {issues} |")
    if report["汇总"]["缺失链路"]:
        lines.append(f"| 缺失链路 | False | {'、'.join(report['汇总']['缺失链路'])} |")
    lines.extend(["", "## 三、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验确认回执状态面板_打开.bat"
    write_text(bat, "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n')


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "210单股证据核验确认回执状态面板"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验确认回执状态面板_最新.json"
    latest_md = out_dir / "单股证据核验确认回执状态面板_最新.md"
    write_json(out_dir / f"单股证据核验确认回执状态面板_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验确认回执状态面板_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_open_bat(root, latest_md)
    print(json.dumps({"状态": "完成", "是否三链路确认完成": report["汇总"]["是否三链路确认完成"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
