# -*- coding: utf-8 -*-
"""验证稳定版试运行问题回传模板与入账预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版试运行问题回传模板与入账预演包验收"

ASSET_JSON = DATA_DIR / "稳定版试运行问题回传模板与入账预演包_最新.json"
TEMPLATE_JSON = DATA_DIR / "稳定版试运行问题回传模板_最新.json"
LEDGER_JSON = DATA_DIR / "稳定版试运行问题入账预演台账_最新.json"
CHECK_JSON = DATA_DIR / "稳定版试运行问题入账只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-trial-feedback-intake-preview-verify-最新.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    template = read_json(TEMPLATE_JSON) if TEMPLATE_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not template:
        errors.append(f"模板不存在：{TEMPLATE_JSON}")
    if not ledger:
        errors.append(f"台账不存在：{LEDGER_JSON}")
    if not check:
        errors.append(f"只读核对不存在：{CHECK_JSON}")

    if asset:
        if asset.get("状态") != "stable_trial_feedback_intake_preview_ready":
            errors.append("总包状态必须为 stable_trial_feedback_intake_preview_ready")
        if asset.get("指标", {}).get("模板字段数", 0) < 10:
            errors.append("模板字段数不得少于10")
        if asset.get("指标", {}).get("当前问题数") != 0:
            errors.append("预演包当前问题数必须为0")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    if template and "是否疑似红线" not in template.get("字段", []):
        errors.append("模板必须包含是否疑似红线字段")
    if ledger and ledger.get("当前问题数") != 0:
        errors.append("预演台账当前问题数必须为0")
    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为pass")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为0")

    report = {
        "名称": "稳定版试运行问题回传模板与入账预演包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "模板字段数": len(template.get("字段", [])) if template else 0,
            "当前问题数": ledger.get("当前问题数") if ledger else None,
            "样例分类数": len(ledger.get("样例分类", [])) if ledger else 0,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "模板": str(TEMPLATE_JSON),
            "台账": str(LEDGER_JSON),
            "只读核对": str(CHECK_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
