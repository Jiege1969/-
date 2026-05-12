# -*- coding: utf-8 -*-
"""验证完全交付使用路线图与工时估算包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "45完全交付使用路线图与工时估算" / "完全交付使用路线图与工时估算包_最新.json"
LOG_DIR = ROOT / "04日志" / "完全交付使用路线图与工时估算验收"
LATEST_LOG = LOG_DIR / "full-delivery-roadmap-hours-estimate-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    if asset.get("性质") != "候选估算包，不是正式规则或承诺排期":
        errors.append("性质必须保持候选估算包")
    progress = asset.get("整体进度判断", {})
    for key in ["日常可用交付版", "稳定交付版", "完全交付使用版", "真正自主运行版"]:
        if key not in progress:
            errors.append(f"缺少进度判断：{key}")
    hours = asset.get("剩余有效工时判断", {})
    for key in ["日常可用交付版剩余", "稳定交付版剩余", "完全交付使用版剩余", "真正自主运行版剩余"]:
        h = hours.get(key, {})
        if not all(isinstance(h.get(name), int) and h.get(name) > 0 for name in ["乐观", "常规", "保守"]):
            errors.append(f"工时估算不完整：{key}")
        if h and not (h["乐观"] <= h["常规"] <= h["保守"]):
            errors.append(f"工时估算顺序错误：{key}")
    if len(asset.get("路线图", [])) < 5:
        errors.append("路线图阶段不得少于5项")
    if len(asset.get("近期优先级", [])) < 5:
        errors.append("近期优先级不得少于5项")
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
        "真实渲染视频",
        "自动发布视频",
        "写正式税务结论",
        "修改总管面板",
        "修改一键接续包",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "完全交付使用路线图与工时估算验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "路线图阶段": len(asset.get("路线图", [])),
            "近期优先级": len(asset.get("近期优先级", [])),
            "完全交付常规剩余工时": asset.get("剩余有效工时判断", {}).get("完全交付使用版剩余", {}).get("常规"),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
