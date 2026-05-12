# -*- coding: utf-8 -*-
"""执行稳定版试运行问题入账只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包"

ASSET_JSON = DATA_DIR / "稳定版试运行问题回传模板与入账预演包_最新.json"
TEMPLATE_JSON = DATA_DIR / "稳定版试运行问题回传模板_最新.json"
LEDGER_JSON = DATA_DIR / "稳定版试运行问题入账预演台账_最新.json"
CHECK_JSON = DATA_DIR / "稳定版试运行问题入账只读核对_最新.json"
CHECK_MD = DATA_DIR / "稳定版试运行问题入账只读核对_最新.md"


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
            "# 稳定版试运行问题入账只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 失败数：{report['汇总']['失败']}",
            f"- 当前问题数：{report['当前问题数']}",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    template = read_json(TEMPLATE_JSON)
    ledger = read_json(LEDGER_JSON)
    errors: list[str] = []
    if asset.get("状态") != "stable_trial_feedback_intake_preview_ready":
        errors.append("总包状态不正确")
    if len(template.get("字段", [])) < 10:
        errors.append("回传模板字段不得少于10项")
    if ledger.get("当前问题数") != len(ledger.get("问题项", [])):
        errors.append("台账问题数不一致")
    if ledger.get("当前问题数") != 0:
        errors.append("预演台账当前应无真实问题")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("总包安全边界必须全部为false")
    if not all(value is False for value in ledger.get("安全边界", {}).values()):
        errors.append("台账安全边界必须全部为false")
    for path_text in asset.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版试运行问题入账只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "blocked",
        "错误": errors,
        "汇总": {"总数": 7, "通过": 7 - len(errors), "失败": len(errors)},
        "当前问题数": ledger.get("当前问题数"),
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "失败": len(errors), "当前问题数": report["当前问题数"], "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
