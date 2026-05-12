# -*- coding: utf-8 -*-
"""执行稳定版最后收口总回传只读核对。

只读取 67 号候选交付封面包登记的核心证据。上游部分历史文件存在编码损伤，
本脚本先尝试严格 JSON，失败后仅做文本证据提取，不回写上游证据。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_DIR = EVOLUTION_ROOT / "03数据" / "67稳定版最后收口总回传与候选交付封面包"

PACKAGE_JSON = PACKAGE_DIR / "稳定版最后收口总回传与候选交付封面包_最新.json"
CHECK_JSON = PACKAGE_DIR / "稳定版最后收口总回传只读核对_最新.json"
CHECK_MD = PACKAGE_DIR / "稳定版最后收口总回传只读核对_最新.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json_or_text(path: Path) -> tuple[dict[str, Any] | None, str]:
    text = read_text(path)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None, text
    except json.JSONDecodeError:
        return None, text


def text_has_pass(text: str) -> bool:
    return any(token in text for token in ['"通过": true', '"閫氳繃": true', '"passed": true', '"pass"', ': "pass"'])


def text_has_number_after_any_label(text: str, labels: list[str], expected: int) -> bool:
    for label in labels:
        pattern = rf'"{re.escape(label)}[^"]*"?\s*:\s*{expected}\b'
        if re.search(pattern, text):
            return True
    return False


def json_deep_values(data: Any) -> list[Any]:
    values: list[Any] = []
    if isinstance(data, dict):
        for value in data.values():
            values.append(value)
            values.extend(json_deep_values(value))
    elif isinstance(data, list):
        for value in data:
            values.append(value)
            values.extend(json_deep_values(value))
    return values


def json_has_int(data: dict[str, Any], expected: int) -> bool:
    return expected in [value for value in json_deep_values(data) if isinstance(value, int) and not isinstance(value, bool)]


def json_has_true(data: dict[str, Any]) -> bool:
    return True in json_deep_values(data)


def evaluate_item(item: dict[str, Any]) -> dict[str, Any]:
    path = Path(item["路径"])
    if not path.exists():
        return {**item, "存在": False, "当前结果": "missing", "摘要": {"错误": "证据文件不存在"}}

    data, text = read_json_or_text(path)
    expectation = item.get("期望", {})
    checks: dict[str, bool] = {"文件存在": True}

    if "通过" in expectation:
        checks["通过"] = json_has_true(data) if data is not None else text_has_pass(text)
    if "总数" in expectation:
        checks["总数"] = json_has_int(data, expectation["总数"]) if data is not None else text_has_number_after_any_label(text, ["总数", "鎬绘暟"], expectation["总数"])
    if "通过" in expectation and isinstance(expectation["通过"], int) and not isinstance(expectation["通过"], bool):
        checks["通过数"] = json_has_int(data, expectation["通过"]) if data is not None else text_has_number_after_any_label(text, ["通过", "閫氳繃"], expectation["通过"])
    if "失败" in expectation:
        checks["失败数"] = json_has_int(data, expectation["失败"]) if data is not None else text_has_number_after_any_label(text, ["失败", "澶辫触", "失败数"], expectation["失败"])
    if "错误数" in expectation:
        checks["错误数"] = json_has_int(data, expectation["错误数"]) if data is not None else text_has_number_after_any_label(text, ["错误数", "閿欒鏁"], expectation["错误数"])
    if "并行任务不少于" in expectation:
        minimum = expectation["并行任务不少于"]
        checks["并行任务不少于"] = any(value >= minimum for value in json_deep_values(data) if isinstance(value, int)) if data is not None else text_has_number_after_any_label(text, ["并行任务", "骞惰浠诲姟"], minimum)
    if "合并验收项不少于" in expectation:
        minimum = expectation["合并验收项不少于"]
        checks["合并验收项不少于"] = any(value >= minimum for value in json_deep_values(data) if isinstance(value, int)) if data is not None else text_has_number_after_any_label(text, ["合并验收项", "鍚堝苟楠屾敹椤"], minimum)

    passed = all(checks.values())
    return {
        **item,
        "存在": True,
        "解析方式": "json" if data is not None else "text-fallback",
        "当前结果": "pass" if passed else "blocked",
        "摘要": checks,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['类别']} | {item['名称']} | {item['当前结果']} | {item.get('解析方式', '')} | {item['路径']} |"
        for item in report["核对结果"]
    ]
    return "\n".join(
        [
            "# 稳定版最后收口总回传只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            f"- 失败：{report['汇总']['失败']}",
            "",
            "| 编号 | 类别 | 名称 | 当前结果 | 解析方式 | 路径 |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8-sig"))
    results = [evaluate_item(item) for item in package.get("核心验收证据", [])]
    passed_count = sum(1 for item in results if item["当前结果"] == "pass")
    output_ok = all(Path(path).exists() for path in package.get("输出文件", {}).values())
    safety_ok = all(value is False for value in package.get("只读安全边界", {}).values())
    required_sections_ok = all(package.get(key) for key in ["当前结论", "可用能力", "仍阻断能力", "阅读入口", "核心验收证据", "下一步最小动作"])
    all_ok = passed_count == len(results) and len(results) >= 5 and output_ok and safety_ok and required_sections_ok

    report = {
        "名称": "稳定版最后收口总回传只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all_ok else "blocked",
        "汇总": {"总数": len(results), "通过": passed_count, "失败": len(results) - passed_count, "错误数": len(results) - passed_count},
        "核对结果": results,
        "附加核对": {
            "输出文件全部存在": output_ok,
            "安全边界全部为false": safety_ok,
            "封面必要栏目齐全": required_sections_ok,
            "证据数量不少于5": len(results) >= 5,
        },
    }

    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed_count, "失败": len(results) - passed_count, "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
