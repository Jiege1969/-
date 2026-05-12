# -*- coding: utf-8 -*-
"""验证日常可用交付版状态包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "43日常可用交付版状态包" / "日常可用交付版状态包_最新.json"
LOG_DIR = ROOT / "04日志" / "日常可用交付版状态包验收"
LATEST_LOG = LOG_DIR / "daily-usable-delivery-status-package-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    if asset.get("整体状态") != "daily_usable_candidate_passed":
        errors.append("整体状态必须为 daily_usable_candidate_passed")
    if len(asset.get("可用能力", [])) < 8:
        errors.append("可用能力不得少于8项")
    if len(asset.get("仍阻断能力", [])) < 10:
        errors.append("仍阻断能力不得少于10项")
    if len(asset.get("后续回归卡", [])) < 8:
        errors.append("后续回归卡不得少于8张")
    for path in asset.get("来源文件", {}).values():
        if not Path(path).exists():
            errors.append(f"来源文件不存在：{path}")
    for flag in [
        "写正式规则",
        "修改运行配置",
        "触发服务重载",
        "重载19310",
        "重载19302",
        "真实发送企业微信",
        "接n8n",
        "触发n8n",
        "接券商",
        "交易",
        "登录电子税务局",
        "接财税软件",
        "生成正式税务结论",
        "真实渲染视频",
        "自动发布视频",
        "修改总管面板",
        "修改一键接续包",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "日常可用交付版状态包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "可用能力": len(asset.get("可用能力", [])),
            "仍阻断能力": len(asset.get("仍阻断能力", [])),
            "后续回归卡": len(asset.get("后续回归卡", [])),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
