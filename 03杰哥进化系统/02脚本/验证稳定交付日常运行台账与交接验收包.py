# -*- coding: utf-8 -*-
"""验证稳定交付日常运行台账与交接验收包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包" / "稳定交付日常运行台账与交接验收包_最新.json"
SUMMARY_JSON = ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包" / "日常运行台账只读汇总_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定交付日常运行台账与交接验收包验收"
LATEST_LOG = LOG_DIR / "stable-delivery-daily-ledger-handoff-package-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    summary = read_json(SUMMARY_JSON) if SUMMARY_JSON.exists() else {}

    if asset.get("状态") != "stable_delivery_daily_ledger_handoff_candidate_ready":
        errors.append("状态必须为 stable_delivery_daily_ledger_handoff_candidate_ready")
    if len(asset.get("日常检查项", [])) < 6:
        errors.append("日常检查项不得少于 6 项")
    if len(asset.get("交接验收项", [])) < 8:
        errors.append("交接验收项不得少于 8 项")
    if len(asset.get("异常记录字段", [])) < 10:
        errors.append("异常记录字段不得少于 10 项")

    for item in asset.get("日常检查项", []):
        for key in ["编号", "检查项", "频率", "验收产物", "通过口径", "失败处理"]:
            if not item.get(key):
                errors.append(f"日常检查项缺少字段：{item.get('编号')} {key}")

    if not summary:
        errors.append("日常运行台账只读汇总不存在")
    else:
        if summary.get("总体状态") != "pass":
            errors.append("日常运行台账只读汇总必须通过")
        if summary.get("汇总", {}).get("失败") != 0:
            errors.append("日常运行台账只读汇总失败数必须为 0")

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
        "名称": "稳定交付日常运行台账与交接验收包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "日常检查项": len(asset.get("日常检查项", [])),
            "交接验收项": len(asset.get("交接验收项", [])),
            "异常记录字段": len(asset.get("异常记录字段", [])),
            "只读汇总总数": summary.get("汇总", {}).get("总数", 0),
            "只读汇总失败": summary.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
