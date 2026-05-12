# -*- coding: utf-8 -*-
"""执行稳定候选三日巡检首日样本记录。

只读取本地验收产物并写入自然日样本台账；同一自然日只保留一个样本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "稳定候选补强与三日巡检启动包_最新.json"
LEDGER_JSON = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
LATEST_JSON = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日巡检当日样本记录_最新.json"
LATEST_MD = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日巡检当日样本记录_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evaluate(path: Path) -> tuple[str, Any]:
    if not path.exists():
        return "missing", "产物不存在"
    data = read_json(path)
    if data.get("总体状态") == "pass":
        return "pass", data.get("汇总", {})
    if data.get("通过") is True:
        return "pass", data.get("指标", data.get("汇总", {}))
    if data.get("passed") is True:
        return "pass", data.get("metrics", {})
    return "blocked", data.get("指标", data.get("汇总", {}))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(record: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['当前结果']} | {item['路径']} |"
        for item in record["巡检结果"]
    ]
    return "\n".join(
        [
            "# 三日巡检当日样本记录",
            "",
            f"- 样本日期：{record['样本日期']}",
            f"- 记录时间：{record['记录时间']}",
            f"- 当日状态：{record['当日状态']}",
            f"- 三日达标：{record['三日达标']}",
            f"- 已记录自然日数：{record['已记录自然日数']}",
            "",
            "| 编号 | 名称 | 当前结果 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    today = datetime.now().strftime("%Y-%m-%d")
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []
    for item in asset.get("三日巡检源", []):
        status, summary = evaluate(Path(item["路径"]))
        results.append({**item, "当前结果": status, "摘要": summary})
    passed = sum(1 for item in results if item["当前结果"] == "pass")
    day_passed = passed == len(results) and all(value is False for value in asset.get("安全边界", {}).values())

    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {"名称": "三日只读巡检样本台账", "自然日样本": []}
    samples = [sample for sample in ledger.get("自然日样本", []) if sample.get("样本日期") != today]
    samples.append(
        {
            "样本日期": today,
            "记录时间": now_text,
            "当日状态": "pass" if day_passed else "blocked",
            "巡检源总数": len(results),
            "通过": passed,
            "失败": len(results) - passed,
        }
    )
    samples = sorted(samples, key=lambda item: item["样本日期"])
    valid_days = [sample for sample in samples if sample.get("当日状态") == "pass"]
    three_day_passed = len({sample["样本日期"] for sample in valid_days}) >= 3
    ledger.update({"最后更新时间": now_text, "自然日样本": samples, "三日达标": three_day_passed})
    write_json(LEDGER_JSON, ledger)

    record = {
        "名称": "三日巡检当日样本记录",
        "样本日期": today,
        "记录时间": now_text,
        "当日状态": "pass" if day_passed else "blocked",
        "已记录自然日数": len({sample["样本日期"] for sample in samples}),
        "三日达标": three_day_passed,
        "巡检结果": results,
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, record)
    write_text(LATEST_MD, build_md(record))
    print(json.dumps({"当日状态": record["当日状态"], "已记录自然日数": record["已记录自然日数"], "三日达标": three_day_passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if record["当日状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
