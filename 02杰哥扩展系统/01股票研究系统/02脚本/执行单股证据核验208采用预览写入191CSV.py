# -*- coding: utf-8 -*-
"""
名称：执行单股证据核验208采用预览写入191CSV.py
作用：在205确认和208采用预览放行后，把208预览填写值写入191人工CSV的填写值列。
触发方式：正式闭环施工时手动执行；默认直接执行191 CSV候选采用，不写191台账。
依赖：208候选采用预览CSV/JSON、191人工填写CSV表单、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：更新03数据/191...CSV表单，并写入04日志/单股证据核验208采用预览写入191CSV。
安全边界：只写191人工CSV表单和本脚本日志；不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建208采用预览写入191CSV脚本，将候选采用从预览推进到正式CSV填写层。
标识：single-stock-evidence-208-adoption-preview-apply-to-191-csv
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


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        str(row.get("股票代码") or ""),
        str(row.get("股票名称") or ""),
        str(row.get("链路") or ""),
        str(row.get("字段") or ""),
    )


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    preview_json = root / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.json"
    preview_csv = root / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.csv"
    target_csv = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    report = load_json(preview_json, {}) or {}
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    if summary.get("是否生成可采用预览值") is not True:
        raise SystemExit("208未生成可采用预览值，禁止写入191 CSV。")
    preview_fields, preview_rows = read_csv(preview_csv)
    target_fields, target_rows = read_csv(target_csv)
    value_map = {key(row): str(row.get("预览填写值") or "") for row in preview_rows if str(row.get("预览填写值") or "").strip()}
    if not value_map:
        raise SystemExit("208预览填写值为空，禁止写入191 CSV。")
    backup_dir = target_csv.parent / "写入前备份"
    backup = backup_dir / f"单股证据核验人工填写CSV表单_205确认采用前备份_{stamp}.csv"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(target_csv.read_text(encoding="utf-8-sig"), encoding="utf-8")
    changed = []
    for row in target_rows:
        row_key = key(row)
        if row_key in value_map:
            before = str(row.get("填写值") or "")
            after = value_map[row_key]
            row["填写值"] = after
            if before != after:
                changed.append({"链路": row.get("链路"), "字段": row.get("字段"), "原值长度": len(before), "新值长度": len(after)})
    write_csv(target_csv, target_fields, target_rows)
    log = {
        "名称": "单股证据核验208采用预览写入191CSV",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": report.get("目标股票", {}),
        "写入字段数": len(changed),
        "备份": str(backup),
        "输出CSV": str(target_csv),
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
        "变化字段": changed,
    }
    log_dir = root / "04日志" / "单股证据核验208采用预览写入191CSV"
    write_json(log_dir / f"single-stock-evidence-208-adoption-preview-apply-to-191-csv-{stamp}.json", log)
    write_json(log_dir / "single-stock-evidence-208-adoption-preview-apply-to-191-csv-最新.json", log)
    print(json.dumps({"状态": "完成", "写入字段数": len(changed), "日志": str(log_dir / "single-stock-evidence-208-adoption-preview-apply-to-191-csv-最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
