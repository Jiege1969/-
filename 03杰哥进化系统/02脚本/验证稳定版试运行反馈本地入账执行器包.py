# -*- coding: utf-8 -*-
"""验证稳定版试运行反馈本地入账执行器包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版试运行反馈本地入账执行器包验收"

ASSET_JSON = DATA_DIR / "稳定版试运行反馈本地入账执行器包_最新.json"
RESULT_JSON = DATA_DIR / "稳定版试运行反馈本地入账结果_最新.json"
LEDGER_JSON = DATA_DIR / "稳定版试运行反馈候选台账_最新.json"
REJECT_JSON = DATA_DIR / "稳定版试运行反馈拒收清单_最新.json"
LATEST_LOG = LOG_DIR / "stable-trial-feedback-local-intake-executor-verify-最新.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    result = read_json(RESULT_JSON) if RESULT_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {}
    reject = read_json(REJECT_JSON) if REJECT_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not result:
        errors.append(f"入账结果不存在：{RESULT_JSON}")
    if not ledger:
        errors.append(f"候选台账不存在：{LEDGER_JSON}")
    if not reject:
        errors.append(f"拒收清单不存在：{REJECT_JSON}")

    if asset:
        if asset.get("状态") != "stable_trial_feedback_local_intake_executor_ready":
            errors.append("总包状态必须为 stable_trial_feedback_local_intake_executor_ready")
        if asset.get("指标", {}).get("必填字段数", 0) < 10:
            errors.append("必填字段数不得少于10")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")
    if result:
        if result.get("总体状态") != "pass":
            errors.append("入账结果总体状态必须为pass")
        if not all(value is False for value in result.get("安全边界", {}).values()):
            errors.append("入账结果安全边界必须全部为false")
    if ledger:
        if ledger.get("候选问题数") != len(ledger.get("候选问题", [])):
            errors.append("候选问题数不一致")
        if not all(value is False for value in ledger.get("安全边界", {}).values()):
            errors.append("候选台账安全边界必须全部为false")

    report = {
        "名称": "稳定版试运行反馈本地入账执行器包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "扫描文件数": result.get("指标", {}).get("扫描文件数") if result else None,
            "接收数": result.get("指标", {}).get("接收数") if result else None,
            "拒收数": result.get("指标", {}).get("拒收数") if result else None,
            "需总管确认数": result.get("指标", {}).get("需总管确认数") if result else None,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "入账结果": str(RESULT_JSON),
            "候选台账": str(LEDGER_JSON),
            "拒收清单": str(REJECT_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
