# -*- coding: utf-8 -*-
"""执行三日巡检第2天待执行链路只读核对。

只读取 59 包、69 包和本包输出，写入本包目录下的只读核对结果。
不生成第2天样本，不修改来源包，不触发任何外部系统。
"""

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
READONLY_MD = OUTPUT_DIR / "第2天待执行链路只读核对结果_最新.md"

EXPECTED_FIRST_DAY = "2026-05-08"
EXPECTED_DAY2_LOWER_BOUND = "2026-05-09"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
    future_files: list[str] = []
    if not OUTPUT_DIR.exists():
        return future_files
    for path in OUTPUT_DIR.glob("*"):
        if not path.is_file():
            continue
        name = path.name
        if any(token in name for token in forbidden_tokens) and not any(token in name for token in allowed_tokens):
            future_files.append(name)
    return sorted(future_files)


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# 三日巡检第2天待执行链路只读核对结果",
        "",
        f"- 核对时间: {report['核对时间']}",
        f"- 通过: {report['通过']}",
        f"- 错误数: {report['错误数']}",
        "",
        "## 核对项",
        "",
    ]
    for item in report["核对项"]:
        status = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['项目']}: {status} - {item['说明']}")
    return "\n".join(lines)


def main() -> int:
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ledger_59 = read_json(PACKAGE_59_LEDGER)
    package_69 = read_json(PACKAGE_69_JSON)
    card_69 = read_json(PACKAGE_69_CARD_JSON)
    readonly_69 = read_json(PACKAGE_69_READONLY_JSON)
    package = read_json(PACKAGE_JSON)
    chain = read_json(CHAIN_JSON)
    checklist = read_json(CHECKLIST_JSON)

    dates = sample_dates_from_ledger(ledger_59)
    future_files = find_future_sample_files()
    source_69 = package_69.get("来源确认", {})

    checks = [
        {
            "项目": "59包当前只有首日样本",
            "通过": dates == [EXPECTED_FIRST_DAY],
            "说明": f"当前自然日样本日期={dates}",
        },
        {
            "项目": "59包三日达标保持false",
            "通过": ledger_59.get("三日达标") is False,
            "说明": f"三日达标={ledger_59.get('三日达标')}",
        },
        {
            "项目": "69包确认仍只有首日样本",
            "通过": source_69.get("自然日样本日期") == [EXPECTED_FIRST_DAY],
            "说明": f"69包来源日期={source_69.get('自然日样本日期')}",
        },
        {
            "项目": "69包只读核对为0错误",
            "通过": readonly_69.get("通过") is True and readonly_69.get("错误数") == 0,
            "说明": f"通过={readonly_69.get('通过')}，错误数={readonly_69.get('错误数')}",
        },
        {
            "项目": "待执行日期大于首日",
            "通过": card_69.get("待执行日期下限") == EXPECTED_DAY2_LOWER_BOUND
            and card_69.get("待执行日期下限", "") > EXPECTED_FIRST_DAY
            and chain.get("待执行日期下限") == EXPECTED_DAY2_LOWER_BOUND,
            "说明": f"首日={EXPECTED_FIRST_DAY}，待执行下限={chain.get('待执行日期下限')}",
        },
        {
            "项目": "不能同日增加自然日计数",
            "通过": checklist.get("检查项", [])[3].get("要求") == "同日只能覆盖同日样本，不能新增自然日计数。",
            "说明": "本包仅声明同日覆盖规则，不新增样本。",
        },
        {
            "项目": "不存在未来样本文件",
            "通过": not future_files,
            "说明": f"未来样本文件={future_files}",
        },
        {
            "项目": "本包未声明三日达标",
            "通过": package.get("来源确认", {}).get("三日达标") is False,
            "说明": f"本包来源三日达标={package.get('来源确认', {}).get('三日达标')}",
        },
        {
            "项目": "安全边界全部为false",
            "通过": all(value is False for value in package.get("安全边界", {}).values()),
            "说明": "不触发外部系统、不重载服务、不转正式规则。",
        },
    ]
    errors = [item for item in checks if not item["通过"]]
    report = {
        "名称": "三日巡检第2天待执行链路只读核对结果",
        "核对时间": checked_at,
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "核对项": checks,
        "错误": errors,
        "读取来源": {
            "59包台账": str(PACKAGE_59_LEDGER),
            "69总包": str(PACKAGE_69_JSON),
            "69次日待执行卡": str(PACKAGE_69_CARD_JSON),
            "69只读核对结果": str(PACKAGE_69_READONLY_JSON),
            "73总包": str(PACKAGE_JSON),
            "73链路说明": str(CHAIN_JSON),
            "73防伪检查清单": str(CHECKLIST_JSON),
        },
    }

    write_json(READONLY_JSON, report)
    write_text(READONLY_MD, build_md(report))
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "输出": str(READONLY_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
