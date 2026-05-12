# -*- coding: utf-8 -*-
"""
名称：执行单股证据核验205回执补入191CSV核验字段.py
作用：在205正式回执确认后，将核验状态、核验人、核验日期补入191人工CSV对应字段。
触发方式：正式闭环施工时手动执行；默认直接执行191 CSV核验字段补入，不写191台账。
依赖：205确认回执CSV、191人工填写CSV表单、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：更新03数据/191...CSV表单，并写入04日志/单股证据核验205回执补入191CSV核验字段。
安全边界：只写191人工CSV表单和本脚本日志；不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建205回执补入191CSV核验字段脚本，补齐198质量闸口需要的人工确认字段。
标识：single-stock-evidence-205-receipt-fill-191-csv-verification-fields
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


FIELDS = ["核验状态", "核验人", "核验日期"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    receipt_csv = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv"
    target_csv = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    _, receipt_rows = read_csv(receipt_csv)
    fieldnames, target_rows = read_csv(target_csv)
    receipt_by_chain = {row.get("链路", ""): row for row in receipt_rows}
    if set(receipt_by_chain) != {"公司概况", "事件风险", "行业景气"}:
        raise SystemExit("205回执三链路不完整，禁止补入191 CSV。")
    for chain, row in receipt_by_chain.items():
        if row.get("确认结果") != "确认采用" or row.get("核验状态") != "已核验" or not row.get("核验人") or not row.get("核验日期"):
            raise SystemExit(f"205回执链路未确认完成：{chain}")
    backup_dir = target_csv.parent / "写入前备份"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"单股证据核验人工填写CSV表单_205核验字段补入前备份_{stamp}.csv"
    backup.write_text(target_csv.read_text(encoding="utf-8-sig"), encoding="utf-8")
    changed = []
    for row in target_rows:
        chain = row.get("链路", "")
        field = row.get("字段", "")
        if field in FIELDS and chain in receipt_by_chain:
            before = row.get("填写值", "")
            after = receipt_by_chain[chain].get(field, "")
            row["填写值"] = after
            if before != after:
                changed.append({"链路": chain, "字段": field, "原值": before, "新值": after})
    write_csv(target_csv, fieldnames, target_rows)
    log = {
        "名称": "单股证据核验205回执补入191CSV核验字段",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "补入字段数": len(changed),
        "备份": str(backup),
        "输出CSV": str(target_csv),
        "变化字段": changed,
        "安全边界": {
            "覆盖191CSV": True,
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
    log_dir = root / "04日志" / "单股证据核验205回执补入191CSV核验字段"
    write_json(log_dir / f"single-stock-evidence-205-receipt-fill-191-csv-verification-fields-{stamp}.json", log)
    write_json(log_dir / "single-stock-evidence-205-receipt-fill-191-csv-verification-fields-最新.json", log)
    print(json.dumps({"状态": "完成", "补入字段数": len(changed), "日志": str(log_dir / "single-stock-evidence-205-receipt-fill-191-csv-verification-fields-最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
