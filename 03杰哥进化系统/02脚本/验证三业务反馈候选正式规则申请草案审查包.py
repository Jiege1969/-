# -*- coding: utf-8 -*-
"""验证三业务反馈候选正式规则申请草案审查包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "83三业务反馈候选正式规则申请草案审查包"
LOG_DIR = ROOT / "04日志" / "三业务反馈候选正式规则申请草案审查包验收"

PACKAGE_JSON = DATA_DIR / "三业务反馈候选正式规则申请草案审查包_最新.json"
REVIEW_RULE_JSON = DATA_DIR / "正式规则申请草案审查规则_最新.json"
REVIEW_RULE_MD = DATA_DIR / "正式规则申请草案审查规则_最新.md"
DRAFT_EXAMPLES_JSON = DATA_DIR / "三业务正式规则申请草案例子_最新.json"
REJECT_CONDITIONS_JSON = DATA_DIR / "正式规则申请草案驳回条件_最新.json"
REJECT_CONDITIONS_MD = DATA_DIR / "正式规则申请草案驳回条件_最新.md"
MANAGER_CHECKLIST_JSON = DATA_DIR / "总管确认清单_最新.json"
MANAGER_CHECKLIST_MD = DATA_DIR / "总管确认清单_最新.md"
REVIEW_PREVIEW_JSON = DATA_DIR / "正式规则申请草案审查预演结果_最新.json"
REVIEW_PREVIEW_MD = DATA_DIR / "正式规则申请草案审查预演结果_最新.md"
REVIEW_DRAFT_LIST_JSON = DATA_DIR / "正式规则申请草案审查清单_最新.json"
LOG_JSON = LOG_DIR / "three-business-formal-rule-application-draft-review-verify-最新.json"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
ALLOWED_REVIEW_STATES = {"待总管确认", "驳回草案", "冻结草案"}
REQUIRED_DRAFT_FIELDS = {
    "候选ID",
    "业务线",
    "来源",
    "拟申请规则标题",
    "影响范围",
    "回滚办法",
    "审查状态",
    "需总管确认",
    "正式生效",
}
REQUIRED_OUTPUTS = [
    PACKAGE_JSON,
    REVIEW_RULE_JSON,
    REVIEW_RULE_MD,
    DRAFT_EXAMPLES_JSON,
    REJECT_CONDITIONS_JSON,
    REJECT_CONDITIONS_MD,
    MANAGER_CHECKLIST_JSON,
    MANAGER_CHECKLIST_MD,
    REVIEW_PREVIEW_JSON,
    REVIEW_PREVIEW_MD,
    REVIEW_DRAFT_LIST_JSON,
]
FORBIDDEN_ACTIONS = [
    "真实发送企业微信",
    "接n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
    "修改总管面板",
    "修改一键接续包",
    "重载服务",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_flag(data: dict[str, Any], source_name: str, errors: list[str]) -> None:
    if data.get("正式生效") is not False:
        errors.append(f"{source_name} 必须声明正式生效=false")
    if data.get("写正式规则") is not False:
        errors.append(f"{source_name} 必须声明写正式规则=false")
    if data.get("需总管确认") is not True:
        errors.append(f"{source_name} 必须声明需总管确认=true")


def validate_draft(draft: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_DRAFT_FIELDS - set(draft))
    if missing:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 缺少申请草案字段：{', '.join(missing)}")
    if draft.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 业务线不合格")
    if not draft.get("候选ID"):
        errors.append("申请草案候选ID不能为空")
    if not draft.get("来源"):
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 来源不能为空")
    if not draft.get("拟申请规则标题"):
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 拟申请规则标题不能为空")
    if not draft.get("影响范围"):
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 影响范围不能为空")
    if not draft.get("回滚办法"):
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 回滚办法不能为空")
    if draft.get("审查状态") not in ALLOWED_REVIEW_STATES:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 审查状态只能为待总管确认/驳回草案/冻结草案")
    if draft.get("需总管确认") is not True:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 需总管确认必须为 true")
    if draft.get("正式生效") is not False:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 正式生效必须为 false")
    if draft.get("写正式规则") is not False:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 写正式规则必须为 false")
    if draft.get("修改运行配置") is not False:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 修改运行配置必须为 false")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    rule = read_json(REVIEW_RULE_JSON) if REVIEW_RULE_JSON.exists() else {}
    examples = read_json(DRAFT_EXAMPLES_JSON) if DRAFT_EXAMPLES_JSON.exists() else {}
    reject_conditions = read_json(REJECT_CONDITIONS_JSON) if REJECT_CONDITIONS_JSON.exists() else {}
    manager_checklist = read_json(MANAGER_CHECKLIST_JSON) if MANAGER_CHECKLIST_JSON.exists() else {}
    preview = read_json(REVIEW_PREVIEW_JSON) if REVIEW_PREVIEW_JSON.exists() else {}
    draft_list = read_json(REVIEW_DRAFT_LIST_JSON) if REVIEW_DRAFT_LIST_JSON.exists() else {}

    if package.get("状态") != "three_business_formal_rule_application_draft_review_ready":
        errors.append("生成包状态不正确")
    if set(rule.get("允许审查状态", [])) != ALLOWED_REVIEW_STATES:
        errors.append("审查状态集合必须仅为待总管确认/驳回草案/冻结草案")
    if rule.get("默认审查状态") != "待总管确认":
        errors.append("审查规则默认状态必须为待总管确认")
    for name in FORBIDDEN_ACTIONS:
        if package.get("红线动作", {}).get(name) is not False:
            errors.append(f"红线动作 {name} 必须为 false")
        if rule.get("红线动作", {}).get(name) is not False:
            errors.append(f"审查规则红线动作 {name} 必须为 false")

    for source_name, data in [
        ("生成包", package),
        ("审查规则", rule),
        ("三业务申请草案例子", examples),
        ("驳回条件", reject_conditions),
        ("总管确认清单", manager_checklist),
        ("审查预演", preview),
        ("审查清单", draft_list),
    ]:
        require_flag(data, source_name, errors)
        if data.get("修改运行配置") is True:
            errors.append(f"{source_name} 不得修改运行配置")

    if preview.get("总体状态") != "pass":
        errors.append("审查预演总体状态必须为 pass")
    if preview.get("错误数") != 0:
        errors.append("审查预演错误数必须为 0")
    if preview.get("默认审查状态") != "待总管确认":
        errors.append("审查预演默认状态必须为待总管确认")
    if preview.get("自动转正式规则") is not False:
        errors.append("审查预演必须声明自动转正式规则=false")
    if preview.get("触发外部系统") is not False:
        errors.append("审查预演必须声明触发外部系统=false")

    drafts = preview.get("申请草案", [])
    if len(drafts) < 3:
        errors.append("申请草案不得少于3条")
    draft_businesses = {draft.get("业务线") for draft in drafts}
    if draft_businesses != REQUIRED_BUSINESSES:
        errors.append("申请草案必须覆盖税收/股票/视频三业务")
    for draft in drafts:
        errors.extend(validate_draft(draft))

    list_drafts = draft_list.get("申请草案", [])
    if len(list_drafts) != len(drafts):
        errors.append("审查清单申请草案数必须与审查预演一致")
    for draft in list_drafts:
        errors.extend(validate_draft(draft))

    example_drafts = examples.get("申请草案", [])
    if {draft.get("业务线") for draft in example_drafts} != REQUIRED_BUSINESSES:
        errors.append("三业务申请草案例子必须覆盖税收/股票/视频")
    for draft in example_drafts:
        errors.extend(validate_draft(draft))

    report = {
        "名称": "三业务反馈候选正式规则申请草案审查包验收",
        "验收时间": now_text(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "覆盖三业务": draft_businesses == REQUIRED_BUSINESSES,
            "正式生效全为false": all(draft.get("正式生效") is False for draft in drafts),
            "写正式规则全为false": all(draft.get("写正式规则") is False for draft in drafts),
            "需总管确认全为true": all(draft.get("需总管确认") is True for draft in drafts),
            "审查状态合法": all(draft.get("审查状态") in ALLOWED_REVIEW_STATES for draft in drafts),
            "预演错误数": preview.get("错误数"),
            "申请草案数": len(drafts),
        },
        "文件": {
            "生成包": str(PACKAGE_JSON),
            "审查规则": str(REVIEW_RULE_JSON),
            "三业务申请草案例子": str(DRAFT_EXAMPLES_JSON),
            "驳回条件": str(REJECT_CONDITIONS_JSON),
            "总管确认清单": str(MANAGER_CHECKLIST_JSON),
            "审查预演": str(REVIEW_PREVIEW_JSON),
            "审查清单": str(REVIEW_DRAFT_LIST_JSON),
            "验收日志": str(LOG_JSON),
        },
    }

    write_json(LOG_JSON, report)
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "日志": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
