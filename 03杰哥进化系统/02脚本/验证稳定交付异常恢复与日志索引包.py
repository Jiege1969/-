# -*- coding: utf-8 -*-
"""验证稳定交付异常恢复与日志索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "49稳定交付异常恢复与日志索引包" / "稳定交付异常恢复与日志索引包_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定交付异常恢复与日志索引包验收"
LATEST_LOG = LOG_DIR / "stable-delivery-recovery-log-index-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}

    if not asset:
        errors.append("总包 JSON 不存在或不可读取")
    if asset.get("状态") != "stable_delivery_support_candidate_ready":
        errors.append("状态必须为 stable_delivery_support_candidate_ready")

    log_index = asset.get("关键日志索引", [])
    if len(log_index) < 5:
        errors.append("关键日志索引不得少于 5 个组件")
    for item in log_index:
        if item.get("证据文件数", 0) < 1:
            errors.append(f"{item.get('组件')} 缺少证据文件")

    failure_cards = asset.get("失败定位卡", [])
    if len(failure_cards) < 10:
        errors.append("失败定位卡不得少于 10 张")
    for card in failure_cards:
        for key in ["编号", "现象", "先看日志", "判断口径", "禁止动作"]:
            if not card.get(key):
                errors.append(f"失败定位卡缺少字段：{key}")

    if len(asset.get("异常恢复步骤", [])) < 6:
        errors.append("异常恢复步骤不得少于 6 项")

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
        "名称": "稳定交付异常恢复与日志索引包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "组件数": len(log_index),
            "失败定位卡": len(failure_cards),
            "异常恢复步骤": len(asset.get("异常恢复步骤", [])),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
