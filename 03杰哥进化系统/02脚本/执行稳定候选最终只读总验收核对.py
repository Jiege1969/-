# -*- coding: utf-8 -*-
"""执行稳定候选最终只读总验收核对。

仅读取 63 号收口包中登记的证据文件，按既有 JSON 结果判定是否通过。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
PACKAGE_DIR = ROOT / "03数据" / "63稳定候选最终只读总验收与收口回传包"
ASSET_JSON = PACKAGE_DIR / "稳定候选最终只读总验收与收口回传包_最新.json"
LATEST_JSON = PACKAGE_DIR / "稳定候选最终只读总验收核对_最新.json"
LATEST_MD = PACKAGE_DIR / "稳定候选最终只读总验收核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def get_error_count(data: dict[str, Any]) -> int:
    if isinstance(data.get("错误数"), int):
        return data["错误数"]
    if isinstance(data.get("错误"), list):
        return len(data["错误"])
    metrics = data.get("指标")
    if isinstance(metrics, dict) and isinstance(metrics.get("错误数"), int):
        return metrics["错误数"]
    summary = data.get("汇总")
    if isinstance(summary, dict):
        if isinstance(summary.get("失败"), int):
            return summary["失败"]
        if isinstance(summary.get("错误数"), int):
            return summary["错误数"]
    return 0


def is_passed(item: dict[str, Any], data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    category = item.get("类别")
    error_count = get_error_count(data)
    metrics = data.get("指标", data.get("汇总", {}))

    if category == "三日首日样本":
        ok = data.get("当日状态") == "pass" and data.get("已记录自然日数", 0) >= 1 and error_count == 0
        summary = {
            "当日状态": data.get("当日状态"),
            "已记录自然日数": data.get("已记录自然日数"),
            "三日达标": data.get("三日达标"),
            "错误数": error_count,
        }
        return ok, summary

    if data.get("通过") is True and error_count == 0:
        return True, metrics
    if data.get("总体状态") == "pass" and error_count == 0:
        return True, metrics
    if data.get("passed") is True and error_count == 0:
        return True, data.get("metrics", metrics)

    return False, metrics if isinstance(metrics, dict) else {"摘要": metrics}


def evaluate_evidence(item: dict[str, Any]) -> dict[str, Any]:
    path = Path(item["路径"])
    if not path.exists():
        return {**item, "存在": False, "当前结果": "missing", "摘要": "证据文件不存在"}
    data = read_json(path)
    passed, summary = is_passed(item, data)
    return {**item, "存在": True, "当前结果": "pass" if passed else "blocked", "摘要": summary}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['类别']} | {item['名称']} | {item['当前结果']} | {item['路径']} |"
        for item in report["核对结果"]
    ]
    return "\n".join(
        [
            "# 稳定候选最终只读总验收核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            f"- 失败：{report['汇总']['失败']}",
            "",
            "| 编号 | 类别 | 名称 | 当前结果 | 路径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    results = [evaluate_evidence(item) for item in asset.get("证据清单", [])]
    passed_count = sum(1 for item in results if item["当前结果"] == "pass")
    output_ok = all(Path(path).exists() for path in asset.get("输出文件", {}).values())
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    all_ok = passed_count == len(results) and len(results) >= 7 and output_ok and safety_ok

    report = {
        "名称": "稳定候选最终只读总验收核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all_ok else "blocked",
        "汇总": {"总数": len(results), "通过": passed_count, "失败": len(results) - passed_count, "错误数": len(results) - passed_count},
        "核对结果": results,
        "附加核对": {
            "输出文件全部存在": output_ok,
            "安全边界全部为false": safety_ok,
            "证据数量不少于7": len(results) >= 7,
        },
        "安全边界": asset.get("安全边界", {}),
    }

    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed_count, "失败": len(results) - passed_count, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
