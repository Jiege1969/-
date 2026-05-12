# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选采用确认回执草案.py
作用：基于204质量预演，把剩余人工动作压缩为三条链路的候选采用确认回执草案，不写原191。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：204候选采用后质量预演、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/205单股证据核验191候选采用确认回执草案/单股证据核验191候选采用确认回执草案_最新.json|csv|md。
安全边界：只读204质量预演；只写205确认回执草案；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建205候选采用确认回执草案，把剩余人工确认压缩为三条链路确认。
创建/修改记录：2026-05-03 增加已录入回执保留机制，避免日常一键刷新冲掉正式205确认。
标识：single-stock-evidence-191-candidate-adoption-confirmation-draft
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


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["链路", "候选可补足字段数", "候选后仍缺必填字段", "确认问题", "确认结果", "核验状态", "核验人", "核验日期", "备注"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def positive_row(row: dict[str, str]) -> bool:
    return (
        str(row.get("确认结果") or "").strip() in {"确认", "同意", "采用", "已确认", "确认采用", "是"}
        and str(row.get("核验状态") or "").strip() == "已核验"
        and bool(str(row.get("核验人") or "").strip())
        and bool(str(row.get("核验日期") or "").strip())
    )


def build_report(root: Path) -> dict[str, Any]:
    preview_path = root / "03数据" / "204单股证据核验191候选采用后质量预演" / "单股证据核验191候选采用后质量预演_最新.json"
    latest_csv = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv"
    preview = load_json(preview_path, {}) or {}
    existing_rows = {row.get("链路", ""): row for row in read_csv_rows(latest_csv)}
    chain_stats = preview.get("链路预演统计", {}) if isinstance(preview.get("链路预演统计"), dict) else {}
    today = datetime.now().strftime("%Y-%m-%d")
    rows: list[dict[str, str]] = []
    for chain in ["公司概况", "事件风险", "行业景气"]:
        stats = chain_stats.get(chain, {}) if isinstance(chain_stats.get(chain), dict) else {}
        existing = existing_rows.get(chain, {})
        missing = stats.get("仍缺必填字段", [])
        if not isinstance(missing, list):
            missing = []
        rows.append({
            "链路": chain,
            "候选可补足字段数": str(stats.get("候选填入字段数") or 0),
            "候选后仍缺必填字段": "、".join(str(item) for item in missing),
            "确认问题": f"是否确认采用系统候选值补足{chain}链路，并将核验状态/核验人/核验日期作为人工确认信息写入191？",
            "确认结果": str(existing.get("确认结果") or ""),
            "核验状态": str(existing.get("核验状态") or ""),
            "核验人": str(existing.get("核验人") or ""),
            "核验日期": str(existing.get("核验日期") or ""),
            "备注": str(existing.get("备注") or f"建议确认后填写；日期参考：{today}；未确认前不得自动写原191。"),
        })
    confirmed_count = sum(1 for row in rows if positive_row(row))
    return {
        "名称": "单股证据核验191候选采用确认回执草案",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": preview.get("目标股票", {}),
        "输入文件": {"204候选采用后质量预演": str(preview_path)},
        "汇总": {
            "确认链路数": len(rows),
            "候选可补足字段数": int((preview.get("汇总", {}) or {}).get("候选可补足字段数") or 0),
            "候选后仍缺必填字段数": int((preview.get("汇总", {}) or {}).get("候选后仍缺必填字段数") or 0),
            "是否允许自动写入191": False,
            "确认完成链路数": confirmed_count,
            "是否已获得用户确认": confirmed_count == 3,
            "是否保留既有回执": bool(existing_rows),
        },
        "确认回执草案": rows,
        "使用原则": [
            "本草案只把剩余人工确认压缩为三条链路回执，不代表已经确认。",
            "确认结果、核验状态、核验人、核验日期必须由用户或受控流程明确给出。",
            "未获得确认前，不得把候选值写入原191 CSV。",
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
        f"# 单股证据核验191候选采用确认回执草案 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 确认链路数：{summary['确认链路数']}",
        f"- 候选可补足字段数：{summary['候选可补足字段数']}",
        f"- 候选后仍缺必填字段数：{summary['候选后仍缺必填字段数']}",
        f"- 是否允许自动写入191：{summary['是否允许自动写入191']}",
        f"- 是否已获得用户确认：{summary['是否已获得用户确认']}",
        "",
        "## 二、确认回执草案",
        "",
        "| 链路 | 候选可补足字段数 | 候选后仍缺必填字段 | 确认问题 |",
        "|---|---:|---|---|",
    ]
    for item in report["确认回执草案"]:
        lines.append(f"| {item['链路']} | {item['候选可补足字段数']} | {item['候选后仍缺必填字段']} | {item['确认问题']} |")
    lines.extend(["", "## 三、使用原则", ""])
    for item in report["使用原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path, csv_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选采用确认回执草案_打开.bat"
    content = "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n' f'start "" "{csv_path}"\r\n'
    write_text(bat, content)


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "205单股证据核验191候选采用确认回执草案"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选采用确认回执草案_最新.json"
    latest_md = out_dir / "单股证据核验191候选采用确认回执草案_最新.md"
    latest_csv = out_dir / "单股证据核验191候选采用确认回执草案_最新.csv"
    markdown = build_markdown(report)
    write_json(out_dir / f"单股证据核验191候选采用确认回执草案_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(out_dir / f"单股证据核验191候选采用确认回执草案_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_csv(out_dir / f"单股证据核验191候选采用确认回执草案_{stamp}.csv", report["确认回执草案"])
    write_csv(latest_csv, report["确认回执草案"])
    write_open_bat(root, latest_md, latest_csv)
    print(json.dumps({"状态": "完成", "汇总": report["汇总"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
