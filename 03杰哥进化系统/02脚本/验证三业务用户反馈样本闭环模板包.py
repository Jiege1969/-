# -*- coding: utf-8 -*-
"""验证三业务用户反馈样本闭环模板包验收结果。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
OUTPUT_DIR = ROOT / "03数据" / "71三业务用户反馈样本闭环模板包"
ASSET_JSON = OUTPUT_DIR / "三业务用户反馈样本闭环模板包_最新.json"
CHECK_JSON = OUTPUT_DIR / "三业务反馈样本闭环只读核对_最新.json"
LOG_DIR = ROOT / "04日志" / "三业务用户反馈样本闭环模板包验收"
LATEST_LOG = LOG_DIR / "three-business-feedback-loop-template-verify-最新.json"

REQUIRED_OUTPUTS = [
    OUTPUT_DIR / "三业务用户反馈样本闭环模板包_最新.json",
    OUTPUT_DIR / "三业务用户反馈样本闭环采集模板_最新.md",
    OUTPUT_DIR / "三业务反馈闭环安全边界_最新.md",
    OUTPUT_DIR / "三业务反馈样本闭环只读核对_最新.json",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if asset.get("状态") != "three_business_feedback_loop_template_ready":
        errors.append("模板包状态不正确")
    if check.get("总体状态") != "pass":
        errors.append("只读核对未通过")
    if check.get("汇总", {}).get("失败") != 0:
        errors.append("只读核对失败数必须为 0")

    templates = asset.get("模板列表", [])
    if {item.get("业务") for item in templates} != {"税收", "股票", "视频"}:
        errors.append("模板必须且只覆盖税收、股票、视频三业务")
    if any(item.get("是否可自动吸收") is not False for item in templates):
        errors.append("所有模板默认必须不自动吸收")
    if asset.get("安全边界", {}).get("自动转正式规则") is not False:
        errors.append("不得自动转正式规则")

    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    report = {
        "名称": "三业务用户反馈样本闭环模板包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "模板数": len(templates),
            "覆盖业务": sorted({item.get("业务") for item in templates}),
            "默认不自动吸收": all(item.get("是否可自动吸收") is False for item in templates),
            "不转正式规则": asset.get("安全边界", {}).get("自动转正式规则") is False,
            "只读核对失败数": check.get("汇总", {}).get("失败"),
        },
        "文件": {
            "模板包": str(ASSET_JSON),
            "只读核对": str(CHECK_JSON),
            "验收日志": str(LATEST_LOG),
        },
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
