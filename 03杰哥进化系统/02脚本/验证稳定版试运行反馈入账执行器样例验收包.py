# -*- coding: utf-8 -*-
"""验证稳定版试运行反馈入账执行器样例验收包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93稳定版试运行反馈入账执行器样例验收包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版试运行反馈入账执行器样例验收包验收"

ASSET_JSON = DATA_DIR / "稳定版试运行反馈入账执行器样例验收包_最新.json"
SAMPLES_JSON = DATA_DIR / "稳定版试运行反馈入账样例_最新.json"
RESULT_JSON = DATA_DIR / "稳定版试运行反馈入账执行器样例自测结果_最新.json"
LATEST_LOG = LOG_DIR / "stable-trial-feedback-intake-executor-sample-verify-最新.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    samples = read_json(SAMPLES_JSON) if SAMPLES_JSON.exists() else {}
    result = read_json(RESULT_JSON) if RESULT_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not samples:
        errors.append(f"样例不存在：{SAMPLES_JSON}")
    if not result:
        errors.append(f"自测结果不存在：{RESULT_JSON}")

    if asset:
        if asset.get("状态") != "stable_trial_feedback_intake_executor_sample_acceptance_ready":
            errors.append("总包状态必须为 stable_trial_feedback_intake_executor_sample_acceptance_ready")
        if asset.get("指标", {}).get("样例数") != 3:
            errors.append("样例数必须为3")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")
    if result:
        if result.get("总体状态") != "pass":
            errors.append("自测结果必须为pass")
        if result.get("汇总", {}).get("失败") != 0:
            errors.append("自测失败数必须为0")
        redline = next((item for item in result.get("样例结果", []) if item.get("名称") == "红线反馈样例"), {})
        if redline.get("实际", {}).get("level") != "P0" or redline.get("实际", {}).get("need_supervisor_confirm") is not True:
            errors.append("红线反馈必须强制P0且需总管确认")

    report = {
        "名称": "稳定版试运行反馈入账执行器样例验收包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "样例数": len(samples),
            "自测通过": result.get("汇总", {}).get("通过") if result else 0,
            "自测失败": result.get("汇总", {}).get("失败") if result else None,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "样例": str(SAMPLES_JSON),
            "自测结果": str(RESULT_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
