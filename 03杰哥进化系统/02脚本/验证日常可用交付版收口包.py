# -*- coding: utf-8 -*-
"""验证日常可用交付版收口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "46日常可用交付版收口包" / "日常可用交付版收口包_最新.json"
LOG_DIR = ROOT / "04日志" / "日常可用交付版收口包验收"
LATEST_LOG = LOG_DIR / "daily-usable-closeout-package-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    if asset.get("性质") != "候选收口包，不是正式规则":
        errors.append("性质必须保持候选收口包")
    if len(asset.get("使用说明", [])) < 5:
        errors.append("使用说明不得少于5项")
    if len(asset.get("故障处理清单", [])) < 5:
        errors.append("故障处理清单不得少于5项")
    tax = asset.get("税收业务接续替代包", {})
    if len(tax.get("当前已通过", [])) < 4:
        errors.append("税收接续替代包必须包含已通过状态")
    if len(tax.get("硬边界", [])) < 4:
        errors.append("税收接续替代包必须包含硬边界")
    port = asset.get("端口诊断与重载申请模板", {})
    if len(port.get("诊断步骤", [])) < 4:
        errors.append("端口诊断步骤不得少于4项")
    if len(port.get("模板正文", [])) < 4:
        errors.append("端口重载申请模板正文不得少于4项")
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
        "名称": "日常可用交付版收口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "使用说明": len(asset.get("使用说明", [])),
            "故障处理项": len(asset.get("故障处理清单", [])),
            "端口诊断步骤": len(port.get("诊断步骤", [])),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
