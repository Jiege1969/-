# -*- coding: utf-8 -*-
"""验证阶段性封版候选回归建议拆单。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "42阶段性封版候选回归建议拆单" / "阶段性封版候选回归建议拆单_最新.json"
LOG_DIR = ROOT / "04日志" / "阶段性封版候选回归建议拆单验收"
LATEST_LOG = LOG_DIR / "freeze-candidate-regression-cards-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    cards = asset.get("回归卡", [])
    if len(cards) != 8:
        errors.append("回归卡数量必须为8")
    for card in cards:
        for field in ["回归ID", "名称", "执行范围", "建议样本", "通过标准", "禁止动作", "越权处理"]:
            if not card.get(field):
                errors.append(f"{card.get('回归ID', '未知')} 缺少字段 {field}")
    safety = asset.get("安全边界", {})
    for flag in ["写正式规则", "修改运行配置", "触发服务重载", "真实发送企业微信", "接n8n", "接券商", "交易", "登录电子税务局", "接财税软件", "修改总管面板", "修改一键接续包", "推进为正式规则"]:
        if safety.get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "阶段性封版候选回归建议拆单验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {"回归卡数量": len(cards), "错误数": len(errors)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
