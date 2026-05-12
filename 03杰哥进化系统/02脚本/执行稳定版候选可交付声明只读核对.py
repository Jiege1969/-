# -*- coding: utf-8 -*-
"""执行稳定版候选可交付声明只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "58稳定版候选最终回传与可交付声明包" / "稳定版候选最终回传与可交付声明包_最新.json"
OUTPUT_DIR = ROOT / "03数据" / "58稳定版候选最终回传与可交付声明包"
LATEST_JSON = OUTPUT_DIR / "稳定版候选可交付声明只读核对_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版候选可交付声明只读核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evaluate(path: Path) -> tuple[str, Any]:
    if not path.exists():
        return "missing", "证据不存在"
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


def build_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['名称']} | {item['当前结果']} | {item['路径']} |" for item in report["证据核对结果"]]
    return "\n".join(
        [
            "# 稳定版候选可交付声明只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 可交付声明成立：{report['可交付声明成立']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 证据 | 结果 | 路径 |",
            "| --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    checks = []
    for item in asset.get("核心证据", []):
        status, summary = evaluate(Path(item["路径"]))
        checks.append({**item, "当前结果": status, "摘要": summary})
    passed = sum(1 for item in checks if item["当前结果"] == "pass")
    output_ok = all(Path(path).exists() for path in asset.get("输出文件", {}).values())
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    statement_ok = asset.get("可交付声明", {}).get("声明级别") == "稳定版候选可交付"
    delivery_ok = passed == len(checks) and output_ok and safety_ok and statement_ok
    report = {
        "名称": "稳定版候选可交付声明只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if delivery_ok else "blocked",
        "可交付声明成立": delivery_ok,
        "汇总": {"总数": len(checks), "通过": passed, "失败": len(checks) - passed},
        "证据核对结果": checks,
        "附加核对": {
            "输出文件全部存在": output_ok,
            "安全边界全部false": safety_ok,
            "声明级别正确": statement_ok,
        },
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "可交付声明成立": delivery_ok, "通过": passed, "失败": len(checks) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
