# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验人工填写CSV表单.py
作用：基于191人工填写台账生成可人工填写、机器可读取的CSV表单，并在重复刷新时保留已填写内容。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：03数据/191单股证据核验人工填写台账/单股证据核验人工填写台账_最新.json，旧CSV表单用于保留已填写内容。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验人工填写CSV表单_最新.csv 与 .json；05入口工具/单股证据核验人工填写CSV表单_打开.bat。
安全边界：只读191台账和旧CSV；只写03数据/191单股证据核验人工填写台账和05入口工具；
不联网抓取、不写正式档案、不导入正式模板、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：single-stock-evidence-manual-csv-generate
"""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


CHAINS = ["公司概况", "事件风险", "行业景气"]
FIELDNAMES = ["股票代码", "股票名称", "链路", "字段", "是否必填", "填写值", "填写说明"]


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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "gbk"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except UnicodeDecodeError:
            continue
    return []


def count_filled_values(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if str(row.get("填写值") or "").strip())


def backup_old_csv_if_needed(csv_path: Path, old_rows: list[dict[str, str]], stamp: str) -> Path | None:
    if not csv_path.exists() or count_filled_values(old_rows) <= 0:
        return None
    backup_dir = csv_path.parent / "CSV人工填写备份"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"单股证据核验人工填写CSV表单_重写前备份_{stamp}.csv"
    shutil.copy2(csv_path, backup_path)
    return backup_path


def csv_safe(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def field_hint(chain: str, field: str) -> str:
    if field == "核验状态":
        return "填“已核验”才允许进入192预览；未核验、存疑、待补充都不能放行。"
    if field in {"核验人", "核验日期"}:
        return "填写人工核验责任人和日期，日期建议YYYY-MM-DD。"
    if "URL" in field or "路径" in field:
        return "填写可追溯来源路径或URL；没有可靠来源就先留空。"
    if "来源" in field or "材料" in field:
        return "填写可靠公开资料、公告、财报、研报摘要等可追溯材料。"
    if field.startswith("是否"):
        return "填写“是/否/不确定”，并在摘要或备注中说明依据。"
    if "建议前台处理" in field:
        return "填写对前台结论的处理建议，例如维持、降级观察、暂不采用。"
    if "摘要" in field or "备注" in field:
        return "简要说明人工判断依据、疑点和后续需要继续跟踪的点。"
    if chain == "公司概况":
        return "按可靠来源补全公司基本面事实，不做主观推荐。"
    if chain == "事件风险":
        return "只记录已核验的事件和风险，不确定内容先留空或写入备注。"
    if chain == "行业景气":
        return "按行业指数、价格、订单、政策等来源核验景气判断。"
    return "按可靠来源填写；无证据则留空。"


def build_rows(ledger: dict[str, Any], old_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    target_code = str(target.get("代码") or "")
    old_values = {
        (row.get("链路", ""), row.get("字段", "")): row.get("填写值", "")
        for row in old_rows
        if row.get("链路") and row.get("字段") and str(row.get("股票代码") or "") == target_code
    }
    rows: list[dict[str, str]] = []
    for chain_name in CHAINS:
        chain = ledger.get(chain_name, {}) if isinstance(ledger.get(chain_name), dict) else {}
        fill = chain.get("人工填写", {}) if isinstance(chain.get("人工填写"), dict) else {}
        for field, ledger_value in fill.items():
            key = (chain_name, field)
            preserved = old_values.get(key)
            value = preserved if preserved not in {None, ""} else ledger_value
            rows.append({
                "股票代码": csv_safe(target.get("代码", "")),
                "股票名称": csv_safe(target.get("名称", "")),
                "链路": chain_name,
                "字段": field,
                "是否必填": "否" if field.startswith("人工备注") else "是",
                "填写值": csv_safe(value),
                "填写说明": field_hint(chain_name, field),
            })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_entry_bats(target: Path) -> dict[str, str]:
    root = module_root()
    entry_dir = root / "05入口工具"
    open_bat = entry_dir / "单股证据核验人工填写CSV表单_打开.bat"
    sync_bat = entry_dir / "单股证据核验CSV表单同步到台账_执行.bat"
    preflight_bat = entry_dir / "单股证据核验191完成后预演检查_执行.bat"
    write_text(open_bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    preflight_content = (
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        f'cd /d "{root / "02脚本"}"\r\n'
        'python "执行单股证据核验191完成后预演检查.py"\r\n'
        'pause\r\n'
    )
    write_text(preflight_bat, preflight_content)
    write_text(
        sync_bat,
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        f'cd /d "{root / "02脚本"}"\r\n'
        'echo 为避免误覆盖人工核验流程，本入口已改为先运行197完成后预演检查。\r\n'
        'echo 如预演通过且确认要写入191台账，请手动运行：\r\n'
        'echo python "执行单股证据核验191完成后预演检查.py" --apply-191 --confirm 允许同步CSV到191台账\r\n'
        'python "执行单股证据核验191完成后预演检查.py"\r\n'
        'pause\r\n',
    )
    return {"打开CSV表单": str(open_bat), "197预演检查": str(preflight_bat), "同步入口已转预演": str(sync_bat)}


def build_note(root: Path, csv_path: Path, rows: list[dict[str, str]], old_rows: list[dict[str, str]], backup_path: Path | None) -> dict[str, Any]:
    required = [row for row in rows if row.get("是否必填") == "是"]
    filled = [row for row in required if str(row.get("填写值") or "").strip()]
    old_filled_count = count_filled_values(old_rows)
    return {
        "名称": "单股证据核验人工填写CSV表单",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "CSV表单": str(csv_path),
        "行数": len(rows),
        "必填行数": len(required),
        "已填必填行数": len(filled),
        "旧CSV保护": {
            "旧CSV读取行数": len(old_rows),
            "旧CSV已填值行数": old_filled_count,
            "重复刷新时保留已填写值": True,
            "是否生成重写前备份": backup_path is not None,
            "重写前备份": str(backup_path) if backup_path else "",
        },
        "后续动作": [
            "打开CSV，只编辑“填写值”列。",
            "填完后先运行：python 执行单股证据核验191完成后预演检查.py",
            "预演确认CSV完整且要写入191台账时，才显式运行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm 允许同步CSV到191台账",
            "写入191后继续由192台账同步预览和193模板同步执行闸口判断是否放行。",
        ],
        "安全边界": {
            "写正式档案": False,
            "导入正式模板": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "根目录": str(root),
    }


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    ledger_path = out_dir / "单股证据核验人工填写台账_最新.json"
    csv_path = out_dir / "单股证据核验人工填写CSV表单_最新.csv"
    note_path = out_dir / "单股证据核验人工填写CSV表单_最新.json"
    ledger = load_json(ledger_path, {}) or {}
    if not ledger.get("目标股票", {}).get("代码"):
        raise SystemExit("未找到191人工填写台账，无法生成CSV表单。")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    old_rows = read_csv_rows(csv_path)
    backup_path = backup_old_csv_if_needed(csv_path, old_rows, stamp)
    rows = build_rows(ledger, old_rows)
    write_csv(csv_path, rows)
    note = build_note(root, csv_path, rows, old_rows, backup_path)
    write_json(note_path, note)
    write_csv(out_dir / f"单股证据核验人工填写CSV表单_{ledger['目标股票'].get('代码')}_{stamp}.csv", rows)
    write_json(out_dir / f"单股证据核验人工填写CSV表单_{ledger['目标股票'].get('代码')}_{stamp}.json", note)
    bats = write_entry_bats(csv_path)
    print(json.dumps({
        "状态": "完成",
        "CSV表单": str(csv_path),
        "行数": len(rows),
        "入口工具": bats,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
