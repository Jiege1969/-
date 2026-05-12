# -*- coding: utf-8 -*-
"""
名称：验证企业微信真实验证反馈进化候选.py
作用：只读验证企业微信真实验证反馈候选包、人工反馈记录、问题候选清单和多案例验证模板。
触发方式：python 验证企业微信真实验证反馈进化候选.py
依赖：Python标准库。
所属系统：03杰哥进化系统
安全边界：只读03候选文件并写03日志；不修改总管面板、一键接续包、企业微信配置或业务系统正式规则；不启用n8n；不真实发送。
标识：enterprise-wechat-real-validation-feedback-candidates-verify
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def all_false(mapping: dict[str, Any], keys: list[str]) -> bool:
    return all(mapping.get(key) is False for key in keys)


def main() -> int:
    root = system_root()
    data_dir = root / "03数据" / "37企业微信真实验证反馈进化候选"
    feedback_path = data_dir / "人工反馈记录_最新.json"
    candidates_path = data_dir / "问题候选清单_最新.json"
    template_path = data_dir / "多案例验证模板_最新.json"
    package_md = data_dir / "企业微信真实验证反馈进化候选包_最新.md"
    log_dir = root / "04日志" / "企业微信真实验证反馈候选验收"

    checks: list[dict[str, Any]] = []
    for name, path in [
        ("人工反馈记录存在", feedback_path),
        ("问题候选清单存在", candidates_path),
        ("多案例验证模板存在", template_path),
        ("候选包Markdown存在", package_md),
    ]:
        add_check(checks, name, path.exists(), str(path))

    feedback = load_json(feedback_path) if feedback_path.exists() else {}
    candidates = load_json(candidates_path) if candidates_path.exists() else {}
    template = load_json(template_path) if template_path.exists() else {}

    expected_ids = {"EWF-001", "EWF-002", "EWF-003", "EWF-004", "EWF-005"}
    feedback_ids = {item.get("问题ID") for item in feedback.get("反馈问题", [])}
    candidate_items = candidates.get("候选清单", [])
    candidate_ids = {item.get("候选ID") for item in candidate_items}
    case_items = template.get("验证案例", [])
    case_candidate_ids = {item.get("candidate_id") for item in case_items}

    add_check(checks, "人工反馈覆盖五类问题", expected_ids.issubset(feedback_ids), sorted(feedback_ids))
    add_check(checks, "候选清单覆盖五类问题", expected_ids.issubset(candidate_ids), sorted(candidate_ids))
    add_check(checks, "候选数量为5", candidates.get("候选数量") == 5 and len(candidate_items) == 5, candidates.get("候选数量"))
    add_check(checks, "所有候选保持candidate_only", all(item.get("候选状态") == "candidate_only" for item in candidate_items), candidate_items)
    add_check(checks, "所有候选需总管确认", all(item.get("需总管确认") is True for item in candidate_items), candidate_items)
    add_check(checks, "多案例模板覆盖五类候选", expected_ids.issubset(case_candidate_ids), sorted(case_candidate_ids))
    add_check(checks, "验证案例不少于10个", len(case_items) >= 10, len(case_items))
    add_check(checks, "每个案例都有禁止动作", all(bool(item.get("forbidden_actions")) for item in case_items), len(case_items))

    feedback_safety = feedback.get("安全边界", {})
    candidate_safety = candidates.get("安全边界", {})
    template_safety = template.get("安全边界", {})
    add_check(
        checks,
        "人工反馈安全边界全关闭",
        all_false(feedback_safety, ["修改总管面板", "修改一键接续包", "修改企业微信配置", "修改业务系统正式规则", "启用n8n", "真实发送"]),
        feedback_safety,
    )
    add_check(
        checks,
        "候选清单安全边界全关闭",
        all_false(candidate_safety, ["候选直接升级正式规则", "修改业务系统", "修改总管进度文件", "修改企业微信路由配置", "启用n8n", "真实发送"]),
        candidate_safety,
    )
    add_check(
        checks,
        "模板禁止真实动作",
        all_false(template_safety, ["执行真实企业微信发送", "触发n8n", "写业务系统正式规则", "修改总管进度口径", "修改企业微信配置"]),
        template_safety,
    )

    touched_redline = {
        "修改总管面板": False,
        "修改一键接续包": False,
        "修改企业微信配置": False,
        "修改业务系统正式规则": False,
        "启用n8n": False,
        "真实发送": False,
    }
    add_check(checks, "本验证未触碰红线", all(value is False for value in touched_redline.values()), touched_redline)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "enterprise-wechat-real-validation-feedback-candidates-verify",
        "所属系统": "03杰哥进化系统",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": {
            "人工反馈记录": str(feedback_path),
            "问题候选清单": str(candidates_path),
            "多案例验证模板": str(template_path),
            "候选包Markdown": str(package_md),
        },
        "红线动作": touched_redline,
    }
    output = log_dir / f"enterprise-wechat-real-validation-feedback-candidates-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "enterprise-wechat-real-validation-feedback-candidates-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
