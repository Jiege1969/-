# -*- coding: utf-8 -*-
"""验证稳定交付失败自动分级与总管确认闸口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包" / "稳定交付失败自动分级与总管确认闸口包_最新.json"
EVAL_JSON = ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包" / "当前失败自动分级只读评估_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定交付失败自动分级与总管确认闸口包验收"
LATEST_LOG = LOG_DIR / "stable-delivery-failure-gate-package-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    evaluation = read_json(EVAL_JSON) if EVAL_JSON.exists() else {}

    if asset.get("状态") != "stable_delivery_failure_gate_candidate_ready":
        errors.append("状态必须为 stable_delivery_failure_gate_candidate_ready")

    levels = asset.get("失败分级规则", [])
    level_ids = {item.get("级别") for item in levels}
    if level_ids != {"L0", "L1", "L2", "L3", "L4", "L5"}:
        errors.append("失败分级必须完整覆盖 L0-L5")
    if len(asset.get("需总管确认闸口", [])) < 8:
        errors.append("需总管确认闸口不得少于 8 项")
    if len(asset.get("失败后自动处置矩阵", [])) < 6:
        errors.append("失败后自动处置矩阵不得少于 6 项")

    confirm_levels = {item.get("级别") for item in levels if item.get("是否需总管确认") is True}
    if confirm_levels != {"L3", "L4", "L5"}:
        errors.append("必须且仅 L3/L4/L5 需要总管确认")

    if not evaluation:
        errors.append("当前失败自动分级只读评估不存在")
    else:
        if evaluation.get("当前失败级别") not in level_ids:
            errors.append("当前失败级别必须落在 L0-L5")
        if evaluation.get("需总管确认") is not False:
            errors.append("当前通过态不应需要总管确认")
        if evaluation.get("红线命中"):
            errors.append("当前评估不得命中红线")

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
        "名称": "稳定交付失败自动分级与总管确认闸口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "失败分级": len(levels),
            "确认闸口": len(asset.get("需总管确认闸口", [])),
            "自动处置矩阵": len(asset.get("失败后自动处置矩阵", [])),
            "当前失败级别": evaluation.get("当前失败级别"),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
