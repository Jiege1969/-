# -*- coding: utf-8 -*-
"""生成三业务正式规则申请草案冲突扫描与签收台账包。

本包承接第83包正式规则申请草案审查产物，只生成冲突扫描规则、
签收台账字段和本包示例草案；不写正式规则，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包"
SOURCE_83_DIR = ROOT / "03数据" / "83三业务反馈候选正式规则申请草案审查包"

PACKAGE_JSON = DATA_DIR / "三业务正式规则申请草案冲突扫描与签收台账包_最新.json"
SCAN_RULE_JSON = DATA_DIR / "冲突扫描规则_最新.json"
SCAN_RULE_MD = DATA_DIR / "冲突扫描规则_最新.md"
SIGNOFF_FIELD_JSON = DATA_DIR / "签收台账字段_最新.json"
SIGNOFF_FIELD_MD = DATA_DIR / "签收台账字段_最新.md"
DRAFT_EXAMPLE_JSON = DATA_DIR / "三业务正式规则申请草案扫描示例_最新.json"

REQUIRED_BUSINESSES = ["税收", "股票", "视频"]
REQUIRED_CONFLICT_TYPES = [
    "红线冲突",
    "跨业务职责冲突",
    "旧口径回潮",
    "正式规则自动生效",
    "缺少回滚办法",
    "缺少总管确认",
]
FORBIDDEN_ACTIONS = [
    "真实发送企业微信",
    "接 n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
    "改总管面板",
    "改一键接续包",
    "重载服务",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def find_source_83_files() -> list[str]:
    if not SOURCE_83_DIR.exists():
        return []
    return [str(path) for path in sorted(SOURCE_83_DIR.glob("*_最新.json"))]


def fallback_drafts(generated_at: str) -> list[dict[str, Any]]:
    return [
        {
            "草案ID": "RULE-DRAFT-TAX-001",
            "业务": "税收",
            "来源": "第83包申请草案审查产物/本包示例",
            "草案标题": "税收反馈候选正式规则申请草案：补齐资料口径与人工复核说明",
            "申请内容摘要": "仅补齐税收反馈候选的资料清单、适用前提和人工复核提示，不登录税局、不接财税软件。",
            "影响范围": "税收反馈候选展示与人工复核说明",
            "回滚办法": "撤回草案扫描记录，保留第83包审查结果，不同步到正式规则。",
            "需总管确认": True,
            "正式生效": False,
            "写正式规则": False,
            "签收状态": "待签收",
            "生成时间": generated_at,
        },
        {
            "草案ID": "RULE-DRAFT-STOCK-001",
            "业务": "股票",
            "来源": "第83包申请草案审查产物/本包示例",
            "草案标题": "股票反馈候选正式规则申请草案：强化非交易风险提示",
            "申请内容摘要": "仅补齐展示层风险提示和非交易建议声明，不接券商、不交易、不触发自动化配置。",
            "影响范围": "股票反馈候选展示文案与人工确认提示",
            "回滚办法": "撤回草案扫描记录，恢复候选说明原文，不触发任何外部交易链路。",
            "需总管确认": True,
            "正式生效": False,
            "写正式规则": False,
            "签收状态": "待签收",
            "生成时间": generated_at,
        },
        {
            "草案ID": "RULE-DRAFT-VIDEO-001",
            "业务": "视频",
            "来源": "第83包申请草案审查产物/本包示例",
            "草案标题": "视频反馈候选正式规则申请草案：补齐分镜占位与发布前确认",
            "申请内容摘要": "仅补齐视频反馈候选的分镜占位、口播节奏和人工确认点，不渲染、不发布、不重载服务。",
            "影响范围": "视频反馈候选分镜说明与人工确认提示",
            "回滚办法": "撤回草案扫描记录，恢复候选分镜说明，不触发渲染发布或服务重载。",
            "需总管确认": True,
            "正式生效": False,
            "写正式规则": False,
            "签收状态": "待签收",
            "生成时间": generated_at,
        },
    ]


def build_scan_rule(generated_at: str, source_files: list[str]) -> dict[str, Any]:
    rules = [
        {
            "冲突类型": "红线冲突",
            "判定口径": "草案内容或签收动作出现外部系统、真实发送、交易、登录、重载等红线动作即命中。",
            "处理动作": "阻断签收，退回人工修订，保持正式生效=false。",
        },
        {
            "冲突类型": "跨业务职责冲突",
            "判定口径": "税收、股票、视频任一草案越权修改其他业务职责、入口或处置链路即命中。",
            "处理动作": "标记待总管确认，并要求拆分业务边界。",
        },
        {
            "冲突类型": "旧口径回潮",
            "判定口径": "草案重新引入已被审查否定的旧口径、旧状态或旧默认自动吸收表达即命中。",
            "处理动作": "标记为需复核，要求说明新旧口径差异。",
        },
        {
            "冲突类型": "正式规则自动生效",
            "判定口径": "草案或台账出现正式生效=true、写正式规则=true、自动转正式规则=true即命中。",
            "处理动作": "强制失败，禁止写入正式规则。",
        },
        {
            "冲突类型": "缺少回滚办法",
            "判定口径": "草案缺少可执行回滚办法、撤回方式或恢复来源说明即命中。",
            "处理动作": "退回补齐回滚办法后重新扫描。",
        },
        {
            "冲突类型": "缺少总管确认",
            "判定口径": "草案或签收台账未声明需总管确认=true即命中。",
            "处理动作": "保持待签收，不允许进入正式生效链路。",
        },
    ]
    return {
        "名称": "三业务正式规则申请草案冲突扫描规则",
        "版本": "three-business-rule-draft-conflict-scan-v1",
        "生成时间": generated_at,
        "承接来源": source_files,
        "覆盖业务": REQUIRED_BUSINESSES,
        "冲突类型": REQUIRED_CONFLICT_TYPES,
        "扫描规则": rules,
        "默认签收状态": "待签收",
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "自动转正式规则": False,
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
    }


def build_signoff_fields(generated_at: str) -> dict[str, Any]:
    fields = [
        {"字段": "台账ID", "必填": True, "说明": "签收台账唯一编号"},
        {"字段": "草案ID", "必填": True, "说明": "关联正式规则申请草案编号"},
        {"字段": "业务", "必填": True, "说明": "税收/股票/视频之一"},
        {"字段": "草案标题", "必填": True, "说明": "待扫描草案标题"},
        {"字段": "冲突扫描状态", "必填": True, "默认值": "待扫描"},
        {"字段": "命中冲突类型", "必填": True, "默认值": []},
        {"字段": "签收状态", "必填": True, "默认值": "待签收"},
        {"字段": "签收人", "必填": False, "默认值": ""},
        {"字段": "签收时间", "必填": False, "默认值": ""},
        {"字段": "需总管确认", "必填": True, "默认值": True},
        {"字段": "正式生效", "必填": True, "默认值": False},
        {"字段": "写正式规则", "必填": True, "默认值": False},
        {"字段": "回滚办法", "必填": True, "说明": "缺少则命中缺少回滚办法"},
    ]
    return {
        "名称": "三业务正式规则申请草案签收台账字段",
        "版本": "three-business-rule-draft-signoff-ledger-v1",
        "生成时间": generated_at,
        "字段": fields,
        "默认状态": "待签收",
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "自动转正式规则": False,
        "允许业务": REQUIRED_BUSINESSES,
    }


def build_md_for_scan_rule(rule: dict[str, Any]) -> str:
    lines = [
        "# 三业务正式规则申请草案冲突扫描规则",
        "",
        f"- 版本：{rule['版本']}",
        f"- 生成时间：{rule['生成时间']}",
        "- 默认签收状态：待签收",
        "- 正式生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "| 冲突类型 | 判定口径 | 处理动作 |",
        "| --- | --- | --- |",
    ]
    for item in rule["扫描规则"]:
        lines.append(f"| {item['冲突类型']} | {item['判定口径']} | {item['处理动作']} |")
    lines.append("")
    return "\n".join(lines)


def build_md_for_signoff(fields: dict[str, Any]) -> str:
    lines = [
        "# 三业务正式规则申请草案签收台账字段",
        "",
        "- 默认状态：待签收",
        "- 正式生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "| 字段 | 必填 | 默认值/说明 |",
        "| --- | --- | --- |",
    ]
    for item in fields["字段"]:
        note = item.get("默认值", item.get("说明", ""))
        lines.append(f"| {item['字段']} | {str(item['必填']).lower()} | {note} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now_text()
    source_files = find_source_83_files()
    drafts = fallback_drafts(generated_at)
    scan_rule = build_scan_rule(generated_at, source_files)
    signoff_fields = build_signoff_fields(generated_at)
    examples = {
        "名称": "三业务正式规则申请草案扫描示例",
        "生成时间": generated_at,
        "承接来源": source_files,
        "覆盖业务": REQUIRED_BUSINESSES,
        "默认状态": "待签收",
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "草案": drafts,
    }
    package = {
        "名称": "三业务正式规则申请草案冲突扫描与签收台账包",
        "状态": "three_business_rule_draft_conflict_signoff_ready",
        "生成时间": generated_at,
        "承接第83包": True,
        "承接来源": source_files,
        "覆盖业务": REQUIRED_BUSINESSES,
        "冲突类型": REQUIRED_CONFLICT_TYPES,
        "默认状态": "待签收",
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "自动转正式规则": False,
        "触发外部系统": False,
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
        "输出文件": {
            "冲突扫描规则JSON": str(SCAN_RULE_JSON),
            "冲突扫描规则Markdown": str(SCAN_RULE_MD),
            "签收台账字段JSON": str(SIGNOFF_FIELD_JSON),
            "签收台账字段Markdown": str(SIGNOFF_FIELD_MD),
            "三业务正式规则申请草案扫描示例": str(DRAFT_EXAMPLE_JSON),
        },
    }

    write_json(SCAN_RULE_JSON, scan_rule)
    write_text(SCAN_RULE_MD, build_md_for_scan_rule(scan_rule))
    write_json(SIGNOFF_FIELD_JSON, signoff_fields)
    write_text(SIGNOFF_FIELD_MD, build_md_for_signoff(signoff_fields))
    write_json(DRAFT_EXAMPLE_JSON, examples)
    write_json(PACKAGE_JSON, package)
    print(json.dumps({"通过": True, "输出目录": str(DATA_DIR), "草案数": len(drafts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
