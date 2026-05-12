# -*- coding: utf-8 -*-
"""验证日常可用交付版收口后进度校准。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "47日常可用交付版收口后进度校准" / "日常可用交付版收口后进度校准_最新.json"
LOG_DIR = ROOT / "04日志" / "日常可用交付版收口后进度校准验收"
LATEST_LOG = LOG_DIR / "daily-usable-closeout-progress-calibration-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    if asset.get("整体进度判断", {}).get("日常可用交付版") != "93%-96%":
        errors.append("日常可用交付版进度应校准为93%-96%")
    h = asset.get("剩余有效工时判断", {}).get("日常可用交付版剩余", {})
    if h.get("常规") != 8:
        errors.append("日常可用交付版常规剩余应为8小时")
    if len(asset.get("日常可用版剩余收口项", [])) < 3:
        errors.append("剩余收口项不得少于3项")
    for flag, value in asset.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "日常可用交付版收口后进度校准验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {"日常可用常规剩余": h.get("常规"), "错误数": len(errors)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
