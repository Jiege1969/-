# -*- coding: utf-8 -*-
"""
名称：验证文稿质检低负担触发闸口.py
作用：验证文稿质检低负担触发规则和闸口脚本，确保默认不调用模型，只有手动或低峰条件才允许旁路审稿。
触发方式：python 验证文稿质检低负担触发闸口.py
依赖：Python标准库；文稿质检低负担触发规则.json；文稿质检低负担触发闸口.py。
所属系统：01杰哥智能系统/文稿质检
输出：04日志/文稿质检/text-review-low-load-gate-verify-最新.json。
安全边界：只读配置并运行闸口决策脚本；不调用模型，不触发n8n，不发送企业微信，不替换原文，不写正式模板，不调用券商接口，不自动交易。
创建/修改记录：2026-05-03 创建低负担触发闸口验证脚本。
标识：text-review-low-load-gate-verify
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def smart_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def run_gate(script: Path, *args: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
    )
    if completed.returncode != 0:
        return {"returncode": completed.returncode, "stderr": completed.stderr.strip(), "stdout": completed.stdout.strip()}
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        value = {"stdout": completed.stdout.strip()}
    value["returncode"] = completed.returncode
    return value


def main() -> int:
    root = smart_root()
    policy = root / "01配置" / "文稿质检低负担触发规则.json"
    script = root / "02脚本" / "文稿质检" / "文稿质检低负担触发闸口.py"
    policy_json = load_json(policy, {}) or {}
    checks: list[dict[str, Any]] = [
        check("低负担触发规则存在", policy.exists(), str(policy)),
        check("低负担触发闸口脚本存在", script.exists(), str(script)),
        check("默认正式链路不自动模型审稿", policy_json.get("默认策略", {}).get("正式推送前自动模型审稿") is False, policy_json.get("默认策略", {})),
        check("普通对话不模型审稿", policy_json.get("默认策略", {}).get("普通对话模型审稿") is False, policy_json.get("默认策略", {})),
        check("硬性禁止不自动替换原文", policy_json.get("硬性禁止", {}).get("自动替换正式原文") is False, policy_json.get("硬性禁止", {})),
    ]

    default_decision = run_gate(script, "--doc-type", "stock_single_report", "--now", "14:00")
    manual_decision = run_gate(script, "--trigger", "#审稿", "--doc-type", "stock_single_report", "--now", "14:00")
    deep_decision = run_gate(script, "--trigger", "#深度审稿", "--doc-type", "stock_single_report", "--now", "14:00")
    batch_day_decision = run_gate(script, "--batch", "--doc-type", "stock_single_report", "--now", "14:00")
    batch_night_decision = run_gate(script, "--batch", "--doc-type", "stock_single_report", "--now", "23:00")
    compare_decision = run_gate(script, "--model-compare", "--doc-type", "stock_single_report", "--now", "23:00")

    checks.extend([
        check("默认场景不允许调用模型", default_decision.get("允许调用模型") is False, default_decision),
        check("手动审稿允许轻量模型", manual_decision.get("允许调用模型") is True and manual_decision.get("动作") == "light_model_review", manual_decision),
        check("深度审稿仅增强候选", deep_decision.get("允许调用模型") is True and deep_decision.get("动作") == "enhanced_model_review_candidate", deep_decision),
        check("白天批处理不允许模型", batch_day_decision.get("允许调用模型") is False, batch_day_decision),
        check("低峰批处理允许轻量审稿", batch_night_decision.get("允许调用模型") is True and batch_night_decision.get("低峰时间窗") is True, batch_night_decision),
        check("多模型对比默认不进入日常链路", compare_decision.get("允许调用模型") is False and compare_decision.get("动作") == "plan_only_or_manual_sample", compare_decision),
        check("所有决策均不触发n8n", all(
            item.get("安全边界", {}).get("触发n8n") is False
            for item in [default_decision, manual_decision, deep_decision, batch_day_decision, batch_night_decision, compare_decision]
        ), "触发n8n应始终为False"),
        check("所有决策均不自动替换原文", all(
            item.get("安全边界", {}).get("替换原文") is False
            for item in [default_decision, manual_decision, deep_decision, batch_day_decision, batch_night_decision, compare_decision]
        ), "替换原文应始终为False"),
    ])

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "名称": "文稿质检低负担触发闸口验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "样本决策": {
            "默认": default_decision,
            "手动审稿": manual_decision,
            "深度审稿": deep_decision,
            "白天批处理": batch_day_decision,
            "低峰批处理": batch_night_decision,
            "多模型对比": compare_decision,
        },
    }
    log_dir = root / "04日志" / "文稿质检"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(log_dir / f"text-review-low-load-gate-verify-{stamp}.json", result)
    latest = log_dir / "text-review-low-load-gate-verify-最新.json"
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
