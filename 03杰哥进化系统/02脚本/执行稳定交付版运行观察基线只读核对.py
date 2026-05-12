# -*- coding: utf-8 -*-
"""执行稳定交付版运行观察基线只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "77稳定交付版运行观察基线与改进闭环包"

ASSET_JSON = DATA_DIR / "稳定交付版运行观察基线与改进闭环包_最新.json"
LATEST_JSON = DATA_DIR / "稳定交付版运行观察基线只读核对_最新.json"
LATEST_MD = DATA_DIR / "稳定交付版运行观察基线只读核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['存在']} | {item['通过']} | {item['错误']} |"
        for item in report["证据核对"]
    ]
    return "\n".join(
        [
            "# 稳定交付版运行观察基线只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 可进入稳定版运行观察：{report['可进入稳定版运行观察']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 存在 | 通过 | 错误 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 只读边界",
            "",
            "- 本核对只读取 77 包和上游证据产物。",
            "- 不重载 19310/19302，不请求外部系统，不转正式规则。",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    evidence_checks = []
    for item in asset.get("证据", []):
        evidence_checks.append(
            {
                "编号": item.get("编号"),
                "名称": item.get("名称"),
                "存在": item.get("存在") is True and Path(item.get("路径", "")).exists(),
                "通过": item.get("通过") is True,
                "错误": "" if item.get("存在") is True and item.get("通过") is True else "证据未达基线口径",
                "路径": item.get("路径"),
            }
        )

    passed = sum(1 for item in evidence_checks if item["存在"] and item["通过"])
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    status_ok = asset.get("状态") == "stable_delivery_runtime_observation_baseline_ready"
    strategy_ok = "稳定交付版" in asset.get("当前策略", "")
    can_observe = status_ok and strategy_ok and safety_ok and passed == len(evidence_checks) and len(evidence_checks) >= 5

    report = {
        "名称": "稳定交付版运行观察基线只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if can_observe else "blocked",
        "可进入稳定版运行观察": can_observe,
        "汇总": {"总数": len(evidence_checks), "通过": passed, "失败": len(evidence_checks) - passed},
        "安全边界全部关闭": safety_ok,
        "证据核对": evidence_checks,
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(evidence_checks) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if can_observe else 1


if __name__ == "__main__":
    raise SystemExit(main())
