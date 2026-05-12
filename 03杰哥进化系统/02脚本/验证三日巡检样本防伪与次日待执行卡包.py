# -*- coding: utf-8 -*-
"""验证三日巡检样本防伪与次日待执行卡包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SOURCE_LEDGER = EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "69三日巡检样本防伪与次日待执行卡包"
PACKAGE_JSON = OUTPUT_DIR / "三日巡检样本防伪与次日待执行卡包_最新.json"
NEXTDAY_CARD_JSON = OUTPUT_DIR / "次日待执行卡_最新.json"
ANTI_FAKE_RULES_JSON = OUTPUT_DIR / "样本防伪规则_最新.json"
READONLY_CHECK_JSON = OUTPUT_DIR / "只读核对结果_最新.json"

LOG_DIR = EVOLUTION_ROOT / "04日志" / "三日巡检样本防伪与次日待执行卡包验收"
LATEST_LOG = LOG_DIR / "three-day-patrol-anti-fake-nextday-card-verify-最新.json"

EXPECTED_FIRST_DAY = "2026-05-08"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    required_files = [SOURCE_LEDGER, PACKAGE_JSON, NEXTDAY_CARD_JSON, ANTI_FAKE_RULES_JSON, READONLY_CHECK_JSON]
    for path in required_files:
        if not path.exists():
            errors.append(f"必需文件不存在: {path}")

    ledger = read_json(SOURCE_LEDGER) if SOURCE_LEDGER.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    card = read_json(NEXTDAY_CARD_JSON) if NEXTDAY_CARD_JSON.exists() else {}
    rules_doc = read_json(ANTI_FAKE_RULES_JSON) if ANTI_FAKE_RULES_JSON.exists() else {}
    readonly_check = read_json(READONLY_CHECK_JSON) if READONLY_CHECK_JSON.exists() else {}

    samples = ledger.get("自然日样本", [])
    dates = sorted({item.get("样本日期") for item in samples if item.get("样本日期")})
    if dates != [EXPECTED_FIRST_DAY]:
        errors.append(f"59包台账必须仅有 {EXPECTED_FIRST_DAY} 一个自然日样本，当前={dates}")
    if ledger.get("三日达标") is not False:
        errors.append("59包台账三日达标必须为 false")
    if package.get("当前允许三日达标") is not False:
        errors.append("69总包当前允许三日达标必须为 false")
    if card.get("来源首日样本日期") != EXPECTED_FIRST_DAY:
        errors.append("次日卡来源首日样本日期不正确")
    if not (card.get("待执行日期下限", "") > EXPECTED_FIRST_DAY):
        errors.append("次日卡待执行日期下限必须大于当前首日")
    if card.get("样本生成状态") != "未生成，仅待执行":
        errors.append("次日卡不得被标记为已生成样本")
    if package.get("未生成样本声明", {}).get("第2自然日样本") != "未生成":
        errors.append("第2自然日样本声明必须为未生成")
    if package.get("未生成样本声明", {}).get("第3自然日样本") != "未生成":
        errors.append("第3自然日样本声明必须为未生成")
    if not any("同一天重复运行只能覆盖当日样本" in item for item in rules_doc.get("规则", [])):
        errors.append("样本防伪规则缺少同日覆盖去重口径")
    if not any("不能提前生成占位样本" in item for item in rules_doc.get("规则", [])):
        errors.append("样本防伪规则缺少禁止预生成第2/3天样本口径")
    if readonly_check.get("错误数") != 0 or readonly_check.get("通过") is not True:
        errors.append("只读核对结果必须通过且错误数为0")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")

    future_sample_files = [
        path.name
        for path in OUTPUT_DIR.glob("*")
        if path.is_file()
        and ("第2自然日样本" in path.name or "第3自然日样本" in path.name)
        and "待执行卡" not in path.name
    ]
    if future_sample_files:
        errors.append(f"发现疑似预生成未来样本文件: {future_sample_files}")

    report = {
        "名称": "三日巡检样本防伪与次日待执行卡包验收",
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "59包自然日样本数": len(dates),
            "59包自然日样本日期": dates,
            "59包三日达标": ledger.get("三日达标"),
            "次日待执行日期下限": card.get("待执行日期下限"),
            "只读核对错误数": readonly_check.get("错误数"),
            "未来样本文件数": len(future_sample_files),
        },
        "读取文件": [str(path) for path in required_files],
    }
    write_json(LATEST_LOG, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
