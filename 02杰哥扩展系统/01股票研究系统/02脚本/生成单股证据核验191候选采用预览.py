# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选采用预览.py
作用：基于205确认回执、206采用前闸口和202候选CSV副本，生成候选采用预览；当前未确认时只显示阻断，不写原191。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：202候选填写CSV副本、205候选采用确认回执草案、206候选采用前闸口、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/208单股证据核验191候选采用预览/单股证据核验191候选采用预览_最新.json|csv|md。
安全边界：只读202/205/206；只写208采用预览；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建208候选采用预览，让总管系统能在确认后生成采用预览、未确认时自动阻断。
标识：single-stock-evidence-191-candidate-adoption-preview
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


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["股票代码", "股票名称", "链路", "字段", "是否必填", "预览填写值", "预览来源", "预览状态"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def confirmed_chains(confirmation: dict[str, Any]) -> set[str]:
    rows = confirmation.get("确认回执草案", []) if isinstance(confirmation.get("确认回执草案"), list) else []
    confirmed: set[str] = set()
    for row in rows:
        if (
            str(row.get("确认结果") or "").strip()
            and str(row.get("核验状态") or "").strip()
            and str(row.get("核验人") or "").strip()
            and str(row.get("核验日期") or "").strip()
        ):
            confirmed.add(str(row.get("链路") or "").strip())
    return confirmed


def build_report(root: Path) -> dict[str, Any]:
    candidate_csv = root / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.csv"
    confirmation_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    pre_gate_path = root / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.json"
    confirmation = load_json(confirmation_path, {}) or {}
    pre_gate = load_json(pre_gate_path, {}) or {}
    rows = read_csv_rows(candidate_csv)
    confirmed = confirmed_chains(confirmation)
    all_confirmed = len(confirmed) == 3 and (confirmation.get("汇总", {}) or {}).get("是否已获得用户确认") is True
    pre_gate_allows = pre_gate.get("是否允许采用候选写入191CSV") is True
    preview_allowed = all_confirmed and pre_gate_allows
    preview_rows: list[dict[str, str]] = []
    for row in rows:
        chain = str(row.get("链路") or "").strip()
        value = str(row.get("填写值") or "").strip()
        if preview_allowed and chain in confirmed and value:
            status = "确认后可进入采用预览"
        elif value:
            status = "候选存在但确认未完成，阻断"
        else:
            status = "无候选值，仍需人工处理"
        preview_rows.append({
            "股票代码": str(row.get("股票代码") or ""),
            "股票名称": str(row.get("股票名称") or ""),
            "链路": chain,
            "字段": str(row.get("字段") or ""),
            "是否必填": str(row.get("是否必填") or ""),
            "预览填写值": value if preview_allowed else "",
            "预览来源": str(row.get("候选来源") or ""),
            "预览状态": status,
        })
    target = confirmation.get("目标股票", {}) if isinstance(confirmation.get("目标股票"), dict) else {}
    return {
        "名称": "单股证据核验191候选采用预览",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {
            "202候选填写CSV副本": str(candidate_csv),
            "205候选采用确认回执草案": str(confirmation_path),
            "206候选采用前闸口": str(pre_gate_path),
        },
        "汇总": {
            "候选行数": len(rows),
            "已确认链路数": len(confirmed),
            "是否三链路已确认": all_confirmed,
            "206是否允许采用": pre_gate_allows,
            "是否生成可采用预览值": preview_allowed,
            "当前阻断原因": "" if preview_allowed else "205确认回执未完成或206闸口未放行",
        },
        "候选采用预览行": preview_rows,
        "下一步": [
            "当前未确认时，208只生成阻断预览，不写原191。",
            "205三条链路确认完成且206重新放行后，208才可生成带预览填写值的采用预览。",
            "即使208生成采用预览，也仍需再经过198质量闸口和197默认预演。",
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
        f"# 单股证据核验191候选采用预览 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、当前状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选行数：{summary['候选行数']}",
        f"- 已确认链路数：{summary['已确认链路数']}",
        f"- 是否三链路已确认：{summary['是否三链路已确认']}",
        f"- 206是否允许采用：{summary['206是否允许采用']}",
        f"- 是否生成可采用预览值：{summary['是否生成可采用预览值']}",
        f"- 当前阻断原因：{summary['当前阻断原因']}",
        "",
        "## 二、预览状态摘录",
        "",
        "| 链路 | 字段 | 状态 |",
        "|---|---|---|",
    ]
    for item in report["候选采用预览行"][:30]:
        lines.append(f"| {item['链路']} | {item['字段']} | {item['预览状态']} |")
    lines.extend(["", "## 三、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path, csv_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选采用预览_打开.bat"
    write_text(bat, "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n' f'start "" "{csv_path}"\r\n')


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "208单股证据核验191候选采用预览"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选采用预览_最新.json"
    latest_md = out_dir / "单股证据核验191候选采用预览_最新.md"
    latest_csv = out_dir / "单股证据核验191候选采用预览_最新.csv"
    write_json(out_dir / f"单股证据核验191候选采用预览_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验191候选采用预览_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_csv(out_dir / f"单股证据核验191候选采用预览_{stamp}.csv", report["候选采用预览行"])
    write_csv(latest_csv, report["候选采用预览行"])
    write_open_bat(root, latest_md, latest_csv)
    print(json.dumps({"状态": "完成", "是否生成可采用预览值": report["汇总"]["是否生成可采用预览值"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
