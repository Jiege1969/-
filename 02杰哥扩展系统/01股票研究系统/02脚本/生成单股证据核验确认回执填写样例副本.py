# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验确认回执填写样例副本.py
作用：基于205确认回执草案生成已填写样例副本，用于演练210确认识别逻辑；不覆盖正式205。
触发方式：手动运行、股票系统日常一键运行，或由验证脚本调用。
依赖：205确认回执草案、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/212单股证据核验确认回执填写样例副本/单股证据核验确认回执填写样例副本_最新.json|csv|md。
安全边界：只读205确认回执草案；只写212样例副本；不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建212确认回执填写样例副本，用于低风险验证确认后路径。
标识：single-stock-evidence-confirmation-receipt-filled-example-copy
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


def build_report(root: Path) -> dict[str, Any]:
    source_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    source = load_json(source_path, {}) or {}
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for row in source.get("确认回执草案", []) if isinstance(source.get("确认回执草案"), list) else []:
        copied = {key: str(value or "") for key, value in row.items()}
        copied["确认结果"] = "确认采用"
        copied["核验状态"] = "已核验"
        copied["核验人"] = "样例核验人"
        copied["核验日期"] = today
        copied["备注"] = "样例副本，仅用于验证确认后路径；不得作为正式205回执。"
        rows.append(copied)
    report = {
        "名称": "单股证据核验确认回执填写样例副本",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": source.get("目标股票", {}) if isinstance(source.get("目标股票"), dict) else {},
        "输入文件": {"205确认回执草案": str(source_path)},
        "汇总": {
            "样例链路数": len(rows),
            "是否正式回执": False,
            "是否允许用于写191": False,
            "用途": "仅用于验证210/211确认后路径识别",
        },
        "样例回执": rows,
        "安全边界": {
            "覆盖205": False,
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }
    return report


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    lines = [
        f"# 单股证据核验确认回执填写样例副本 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、说明",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 样例链路数：{report['汇总']['样例链路数']}",
        f"- 是否正式回执：{report['汇总']['是否正式回执']}",
        f"- 是否允许用于写191：{report['汇总']['是否允许用于写191']}",
        "",
        "## 二、样例回执",
        "",
        "| 链路 | 确认结果 | 核验状态 | 核验人 | 核验日期 |",
        "|---|---|---|---|---|",
    ]
    for row in report["样例回执"]:
        lines.append(f"| {row.get('链路')} | {row.get('确认结果')} | {row.get('核验状态')} | {row.get('核验人')} | {row.get('核验日期')} |")
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "212单股证据核验确认回执填写样例副本"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验确认回执填写样例副本_最新.json"
    latest_md = out_dir / "单股证据核验确认回执填写样例副本_最新.md"
    latest_csv = out_dir / "单股证据核验确认回执填写样例副本_最新.csv"
    write_json(out_dir / f"单股证据核验确认回执填写样例副本_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验确认回执填写样例副本_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_csv(out_dir / f"单股证据核验确认回执填写样例副本_{stamp}.csv", report["样例回执"])
    write_csv(latest_csv, report["样例回执"])
    print(json.dumps({"状态": "完成", "样例链路数": report["汇总"]["样例链路数"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
