# -*- coding: utf-8 -*-
"""执行稳定版候选正式封版申请草案只读核对。

只读取已生成的草案包与四类上游证据，不执行正式封版，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "71稳定版候选正式封版申请草案与最终交付封面收紧包"

ASSET_JSON = OUTPUT_DIR / "稳定版候选正式封版申请草案与最终交付封面收紧包_最新.json"
LATEST_JSON = OUTPUT_DIR / "稳定版候选封版申请草案只读核对_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版候选封版申请草案只读核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def nested_get(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def evaluate_evidence(item: dict[str, Any]) -> dict[str, Any]:
    path = Path(item["路径"])
    result = {
        "编号": item["编号"],
        "名称": item["名称"],
        "路径": item["路径"],
        "存在": path.exists(),
        "通过": False,
        "摘要": {},
        "错误": "",
    }
    if not path.exists():
        result["错误"] = "证据文件不存在"
        return result

    data = read_json(path)
    expected = item.get("期望状态值")
    field = item.get("期望状态字段")
    actual = data.get(field)
    result["摘要"] = {"期望字段": field, "期望值": expected, "实际值": actual}
    result["通过"] = actual == expected

    if item["名称"] == "自主巡检快照":
        summary = data.get("汇总", {})
        result["摘要"]["汇总"] = summary
        result["通过"] = result["通过"] and summary.get("失败") == 0
    elif item["名称"] == "第二轮并行合并验收":
        metrics = data.get("指标", {})
        result["摘要"]["指标"] = metrics
        result["通过"] = result["通过"] and metrics.get("错误数") == 0
    else:
        safety = data.get("安全边界", {})
        result["摘要"]["安全边界false"] = all(value is False for value in safety.values()) if safety else None
        if safety:
            result["通过"] = result["通过"] and all(value is False for value in safety.values())

    if not result["通过"]:
        result["错误"] = "证据状态未达申请草案核对口径"
    return result


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['存在']} | {item['通过']} | {item['错误']} | {item['路径']} |"
        for item in report["核对结果"]
    ]
    return "\n".join(
        [
            "# 稳定版候选封版申请草案只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 可提交申请草案：{report['可提交申请草案']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 存在 | 通过 | 错误 | 路径 |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 只读声明",
            "",
            "- 本核对只读取稳定版最后收口封面、稳定候选最终复核、第二轮并行合并验收、自主巡检快照。",
            "- 本核对不正式封版、不转正式规则、不触发外部系统。",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    checks = [evaluate_evidence(item) for item in asset.get("当前证据", [])]
    passed = sum(1 for item in checks if item["通过"])
    prohibited_ok = all(value is False for value in asset.get("禁止自动执行项", {}).values())
    draft_ok = asset.get("状态") == "formal_freeze_request_draft_ready"
    candidate_ok = draft_ok and prohibited_ok and passed == len(checks) and len(checks) >= 4

    report = {
        "名称": "稳定版候选封版申请草案只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if candidate_ok else "blocked",
        "可提交申请草案": candidate_ok,
        "草案性质": asset.get("草案性质"),
        "汇总": {"总数": len(checks), "通过": passed, "失败": len(checks) - passed},
        "禁止自动执行项全部关闭": prohibited_ok,
        "核对结果": checks,
        "仍需总管确认项": asset.get("仍需总管确认项", []),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(checks) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if candidate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
