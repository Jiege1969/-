# -*- coding: utf-8 -*-
"""执行三日巡检样本防伪只读核对。

只读取 59 包台账与 69 包文件，输出核对结果；不写入 59 包，不生成未来样本。
"""

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
READONLY_CHECK_MD = OUTPUT_DIR / "只读核对结果_最新.md"

EXPECTED_FIRST_DAY = "2026-05-08"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    checks = [
        f"- {item['项目']}: {'通过' if item['通过'] else '失败'} - {item['说明']}"
        for item in report["核对项"]
    ]
    return "\n".join(
        [
            "# 三日巡检样本防伪只读核对结果",
            "",
            f"- 核对时间: {report['核对时间']}",
            f"- 通过: {report['通过']}",
            f"- 错误数: {report['错误数']}",
            "",
            "## 核对项",
            "",
            *checks,
        ]
    )


def main() -> int:
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ledger = read_json(SOURCE_LEDGER)
    package = read_json(PACKAGE_JSON)
    card = read_json(NEXTDAY_CARD_JSON)
    rules_doc = read_json(ANTI_FAKE_RULES_JSON)

    samples = ledger.get("自然日样本", [])
    dates = sorted({item.get("样本日期") for item in samples if item.get("样本日期")})
    output_names = [path.name for path in OUTPUT_DIR.glob("*") if path.is_file()]
    future_sample_files = [
        name
        for name in output_names
        if ("第2自然日样本" in name or "第3自然日样本" in name) and "待执行卡" not in name
    ]

    checks = [
        {
            "项目": "59包台账仅有首日样本",
            "通过": dates == [EXPECTED_FIRST_DAY],
            "说明": f"当前自然日样本日期={dates}",
        },
        {
            "项目": "59包三日达标保持false",
            "通过": ledger.get("三日达标") is False,
            "说明": f"三日达标={ledger.get('三日达标')}",
        },
        {
            "项目": "同日重复运行覆盖规则存在",
            "通过": any("同一天重复运行只能覆盖当日样本" in item for item in rules_doc.get("规则", [])),
            "说明": "规则必须声明同日去重覆盖，不增加自然日计数",
        },
        {
            "项目": "第2天日期大于首日",
            "通过": card.get("来源首日样本日期") == EXPECTED_FIRST_DAY and card.get("待执行日期下限", "") > EXPECTED_FIRST_DAY,
            "说明": f"首日={card.get('来源首日样本日期')}，次日下限={card.get('待执行日期下限')}",
        },
        {
            "项目": "未预生成第2/3自然日样本",
            "通过": not future_sample_files
            and package.get("未生成样本声明", {}).get("第2自然日样本") == "未生成"
            and package.get("未生成样本声明", {}).get("第3自然日样本") == "未生成",
            "说明": f"未来样本文件={future_sample_files}",
        },
        {
            "项目": "安全边界均为false",
            "通过": all(value is False for value in package.get("安全边界", {}).values()),
            "说明": "不触发外部系统、不重载服务、不转正式规则",
        },
    ]
    errors = [item for item in checks if not item["通过"]]
    report = {
        "名称": "三日巡检样本防伪只读核对结果",
        "核对时间": checked_at,
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "核对项": checks,
        "错误": errors,
        "读取来源": {
            "59包台账": str(SOURCE_LEDGER),
            "69总包": str(PACKAGE_JSON),
            "次日待执行卡": str(NEXTDAY_CARD_JSON),
            "样本防伪规则": str(ANTI_FAKE_RULES_JSON),
        },
    }
    write_json(READONLY_CHECK_JSON, report)
    write_text(READONLY_CHECK_MD, build_md(report))
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "输出": str(READONLY_CHECK_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
