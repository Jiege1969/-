# -*- coding: utf-8 -*-
"""验证稳定版候选最终回传与可交付声明包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "58稳定版候选最终回传与可交付声明包" / "稳定版候选最终回传与可交付声明包_最新.json"
CHECK_JSON = ROOT / "03数据" / "58稳定版候选最终回传与可交付声明包" / "稳定版候选可交付声明只读核对_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定版候选最终回传与可交付声明包验收"
LATEST_LOG = LOG_DIR / "stable-candidate-final-delivery-statement-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if asset.get("状态") != "stable_candidate_final_delivery_statement_ready":
        errors.append("状态必须为 stable_candidate_final_delivery_statement_ready")
    if len(asset.get("核心证据", [])) < 5:
        errors.append("核心证据不得少于 5 项")
    if len(asset.get("剩余限制", [])) < 6:
        errors.append("剩余限制不得少于 6 项")
    if asset.get("可交付声明", {}).get("声明级别") != "稳定版候选可交付":
        errors.append("声明级别必须为 稳定版候选可交付")

    for item in asset.get("核心证据", []):
        for key in ["名称", "路径", "要求"]:
            if not item.get(key):
                errors.append(f"核心证据缺少字段：{item.get('名称')} {key}")
        if item.get("路径") and not Path(item["路径"]).exists():
            errors.append(f"核心证据路径不存在：{item.get('名称')} {item.get('路径')}")

    if not check:
        errors.append("稳定版候选可交付声明只读核对不存在")
    else:
        if check.get("总体状态") != "pass":
            errors.append("稳定版候选可交付声明只读核对必须通过")
        if check.get("可交付声明成立") is not True:
            errors.append("可交付声明必须成立")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("核心证据失败数必须为 0")

    for name, path_text in asset.get("输出文件", {}).items():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{name} {path_text}")

    for flag in [
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
        "修改运行配置",
        "修改总管面板",
        "修改一键接续包",
        "重载19310",
        "重载19302",
        "请求19302业务接口",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "稳定版候选最终回传与可交付声明包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "核心证据": len(asset.get("核心证据", [])),
            "剩余限制": len(asset.get("剩余限制", [])),
            "证据失败": check.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
