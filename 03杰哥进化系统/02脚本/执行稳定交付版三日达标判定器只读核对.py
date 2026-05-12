# -*- coding: utf-8 -*-
"""执行稳定交付版三日达标判定器只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包"

ASSET_JSON = DATA_DIR / "稳定交付版三日达标判定器与样本采集标准包_最新.json"
DECISION_JSON = DATA_DIR / "稳定版三日达标判定结果_最新.json"
CHECK_JSON = DATA_DIR / "稳定版三日达标判定器只读核对_最新.json"
CHECK_MD = DATA_DIR / "稳定版三日达标判定器只读核对_最新.md"


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
            "# 稳定版三日达标判定器只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 三日达标：{report['三日达标']}",
            f"- 通过样本数：{report['不同自然日通过样本数']}",
            f"- 失败数：{report['汇总']['失败']}",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    decision = read_json(DECISION_JSON)
    errors: list[str] = []

    if asset.get("状态") != "stable_delivery_three_day_acceptance_judge_ready":
        errors.append("总包状态不正确")
    if decision.get("是否生成未来样本") is not False:
        errors.append("不得生成未来样本")
    if asset.get("上游摘要", {}).get("防伪验收通过") is not True:
        errors.append("防伪验收必须通过")
    if asset.get("上游摘要", {}).get("防伪未来样本文件数") != 0:
        errors.append("未来样本文件数必须为0")
    if asset.get("上游摘要", {}).get("首日复验验收通过") is not True:
        errors.append("首日复验验收必须通过")
    if asset.get("上游摘要", {}).get("次日闸口验收通过") is not True:
        errors.append("次日闸口验收必须通过")
    if decision.get("不同自然日通过样本数", 0) < 3 and decision.get("三日达标") is not False:
        errors.append("不足3个不同自然日样本时三日达标必须为false")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为false")
    for path_text in asset.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版三日达标判定器只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "blocked",
        "错误": errors,
        "汇总": {"总数": 8, "通过": 8 - len(errors), "失败": len(errors)},
        "三日达标": decision.get("三日达标"),
        "不同自然日通过样本数": decision.get("不同自然日通过样本数"),
        "是否生成未来样本": decision.get("是否生成未来样本"),
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "失败": len(errors), "三日达标": report["三日达标"], "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
