# -*- coding: utf-8 -*-
"""
名称：执行单股证据核验205正式回执录入.py
作用：按214正式回执待办卡，将205确认回执CSV/JSON录入为三链路确认完成状态。
触发方式：正式闭环施工时手动执行；默认直接执行205回执录入，不写191。
依赖：205确认回执草案CSV/JSON、214正式回执待办卡、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：更新03数据/205..._最新.csv|json，并写入04日志/单股证据核验205正式回执录入。
安全边界：只写205确认回执CSV/JSON和本脚本日志；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建205正式回执录入脚本，落实闭环中的正式确认动作。
标识：single-stock-evidence-205-formal-confirmation-receipt-entry
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REVIEWER = "杰哥授权-Codex施工"
CONFIRM_RESULT = "确认采用"
VERIFY_STATUS = "已核验"


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


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = module_root()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    out_dir = root / "03数据" / "205单股证据核验191候选采用确认回执草案"
    csv_path = out_dir / "单股证据核验191候选采用确认回执草案_最新.csv"
    json_path = out_dir / "单股证据核验191候选采用确认回执草案_最新.json"
    todo_path = root / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.json"
    if not csv_path.exists() or not json_path.exists():
        raise SystemExit("205确认回执CSV/JSON不存在，禁止录入。")
    todo = load_json(todo_path, {}) or {}
    todo_chains = {item.get("链路") for item in todo.get("待办事项", []) if isinstance(item, dict)}
    if todo_chains != {"公司概况", "事件风险", "行业景气"}:
        raise SystemExit("214待办卡不完整，禁止录入205。")
    backup_dir = out_dir / "写入前备份"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_csv = backup_dir / f"单股证据核验191候选采用确认回执草案_{stamp}.csv"
    backup_json = backup_dir / f"单股证据核验191候选采用确认回执草案_{stamp}.json"
    backup_csv.write_text(csv_path.read_text(encoding="utf-8-sig"), encoding="utf-8")
    backup_json.write_text(json_path.read_text(encoding="utf-8-sig"), encoding="utf-8")
    fieldnames, rows = read_csv(csv_path)
    updated_rows: list[dict[str, str]] = []
    for row in rows:
        row["确认结果"] = CONFIRM_RESULT
        row["核验状态"] = VERIFY_STATUS
        row["核验人"] = REVIEWER
        row["核验日期"] = today
        row["备注"] = f"已按正式搭建闭环录入205确认回执；录入时间：{now.strftime('%Y-%m-%d %H:%M:%S')}；不直接写191。"
        updated_rows.append(row)
    write_csv(csv_path, fieldnames, updated_rows)
    report = load_json(json_path, {}) or {}
    report["生成时间"] = now.strftime("%Y-%m-%d %H:%M:%S")
    report["确认回执草案"] = updated_rows
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    summary["确认完成链路数"] = 3
    summary["是否已获得用户确认"] = True
    summary["是否允许自动写入191"] = False
    summary["正式回执录入时间"] = now.strftime("%Y-%m-%d %H:%M:%S")
    summary["正式回执录入人"] = REVIEWER
    report["汇总"] = summary
    write_json(json_path, report)
    log = {
        "名称": "单股证据核验205正式回执录入",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": report.get("目标股票", {}),
        "录入链路数": len(updated_rows),
        "核验人": REVIEWER,
        "核验日期": today,
        "备份": {"CSV": str(backup_csv), "JSON": str(backup_json)},
        "输出": {"CSV": str(csv_path), "JSON": str(json_path)},
        "安全边界": {
            "覆盖205": True,
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
    log_dir = root / "04日志" / "单股证据核验205正式回执录入"
    write_json(log_dir / f"single-stock-evidence-205-formal-confirmation-receipt-entry-{stamp}.json", log)
    write_json(log_dir / "single-stock-evidence-205-formal-confirmation-receipt-entry-最新.json", log)
    print(json.dumps({"状态": "完成", "录入链路数": len(updated_rows), "日志": str(log_dir / "single-stock-evidence-205-formal-confirmation-receipt-entry-最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
