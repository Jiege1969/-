# -*- coding: utf-8 -*-
"""生成三业务反馈候选正式规则申请草案审查包。

本包只承接第80包状态机/预演产物与本包示例，生成“正式规则申请草案审查”
所需的规则、示例、驳回条件和总管确认清单；不写正式规则，不改运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "83三业务反馈候选正式规则申请草案审查包"
SOURCE_80_DIR = ROOT / "03数据" / "80三业务反馈人工确认状态机与候选生效前闸口包"
SOURCE_80_PACKAGE_JSON = SOURCE_80_DIR / "三业务反馈人工确认状态机与候选生效前闸口包_最新.json"
SOURCE_80_STATE_MACHINE_JSON = SOURCE_80_DIR / "人工确认状态机定义_最新.json"
SOURCE_80_PREVIEW_JSON = SOURCE_80_DIR / "人工确认状态迁移预演结果_最新.json"

PACKAGE_JSON = DATA_DIR / "三业务反馈候选正式规则申请草案审查包_最新.json"
REVIEW_RULE_JSON = DATA_DIR / "正式规则申请草案审查规则_最新.json"
REVIEW_RULE_MD = DATA_DIR / "正式规则申请草案审查规则_最新.md"
DRAFT_EXAMPLES_JSON = DATA_DIR / "三业务正式规则申请草案例子_最新.json"
REJECT_CONDITIONS_JSON = DATA_DIR / "正式规则申请草案驳回条件_最新.json"
REJECT_CONDITIONS_MD = DATA_DIR / "正式规则申请草案驳回条件_最新.md"
MANAGER_CHECKLIST_JSON = DATA_DIR / "总管确认清单_最新.json"
MANAGER_CHECKLIST_MD = DATA_DIR / "总管确认清单_最新.md"

REQUIRED_BUSINESSES = ["税收", "股票", "视频"]
ALLOWED_REVIEW_STATES = ["待总管确认", "驳回草案", "冻结草案"]
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


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fallback_source_candidates() -> list[dict[str, Any]]:
    return [
        {
            "候选ID": "DRAFT-SEED-TAX-001",
            "业务线": "税收",
            "来源": "本包示例/税收/正式规则申请草案审查",
            "问题类型": "口径不清",
            "建议动作": "补充资料清单、适用前提和人工复核提示。",
        },
        {
            "候选ID": "DRAFT-SEED-STOCK-001",
            "业务线": "股票",
            "来源": "本包示例/股票/正式规则申请草案审查",
            "问题类型": "风险提示不足",
            "建议动作": "补充非交易建议声明、风险边界和人工确认提示。",
        },
        {
            "候选ID": "DRAFT-SEED-VIDEO-001",
            "业务线": "视频",
            "来源": "本包示例/视频/正式规则申请草案审查",
            "问题类型": "分镜遗漏",
            "建议动作": "补充分镜占位、口播节奏和人工确认点。",
        },
    ]


def load_source_candidates(preview: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = preview.get("候选条目", [])
    if not isinstance(candidates, list) or not candidates:
        return fallback_source_candidates()

    selected: list[dict[str, Any]] = []
    seen_businesses: set[str] = set()
    for item in candidates:
        business = item.get("业务线")
        if business in REQUIRED_BUSINESSES and business not in seen_businesses:
            selected.append(
                {
                    "候选ID": item.get("候选ID"),
                    "业务线": business,
                    "来源": item.get("来源"),
                    "问题类型": item.get("问题类型"),
                    "建议动作": item.get("建议动作"),
                    "第80包当前状态": item.get("当前状态"),
                    "第80包允许下一状态": item.get("允许下一状态", []),
                }
            )
            seen_businesses.add(business)
    if set(seen_businesses) == set(REQUIRED_BUSINESSES):
        return selected
    return fallback_source_candidates()


def business_scope(business: str) -> str:
    scopes = {
        "税收": "仅影响税收反馈候选的资料清单、口径说明和人工复核提示文本。",
        "股票": "仅影响股票反馈候选的风险提示、非交易建议声明和展示层改写建议。",
        "视频": "仅影响视频反馈候选的分镜占位、口播节奏提示和人工确认点。",
    }
    return scopes[business]


def rollback_plan(business: str) -> str:
    plans = {
        "税收": "撤回草案记录，保留原候选与第80包状态机产物，不同步到正式规则。",
        "股票": "撤回草案记录，恢复候选说明原文，不触发券商、交易或任何自动化配置。",
        "视频": "撤回草案记录，恢复候选分镜说明，不触发渲染、发布或服务重载。",
    }
    return plans[business]


def rule_title(item: dict[str, Any]) -> str:
    return f"{item['业务线']}反馈候选正式规则申请草案：{item.get('问题类型') or '人工确认补充'}"


def build_draft_examples(candidates: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    drafts = []
    for item in candidates:
        business = item["业务线"]
        drafts.append(
            {
                "候选ID": item["候选ID"],
                "业务线": business,
                "来源": item["来源"],
                "拟申请规则标题": rule_title(item),
                "草案依据": item.get("建议动作", ""),
                "影响范围": business_scope(business),
                "回滚办法": rollback_plan(business),
                "审查状态": "待总管确认",
                "需总管确认": True,
                "正式生效": False,
                "写正式规则": False,
                "修改运行配置": False,
                "第80包当前状态": item.get("第80包当前状态", ""),
                "第80包允许下一状态": item.get("第80包允许下一状态", []),
            }
        )
    return {
        "名称": "三业务正式规则申请草案例子",
        "生成时间": generated_at,
        "说明": "示例只用于正式规则申请草案审查，不代表正式规则生效。",
        "覆盖业务": REQUIRED_BUSINESSES,
        "默认审查状态": "待总管确认",
        "需总管确认": True,
        "正式生效": False,
        "写正式规则": False,
        "修改运行配置": False,
        "申请草案": drafts,
    }


def build_review_rule(generated_at: str, state_machine: dict[str, Any]) -> dict[str, Any]:
    return {
        "名称": "正式规则申请草案审查规则",
        "版本": "formal-rule-application-draft-review-v1",
        "生成时间": generated_at,
        "承接状态机": str(SOURCE_80_STATE_MACHINE_JSON),
        "第80包状态集合": state_machine.get("状态集合", []),
        "适用业务": REQUIRED_BUSINESSES,
        "允许审查状态": ALLOWED_REVIEW_STATES,
        "默认审查状态": "待总管确认",
        "需总管确认": True,
        "正式生效": False,
        "写正式规则": False,
        "修改运行配置": False,
        "自动转正式规则": False,
        "必填字段": [
            "候选ID",
            "业务线",
            "来源",
            "拟申请规则标题",
            "影响范围",
            "回滚办法",
            "审查状态",
            "需总管确认",
            "正式生效",
        ],
        "硬性闸口": {
            "需总管确认": True,
            "正式生效": False,
            "写正式规则": False,
            "修改运行配置": False,
            "自动转正式规则": False,
        },
        "审查结论规则": [
            "候选可以形成正式规则申请草案，但草案不得自动转为正式规则。",
            "审查状态只能为待总管确认、驳回草案、冻结草案。",
            "总管确认前，任何草案都必须保持正式生效=false、写正式规则=false。",
            "影响范围与回滚办法缺失时必须驳回草案。",
        ],
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
    }


def build_reject_conditions(generated_at: str) -> dict[str, Any]:
    conditions = [
        "缺少候选ID、业务线、来源、拟申请规则标题、影响范围、回滚办法任一字段。",
        "业务线不属于税收、股票、视频。",
        "审查状态不属于待总管确认、驳回草案、冻结草案。",
        "需总管确认不是true。",
        "正式生效不是false，或写正式规则不是false。",
        "影响范围无法限定在候选说明/展示层/人工确认材料内。",
        "回滚办法不能明确撤回草案且不影响正式规则。",
        "出现真实发送企业微信、接n8n、接券商、交易、登录税局、接财税软件、自动转正式规则、修改总管面板、修改一键接续包、重载服务任一动作。",
    ]
    return {
        "名称": "正式规则申请草案驳回条件",
        "生成时间": generated_at,
        "适用业务": REQUIRED_BUSINESSES,
        "驳回条件": [{"序号": index + 1, "条件": value} for index, value in enumerate(conditions)],
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
    }


def build_manager_checklist(generated_at: str, drafts: list[dict[str, Any]]) -> dict[str, Any]:
    checklist = []
    for draft in drafts:
        checklist.append(
            {
                "候选ID": draft["候选ID"],
                "业务线": draft["业务线"],
                "拟申请规则标题": draft["拟申请规则标题"],
                "确认项": [
                    "候选来源可信且可追溯",
                    "影响范围已限定",
                    "回滚办法可执行",
                    "正式生效=false",
                    "写正式规则=false",
                    "需总管确认=true",
                ],
                "默认审查状态": "待总管确认",
                "需总管确认": True,
                "正式生效": False,
                "写正式规则": False,
            }
        )
    return {
        "名称": "总管确认清单",
        "生成时间": generated_at,
        "说明": "清单只用于总管审查申请草案，不修改总管面板。",
        "覆盖业务": REQUIRED_BUSINESSES,
        "确认清单": checklist,
        "需总管确认": True,
        "正式生效": False,
        "写正式规则": False,
    }


def build_review_rule_md(rule: dict[str, Any]) -> str:
    lines = [
        "# 正式规则申请草案审查规则",
        "",
        f"- 版本：{rule['版本']}",
        f"- 生成时间：{rule['生成时间']}",
        "- 默认审查状态：待总管确认",
        "- 需总管确认：true",
        "- 正式生效：false",
        "- 写正式规则：false",
        "",
        "## 必填字段",
        "",
    ]
    lines.extend(f"- {field}" for field in rule["必填字段"])
    lines.extend(["", "## 审查结论规则", ""])
    lines.extend(f"- {item}" for item in rule["审查结论规则"])
    lines.append("")
    return "\n".join(lines)


def build_reject_conditions_md(data: dict[str, Any]) -> str:
    lines = ["# 正式规则申请草案驳回条件", "", f"- 生成时间：{data['生成时间']}", ""]
    for item in data["驳回条件"]:
        lines.append(f"{item['序号']}. {item['条件']}")
    lines.append("")
    return "\n".join(lines)


def build_manager_checklist_md(data: dict[str, Any]) -> str:
    lines = [
        "# 总管确认清单",
        "",
        f"- 生成时间：{data['生成时间']}",
        "- 正式生效：false",
        "- 写正式规则：false",
        "",
        "| 候选ID | 业务线 | 拟申请规则标题 | 默认审查状态 |",
        "| --- | --- | --- | --- |",
    ]
    for item in data["确认清单"]:
        lines.append(f"| {item['候选ID']} | {item['业务线']} | {item['拟申请规则标题']} | {item['默认审查状态']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now_text()
    source_package = read_json_if_exists(SOURCE_80_PACKAGE_JSON)
    state_machine = read_json_if_exists(SOURCE_80_STATE_MACHINE_JSON)
    source_preview = read_json_if_exists(SOURCE_80_PREVIEW_JSON)
    candidates = load_source_candidates(source_preview)

    draft_examples = build_draft_examples(candidates, generated_at)
    review_rule = build_review_rule(generated_at, state_machine)
    reject_conditions = build_reject_conditions(generated_at)
    manager_checklist = build_manager_checklist(generated_at, draft_examples["申请草案"])
    package = {
        "名称": "三业务反馈候选正式规则申请草案审查包",
        "生成时间": generated_at,
        "状态": "three_business_formal_rule_application_draft_review_ready",
        "承接来源": {
            "第80包总包": str(SOURCE_80_PACKAGE_JSON),
            "第80包状态机": str(SOURCE_80_STATE_MACHINE_JSON),
            "第80包预演": str(SOURCE_80_PREVIEW_JSON),
        },
        "第80包状态": source_package.get("状态", ""),
        "读取范围": ["本包示例", "第80包状态机产物", "第80包状态迁移预演产物"],
        "覆盖业务": REQUIRED_BUSINESSES,
        "允许审查状态": ALLOWED_REVIEW_STATES,
        "默认审查状态": "待总管确认",
        "需总管确认": True,
        "正式生效": False,
        "写正式规则": False,
        "修改运行配置": False,
        "自动转正式规则": False,
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
        "输出文件": {
            "审查规则JSON": str(REVIEW_RULE_JSON),
            "审查规则Markdown": str(REVIEW_RULE_MD),
            "三业务申请草案例子JSON": str(DRAFT_EXAMPLES_JSON),
            "驳回条件JSON": str(REJECT_CONDITIONS_JSON),
            "驳回条件Markdown": str(REJECT_CONDITIONS_MD),
            "总管确认清单JSON": str(MANAGER_CHECKLIST_JSON),
            "总管确认清单Markdown": str(MANAGER_CHECKLIST_MD),
            "总包JSON": str(PACKAGE_JSON),
        },
    }

    write_json(REVIEW_RULE_JSON, review_rule)
    write_text(REVIEW_RULE_MD, build_review_rule_md(review_rule))
    write_json(DRAFT_EXAMPLES_JSON, draft_examples)
    write_json(REJECT_CONDITIONS_JSON, reject_conditions)
    write_text(REJECT_CONDITIONS_MD, build_reject_conditions_md(reject_conditions))
    write_json(MANAGER_CHECKLIST_JSON, manager_checklist)
    write_text(MANAGER_CHECKLIST_MD, build_manager_checklist_md(manager_checklist))
    write_json(PACKAGE_JSON, package)

    print(
        json.dumps(
            {
                "状态": package["状态"],
                "草案数": len(draft_examples["申请草案"]),
                "覆盖业务": package["覆盖业务"],
                "输出": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
