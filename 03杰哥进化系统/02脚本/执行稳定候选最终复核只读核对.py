# -*- coding: utf-8 -*-
"""执行稳定候选最终复核只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "62稳定候选最终复核与日常版收口声明包" / "稳定候选最终复核与日常版收口声明包_最新.json"
LATEST_JSON = ROOT / "03数据" / "62稳定候选最终复核与日常版收口声明包" / "稳定候选最终复核只读核对_最新.json"
LATEST_MD = ROOT / "03数据" / "62稳定候选最终复核与日常版收口声明包" / "稳定候选最终复核只读核对_最新.md"


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
    rows = [f"| {item['编号']} | {item['名称']} | {item['当前结果']} | {item['路径']} |" for item in report["复核结果"]]
    return "\n".join(
        [
            "# 稳定候选最终复核只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 日常版候选收口成立：{report['日常版候选收口成立']}",
            f"- 稳定版候选复核成立：{report['稳定版候选复核成立']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 当前结果 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    results = []
    for item in asset.get("最终复核证据", []):
        status, summary = evaluate(Path(item["路径"]))
        results.append({**item, "当前结果": status, "摘要": summary})
    passed = sum(1 for item in results if item["当前结果"] == "pass")
    output_ok = all(Path(path).exists() for path in asset.get("输出文件", {}).values())
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    daily_ok = asset.get("日常版收口声明", {}).get("声明级别") == "日常可用交付版候选收口"
    all_ok = passed == len(results) and output_ok and safety_ok and daily_ok
    report = {
        "名称": "稳定候选最终复核只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all_ok else "blocked",
        "日常版候选收口成立": all_ok,
        "稳定版候选复核成立": all_ok,
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "复核结果": results,
        "附加核对": {
            "输出文件全部存在": output_ok,
            "安全边界全部false": safety_ok,
            "日常版声明级别正确": daily_ok,
        },
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
