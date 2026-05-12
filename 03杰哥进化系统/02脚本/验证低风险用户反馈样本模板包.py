# -*- coding: utf-8 -*-
"""验证低风险用户反馈样本模板包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "71低风险用户反馈样本模板包" / "低风险用户反馈样本模板包_最新.json"
CHECK_JSON = ROOT / "03数据" / "71低风险用户反馈样本模板包" / "低风险用户反馈模板只读核对_最新.json"
LOG_DIR = ROOT / "04日志" / "低风险用户反馈样本模板包验收"
LATEST_LOG = LOG_DIR / "low-risk-user-feedback-template-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}
    if asset.get("状态") != "low_risk_user_feedback_template_ready":
        errors.append("状态必须为 low_risk_user_feedback_template_ready")
    if len(asset.get("反馈模板", [])) < 5:
        errors.append("反馈模板不得少于5项")
    if len(asset.get("反馈分级规则", [])) < 5:
        errors.append("反馈分级规则不得少于5项")
    if check.get("总体状态") != "pass" or check.get("汇总", {}).get("失败") != 0:
        errors.append("只读核对必须通过且失败=0")
    for name, path_text in asset.get("输出文件", {}).items():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{name} {path_text}")
    for flag, value in asset.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界 {flag} 必须为false")
    report = {
        "名称": "低风险用户反馈样本模板包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "反馈模板": len(asset.get("反馈模板", [])),
            "反馈分级规则": len(asset.get("反馈分级规则", [])),
            "核对失败": check.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
