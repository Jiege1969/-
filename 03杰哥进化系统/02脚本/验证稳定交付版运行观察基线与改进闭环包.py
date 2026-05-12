# -*- coding: utf-8 -*-
"""验证稳定交付版运行观察基线与改进闭环包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "77稳定交付版运行观察基线与改进闭环包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版运行观察基线与改进闭环包验收"

ASSET_JSON = DATA_DIR / "稳定交付版运行观察基线与改进闭环包_最新.json"
CHECK_JSON = DATA_DIR / "稳定交付版运行观察基线只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-runtime-observation-loop-verify-最新.json"


REQUIRED_OUTPUTS = [
    "总包JSON",
    "总包Markdown",
    "运行观察台账模板JSON",
    "运行观察台账模板Markdown",
    "问题分级表JSON",
    "改进闭环候选流程JSON",
    "改进闭环候选流程Markdown",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not check:
        errors.append(f"只读核对不存在：{CHECK_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_runtime_observation_baseline_ready":
            errors.append("总包状态必须为 stable_delivery_runtime_observation_baseline_ready")
        if "稳定交付版" not in asset.get("当前策略", ""):
            errors.append("当前策略必须明确稳定交付版优先")
        if len(asset.get("证据", [])) < 5:
            errors.append("证据不得少于 5 项")
        if asset.get("指标", {}).get("证据通过") != asset.get("指标", {}).get("证据总数"):
            errors.append("证据必须全部通过")
        if len(asset.get("问题分级表", [])) != 5:
            errors.append("问题分级必须为 P0-P4 五类")
        if asset.get("指标", {}).get("闭环步骤数", 0) < 7:
            errors.append("闭环步骤不得少于 7 项")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("安全边界必须全部为 false")
        loop_path = Path(asset.get("改进闭环候选流程", ""))
        if loop_path.exists():
            loop = read_json(loop_path)
            if loop.get("性质") != "候选流程，不是正式规则":
                errors.append("改进闭环必须保持候选流程，不是正式规则")
        else:
            errors.append(f"改进闭环候选流程不存在：{loop_path}")
        for key in REQUIRED_OUTPUTS:
            output = asset.get("输出文件", {}).get(key)
            if not output:
                errors.append(f"输出文件缺少：{key}")
            elif not Path(output).exists():
                errors.append(f"输出文件不存在：{key} {output}")

    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为 pass")
        if check.get("可进入稳定版运行观察") is not True:
            errors.append("只读核对必须允许进入稳定版运行观察")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为 0")
        if check.get("安全边界全部关闭") is not True:
            errors.append("只读核对必须确认安全边界全部关闭")

    report = {
        "名称": "稳定交付版运行观察基线与改进闭环包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "证据总数": asset.get("指标", {}).get("证据总数", 0) if asset else 0,
            "证据通过": asset.get("指标", {}).get("证据通过", 0) if asset else 0,
            "问题分级数": asset.get("指标", {}).get("问题分级数", 0) if asset else 0,
            "闭环步骤数": asset.get("指标", {}).get("闭环步骤数", 0) if asset else 0,
            "只读核对失败": check.get("汇总", {}).get("失败") if check else None,
        },
        "验证范围": {"总包": str(ASSET_JSON), "只读核对": str(CHECK_JSON), "日志": str(LATEST_LOG)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
