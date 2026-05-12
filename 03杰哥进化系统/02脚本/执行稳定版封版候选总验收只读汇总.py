# -*- coding: utf-8 -*-
"""执行稳定版封版候选总验收只读汇总。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单" / "稳定版封版候选总验收与剩余缺口清单_最新.json"
OUTPUT_DIR = ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单"
LATEST_JSON = OUTPUT_DIR / "稳定版封版候选总验收只读汇总_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版封版候选总验收只读汇总_最新.md"


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
    if data.get("汇总", {}).get("失败") == 0 and data.get("汇总", {}).get("通过", 0) > 0:
        return "pass", data.get("汇总", {})
    return "blocked", data.get("指标", data.get("汇总", {}))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['当前结果']} | {item['路径']} |"
        for item in report["证据检查结果"]
    ]
    return "\n".join(
        [
            "# 稳定版封版候选总验收只读汇总",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 稳定版封版候选成立：{report['稳定版封版候选成立']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 当前结果 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 说明",
            "",
            "- 本汇总只读证据，不修改正式规则，不变更运行配置。",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    checks = []
    for item in asset.get("总验收证据", []):
        status, summary = evaluate(Path(item["路径"]))
        checks.append({**item, "当前结果": status, "摘要": summary})
    passed = sum(1 for item in checks if item["当前结果"] == "pass")
    gaps_blocking = [item for item in asset.get("剩余缺口", []) if item.get("是否阻断稳定版候选") is True]
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    candidate_ok = passed == len(checks) and not gaps_blocking and safety_ok
    report = {
        "名称": "稳定版封版候选总验收只读汇总",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if candidate_ok else "blocked",
        "稳定版封版候选成立": candidate_ok,
        "汇总": {"总数": len(checks), "通过": passed, "失败": len(checks) - passed},
        "阻断缺口": gaps_blocking,
        "证据检查结果": checks,
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "候选成立": candidate_ok, "通过": passed, "失败": len(checks) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
