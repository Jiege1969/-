# -*- coding: utf-8 -*-
"""验证最终日常可用交付候选回传包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "48最终日常可用交付候选回传" / "最终日常可用交付候选回传_最新.json"
LOG_DIR = ROOT / "04日志" / "最终日常可用交付候选回传验收"
LATEST_LOG = LOG_DIR / "final-daily-usable-delivery-candidate-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    if asset.get("总判断") != "日常可用交付候选版通过":
        errors.append("总判断必须为日常可用交付候选版通过")
    evidence = asset.get("通过证据", {})
    if evidence.get("一键只读总回归", {}).get("失败") != 0:
        errors.append("一键只读总回归必须0失败")
    if evidence.get("总览快照", {}).get("失败") != 0:
        errors.append("总览快照必须0失败")
    if evidence.get("可用能力", 0) < 8:
        errors.append("可用能力不得少于8")
    if evidence.get("仍阻断能力", 0) < 10:
        errors.append("仍阻断能力不得少于10")
    if evidence.get("回归卡", 0) < 8:
        errors.append("回归卡不得少于8")
    h = asset.get("剩余有效工时", {}).get("日常可用交付版剩余", {})
    if h.get("常规") != 8:
        errors.append("日常可用交付版常规剩余应为8小时")
    for flag, value in asset.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "最终日常可用交付候选回传验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "可用能力": evidence.get("可用能力", 0),
            "仍阻断能力": evidence.get("仍阻断能力", 0),
            "回归卡": evidence.get("回归卡", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
