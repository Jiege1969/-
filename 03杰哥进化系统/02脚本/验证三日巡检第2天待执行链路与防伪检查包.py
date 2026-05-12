# -*- coding: utf-8 -*-
"""验证三日巡检第2天待执行链路与防伪检查包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_ROOT = EVOLUTION_ROOT / "03数据"

PACKAGE_59_LEDGER = DATA_ROOT / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
PACKAGE_69_DIR = DATA_ROOT / "69三日巡检样本防伪与次日待执行卡包"
PACKAGE_69_JSON = PACKAGE_69_DIR / "三日巡检样本防伪与次日待执行卡包_最新.json"
PACKAGE_69_CARD_JSON = PACKAGE_69_DIR / "次日待执行卡_最新.json"
PACKAGE_69_READONLY_JSON = PACKAGE_69_DIR / "只读核对结果_最新.json"

OUTPUT_DIR = DATA_ROOT / "73三日巡检第2天待执行链路与防伪检查包"
PACKAGE_JSON = OUTPUT_DIR / "三日巡检第2天待执行链路与防伪检查包_最新.json"
CHAIN_JSON = OUTPUT_DIR / "第2天待执行链路说明_最新.json"
CHECKLIST_JSON = OUTPUT_DIR / "第2天防伪检查清单_最新.json"
READONLY_JSON = OUTPUT_DIR / "第2天待执行链路只读核对结果_最新.json"

LOG_DIR = EVOLUTION_ROOT / "04日志" / "三日巡检第2天待执行链路与防伪检查包验收"
LATEST_LOG = LOG_DIR / "three-day-patrol-day2-pending-chain-verify-最新.json"

EXPECTED_FIRST_DAY = "2026-05-08"
EXPECTED_DAY2_LOWER_BOUND = "2026-05-09"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sample_dates_from_ledger(ledger: dict[str, Any]) -> list[str]:
    return sorted({item.get("样本日期") for item in ledger.get("自然日样本", []) if item.get("样本日期")})


def find_future_sample_files() -> list[str]:
    forbidden_tokens = [
        "第2自然日样本",
        "第3自然日样本",
        "第2天样本",
        "第3天样本",
        "day2-sample",
        "day3-sample",
    ]
    allowed_tokens = ["待执行", "链路", "防伪", "检查", "核对", "说明", "清单", "包"]
    found: list[str] = []
    if not OUTPUT_DIR.exists():
        return found
    for path in OUTPUT_DIR.glob("*"):
        if path.is_file() and any(token in path.name for token in forbidden_tokens) and not any(
            token in path.name for token in allowed_tokens
        ):
            found.append(path.name)
    return sorted(found)


def main() -> int:
    errors: list[str] = []
    required_files = [
        PACKAGE_59_LEDGER,
        PACKAGE_69_JSON,
        PACKAGE_69_CARD_JSON,
        PACKAGE_69_READONLY_JSON,
        PACKAGE_JSON,
        CHAIN_JSON,
        CHECKLIST_JSON,
        READONLY_JSON,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"必需文件不存在: {path}")

    ledger_59 = read_json(PACKAGE_59_LEDGER) if PACKAGE_59_LEDGER.exists() else {}
    package_69 = read_json(PACKAGE_69_JSON) if PACKAGE_69_JSON.exists() else {}
    card_69 = read_json(PACKAGE_69_CARD_JSON) if PACKAGE_69_CARD_JSON.exists() else {}
    readonly_69 = read_json(PACKAGE_69_READONLY_JSON) if PACKAGE_69_READONLY_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    chain = read_json(CHAIN_JSON) if CHAIN_JSON.exists() else {}
    checklist = read_json(CHECKLIST_JSON) if CHECKLIST_JSON.exists() else {}
    readonly = read_json(READONLY_JSON) if READONLY_JSON.exists() else {}

    dates = sample_dates_from_ledger(ledger_59)
    source_69 = package_69.get("来源确认", {})
    future_files = find_future_sample_files()

    if dates != [EXPECTED_FIRST_DAY]:
        errors.append(f"59包台账必须仅有首日样本 {EXPECTED_FIRST_DAY}，当前={dates}")
    if ledger_59.get("三日达标") is not False:
        errors.append("59包台账三日达标必须为 false")
    if source_69.get("自然日样本日期") != [EXPECTED_FIRST_DAY]:
        errors.append("69包来源确认必须仅有首日样本 2026-05-08")
    if source_69.get("三日达标") is not False:
        errors.append("69包来源确认三日达标必须为 false")
    if card_69.get("待执行日期下限") != EXPECTED_DAY2_LOWER_BOUND:
        errors.append("69包次日待执行日期下限必须为 2026-05-09")
    if readonly_69.get("通过") is not True or readonly_69.get("错误数") != 0:
        errors.append("69包只读核对必须通过且错误数为 0")
    if package.get("来源确认", {}).get("自然日样本日期") != [EXPECTED_FIRST_DAY]:
        errors.append("73包来源确认必须仅有首日样本")
    if package.get("来源确认", {}).get("三日达标") is not False:
        errors.append("73包来源确认三日达标必须为 false")
    if chain.get("待执行日期下限") != EXPECTED_DAY2_LOWER_BOUND or chain.get("待执行日期下限", "") <= EXPECTED_FIRST_DAY:
        errors.append("73链路说明待执行日期必须大于首日，且下限为 2026-05-09")
    if "不生成第2天样本" not in chain.get("本包输出性质", ""):
        errors.append("73链路说明必须声明不生成第2天样本")
    if package.get("样本生成声明", {}).get("第2自然日样本", "").startswith("未生成") is not True:
        errors.append("73包必须声明第2自然日样本未生成")
    if package.get("样本生成声明", {}).get("第3自然日样本") != "未生成":
        errors.append("73包必须声明第3自然日样本未生成")
    if readonly.get("通过") is not True or readonly.get("错误数") != 0:
        errors.append("73只读核对必须通过且错误数为 0")
    if future_files:
        errors.append(f"发现疑似未来样本文件: {future_files}")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("73包安全边界必须全部为 false")
    if not checklist.get("检查项"):
        errors.append("73防伪检查清单不能为空")

    report = {
        "名称": "三日巡检第2天待执行链路与防伪检查包验收",
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "59包自然日样本数": len(dates),
            "59包自然日样本日期": dates,
            "59包三日达标": ledger_59.get("三日达标"),
            "69包待执行日期下限": card_69.get("待执行日期下限"),
            "69包只读核对错误数": readonly_69.get("错误数"),
            "73包待执行日期下限": chain.get("待执行日期下限"),
            "73只读核对错误数": readonly.get("错误数"),
            "未来样本文件数": len(future_files),
        },
        "读取文件": [str(path) for path in required_files],
    }
    write_json(LATEST_LOG, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
