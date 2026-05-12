# -*- coding: utf-8 -*-
"""验证稳定版候选正式封版申请草案与最终交付封面收紧包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "71稳定版候选正式封版申请草案与最终交付封面收紧包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版候选正式封版申请草案与最终交付封面收紧包验收"

ASSET_JSON = DATA_DIR / "稳定版候选正式封版申请草案与最终交付封面收紧包_最新.json"
CHECK_JSON = DATA_DIR / "稳定版候选封版申请草案只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-candidate-formal-freeze-request-draft-verify-最新.json"


REQUIRED_OUTPUT_KEYS = ["总包JSON", "总包Markdown", "申请条件", "当前证据清单", "仍需总管确认项", "禁止自动执行项", "使用者交付封面简版"]
REQUIRED_PROHIBITED_FALSE = [
    "真实发送企业微信",
    "触发n8n",
    "接n8n",
    "接券商",
    "交易",
    "登录电子税务局",
    "接财税软件",
    "生成正式税务结论",
    "真实渲染视频",
    "自动发布视频",
    "自动转正式规则",
    "正式封版",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载19310",
    "重载19302",
    "请求19302业务接口",
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
        if asset.get("状态") != "formal_freeze_request_draft_ready":
            errors.append("总包状态必须为 formal_freeze_request_draft_ready")
        if asset.get("草案性质") != "正式封版申请草案，不是正式封版":
            errors.append("草案性质必须明确不是正式封版")
        if len(asset.get("申请条件", [])) < 5:
            errors.append("申请条件不得少于 5 项")
        if len(asset.get("当前证据", [])) < 4:
            errors.append("当前证据不得少于 4 项")
        if len(asset.get("仍需总管确认项", [])) < 5:
            errors.append("仍需总管确认项不得少于 5 项")

        for item in asset.get("当前证据", []):
            for key in ["编号", "名称", "类别", "路径", "存在", "通过"]:
                if key not in item:
                    errors.append(f"当前证据缺少字段：{item.get('编号')} {key}")
            path_text = item.get("路径")
            if path_text and not Path(path_text).exists():
                errors.append(f"当前证据路径不存在：{item.get('编号')} {path_text}")
            if item.get("通过") is not True:
                errors.append(f"当前证据未通过：{item.get('编号')} {item.get('名称')}")

        prohibited = asset.get("禁止自动执行项", {})
        for flag in REQUIRED_PROHIBITED_FALSE:
            if prohibited.get(flag) is not False:
                errors.append(f"禁止自动执行项必须为 false：{flag}")

        for key in REQUIRED_OUTPUT_KEYS:
            path_text = asset.get("输出文件", {}).get(key)
            if not path_text:
                errors.append(f"输出文件缺少：{key}")
            elif not Path(path_text).exists():
                errors.append(f"输出文件不存在：{key} {path_text}")

    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为 pass")
        if check.get("可提交申请草案") is not True:
            errors.append("只读核对必须允许提交申请草案")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为 0")
        if check.get("禁止自动执行项全部关闭") is not True:
            errors.append("只读核对必须确认禁止自动执行项全部关闭")

    report = {
        "名称": "稳定版候选正式封版申请草案与最终交付封面收紧包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "申请条件": len(asset.get("申请条件", [])) if asset else 0,
            "当前证据": len(asset.get("当前证据", [])) if asset else 0,
            "仍需总管确认项": len(asset.get("仍需总管确认项", [])) if asset else 0,
            "禁止自动执行项": len(asset.get("禁止自动执行项", {})) if asset else 0,
            "只读核对失败": check.get("汇总", {}).get("失败") if check else None,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "只读核对": str(CHECK_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
