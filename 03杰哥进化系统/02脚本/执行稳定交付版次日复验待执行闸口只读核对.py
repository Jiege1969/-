# -*- coding: utf-8 -*-
"""执行稳定交付版次日复验待执行闸口只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "83稳定交付版次日复验待执行闸口包"

ASSET_JSON = DATA_DIR / "稳定交付版次日复验待执行闸口包_最新.json"
GATE_JSON = DATA_DIR / "稳定版次日复验待执行闸口_最新.json"
CHECK_JSON = DATA_DIR / "稳定版次日复验待执行闸口只读核对_最新.json"
CHECK_MD = DATA_DIR / "稳定版次日复验待执行闸口只读核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版次日复验待执行闸口只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 当前是否可执行次日复验：{report['当前是否可执行次日复验']}",
            f"- 是否生成次日样本：{report['是否生成次日样本']}",
            f"- 失败数：{report['汇总']['失败']}",
            "",
            "## 只读声明",
            "",
            "- 本核对只读取 83 包，不运行次日复验，不制造自然日样本。",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    gate = read_json(GATE_JSON)
    errors: list[str] = []
    if asset.get("状态") != "stable_delivery_day2_recheck_pending_gate_ready":
        errors.append("总包状态不正确")
    if asset.get("是否生成次日样本") is not False or gate.get("是否生成次日样本") is not False:
        errors.append("不得生成次日样本")
    if asset.get("首日样本日期") >= asset.get("次日最早执行日期"):
        errors.append("次日最早执行日期必须晚于首日样本日期")
    for path_text in asset.get("次日复验执行入口", {}).values():
        if not Path(path_text).exists():
            errors.append(f"复验入口不存在：{path_text}")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("总包安全边界必须全部关闭")
    if not all(value is False for value in gate.get("安全边界", {}).values()):
        errors.append("闸口安全边界必须全部关闭")

    report = {
        "名称": "稳定版次日复验待执行闸口只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "blocked",
        "错误": errors,
        "汇总": {"总数": 6, "通过": 6 - len(errors), "失败": len(errors)},
        "当前是否可执行次日复验": asset.get("当前是否可执行次日复验"),
        "是否生成次日样本": asset.get("是否生成次日样本"),
        "安全边界全部关闭": not errors,
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "失败": len(errors), "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
