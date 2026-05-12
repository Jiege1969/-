# -*- coding: utf-8 -*-
"""执行三业务反馈候选正式规则申请草案审查预演。

执行结果只生成申请草案审查预演，不写正式规则、不改运行配置、不接外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "83三业务反馈候选正式规则申请草案审查包"

PACKAGE_JSON = DATA_DIR / "三业务反馈候选正式规则申请草案审查包_最新.json"
REVIEW_RULE_JSON = DATA_DIR / "正式规则申请草案审查规则_最新.json"
DRAFT_EXAMPLES_JSON = DATA_DIR / "三业务正式规则申请草案例子_最新.json"
REJECT_CONDITIONS_JSON = DATA_DIR / "正式规则申请草案驳回条件_最新.json"
MANAGER_CHECKLIST_JSON = DATA_DIR / "总管确认清单_最新.json"
REVIEW_PREVIEW_JSON = DATA_DIR / "正式规则申请草案审查预演结果_最新.json"
REVIEW_PREVIEW_MD = DATA_DIR / "正式规则申请草案审查预演结果_最新.md"
REVIEW_DRAFT_LIST_JSON = DATA_DIR / "正式规则申请草案审查清单_最新.json"

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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_package(package: dict[str, Any], errors: list[str]) -> None:
    if package.get("状态") != "three_business_formal_rule_application_draft_review_ready":
        errors.append("生成包状态不正确或尚未生成")
    for field, expected in [("需总管确认", True), ("正式生效", False), ("写正式规则", False), ("修改运行配置", False)]:
        if package.get(field) is not expected:
            errors.append(f"生成包字段 {field} 必须为 {str(expected).lower()}")
    for name in FORBIDDEN_ACTIONS:
        if package.get("红线动作", {}).get(name) is not False:
            errors.append(f"红线动作 {name} 必须为 false")


def validate_draft(draft: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_DRAFT_FIELDS - set(draft))
    if missing:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 缺少字段：{', '.join(missing)}")
    if draft.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 业务线不在税收/股票/视频范围")
    if draft.get("审查状态") not in ALLOWED_REVIEW_STATES:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 审查状态非法")
    if draft.get("需总管确认") is not True:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 需总管确认必须为 true")
    if draft.get("正式生效") is not False:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 正式生效必须为 false")
    if draft.get("写正式规则") is not False:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 写正式规则必须为 false")
    if draft.get("修改运行配置") is not False:
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 修改运行配置必须为 false")
    if not draft.get("影响范围"):
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 影响范围不能为空")
    if not draft.get("回滚办法"):
        errors.append(f"{draft.get('候选ID', 'UNKNOWN')} 回滚办法不能为空")
    return errors


def build_reviewed_drafts(example_drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reviewed = []
    for draft in example_drafts:
        reviewed.append(
            {
                "候选ID": draft.get("候选ID"),
                "业务线": draft.get("业务线"),
                "来源": draft.get("来源"),
                "拟申请规则标题": draft.get("拟申请规则标题"),
                "草案依据": draft.get("草案依据", ""),
                "影响范围": draft.get("影响范围"),
                "回滚办法": draft.get("回滚办法"),
                "审查状态": "待总管确认",
                "审查结论": "可生成申请草案，等待总管确认；不得写正式规则。",
                "需总管确认": True,
                "正式生效": False,
                "写正式规则": False,
                "修改运行配置": False,
                "自动转正式规则": False,
                "触发外部系统": False,
                "总管确认前动作": "仅保留草案审查记录",
            }
        )
    return reviewed


def build_preview_md(report: dict[str, Any]) -> str:
    lines = [
        "# 正式规则申请草案审查预演结果",
        "",
        f"- 预演时间：{report['预演时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 错误数：{report['错误数']}",
        "- 正式生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "| 候选ID | 业务线 | 审查状态 | 正式生效 | 写正式规则 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for draft in report["申请草案"]:
        lines.append(
            f"| {draft['候选ID']} | {draft['业务线']} | {draft['审查状态']} | "
            f"{str(draft['正式生效']).lower()} | {str(draft['写正式规则']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    for path in [PACKAGE_JSON, REVIEW_RULE_JSON, DRAFT_EXAMPLES_JSON, REJECT_CONDITIONS_JSON, MANAGER_CHECKLIST_JSON]:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    rule = read_json(REVIEW_RULE_JSON) if REVIEW_RULE_JSON.exists() else {}
    examples = read_json(DRAFT_EXAMPLES_JSON) if DRAFT_EXAMPLES_JSON.exists() else {}
    reject_conditions = read_json(REJECT_CONDITIONS_JSON) if REJECT_CONDITIONS_JSON.exists() else {}
    manager_checklist = read_json(MANAGER_CHECKLIST_JSON) if MANAGER_CHECKLIST_JSON.exists() else {}

    validate_package(package, errors)
    if set(rule.get("允许审查状态", [])) != ALLOWED_REVIEW_STATES:
        errors.append("审查规则允许状态必须仅为待总管确认/驳回草案/冻结草案")
    if reject_conditions.get("写正式规则") is not False or reject_conditions.get("正式生效") is not False:
        errors.append("驳回条件必须声明正式生效=false且写正式规则=false")
    if manager_checklist.get("需总管确认") is not True:
        errors.append("总管确认清单必须声明需总管确认=true")

    example_drafts = examples.get("申请草案", [])
    reviewed_drafts = build_reviewed_drafts(example_drafts) if not errors else []
    for draft in reviewed_drafts:
        errors.extend(validate_draft(draft))

    businesses = {draft.get("业务线") for draft in reviewed_drafts}
    if businesses != REQUIRED_BUSINESSES:
        errors.append("审查预演必须覆盖税收/股票/视频三业务")

    generated_at = now_text()
    report = {
        "名称": "正式规则申请草案审查预演结果",
        "预演时间": generated_at,
        "总体状态": "pass" if not errors else "fail",
        "错误数": len(errors),
        "错误": errors,
        "读取文件": [
            str(PACKAGE_JSON),
            str(REVIEW_RULE_JSON),
            str(DRAFT_EXAMPLES_JSON),
            str(REJECT_CONDITIONS_JSON),
            str(MANAGER_CHECKLIST_JSON),
        ],
        "覆盖业务": sorted(businesses),
        "允许审查状态": sorted(ALLOWED_REVIEW_STATES),
        "默认审查状态": "待总管确认",
        "需总管确认": True,
        "正式生效": False,
        "写正式规则": False,
        "修改运行配置": False,
        "自动转正式规则": False,
        "触发外部系统": False,
        "申请草案": reviewed_drafts,
        "汇总": {
            "申请草案数": len(reviewed_drafts),
            "业务数": len(businesses),
            "待总管确认数": sum(1 for draft in reviewed_drafts if draft.get("审查状态") == "待总管确认"),
            "需总管确认数": sum(1 for draft in reviewed_drafts if draft.get("需总管确认") is True),
            "正式生效数": sum(1 for draft in reviewed_drafts if draft.get("正式生效") is True),
            "写正式规则数": sum(1 for draft in reviewed_drafts if draft.get("写正式规则") is True),
            "修改运行配置数": sum(1 for draft in reviewed_drafts if draft.get("修改运行配置") is True),
            "错误数": len(errors),
        },
        "输出文件": {
            "审查预演JSON": str(REVIEW_PREVIEW_JSON),
            "审查预演Markdown": str(REVIEW_PREVIEW_MD),
            "审查清单JSON": str(REVIEW_DRAFT_LIST_JSON),
        },
    }
    draft_list = {
        "名称": "正式规则申请草案审查清单",
        "生成时间": generated_at,
        "覆盖业务": sorted(businesses),
        "默认审查状态": "待总管确认",
        "需总管确认": True,
        "正式生效": False,
        "写正式规则": False,
        "修改运行配置": False,
        "申请草案": reviewed_drafts,
    }

    write_json(REVIEW_PREVIEW_JSON, report)
    write_text(REVIEW_PREVIEW_MD, build_preview_md(report))
    write_json(REVIEW_DRAFT_LIST_JSON, draft_list)

    print(
        json.dumps(
            {
                "总体状态": report["总体状态"],
                "错误数": report["错误数"],
                "申请草案数": len(reviewed_drafts),
                "输出": str(REVIEW_PREVIEW_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
