# -*- coding: utf-8 -*-
"""执行三业务正式规则申请草案冲突扫描。

只读取本包规则/示例和第83包草案审查产物，生成扫描结果与签收台账；
不写正式规则，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包"

PACKAGE_JSON = DATA_DIR / "三业务正式规则申请草案冲突扫描与签收台账包_最新.json"
SCAN_RULE_JSON = DATA_DIR / "冲突扫描规则_最新.json"
SIGNOFF_FIELD_JSON = DATA_DIR / "签收台账字段_最新.json"
DRAFT_EXAMPLE_JSON = DATA_DIR / "三业务正式规则申请草案扫描示例_最新.json"
SCAN_RESULT_JSON = DATA_DIR / "三业务草案冲突扫描结果_最新.json"
SCAN_RESULT_MD = DATA_DIR / "三业务草案冲突扫描结果_最新.md"
SIGNOFF_LEDGER_JSON = DATA_DIR / "签收台账_最新.json"
SIGNOFF_LEDGER_MD = DATA_DIR / "签收台账_最新.md"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_CONFLICT_TYPES = {
    "红线冲突",
    "跨业务职责冲突",
    "旧口径回潮",
    "正式规则自动生效",
    "缺少回滚办法",
    "缺少总管确认",
}
FORBIDDEN_KEYWORDS = {
    "真实发送企业微信": "红线冲突",
    "接 n8n": "红线冲突",
    "接n8n": "红线冲突",
    "接券商": "红线冲突",
    "交易": "红线冲突",
    "登录税局": "红线冲突",
    "接财税软件": "红线冲突",
    "自动转正式规则": "正式规则自动生效",
    "改总管面板": "红线冲突",
    "改一键接续包": "红线冲突",
    "重载服务": "红线冲突",
}


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


def detect_conflicts(draft: dict[str, Any]) -> list[str]:
    conflicts: set[str] = set()
    combined_text = " ".join(str(value) for value in draft.values())
    business = draft.get("业务")

    for keyword, conflict_type in FORBIDDEN_KEYWORDS.items():
        if keyword in combined_text and "不" not in combined_text[max(0, combined_text.find(keyword) - 2) : combined_text.find(keyword)]:
            conflicts.add(conflict_type)

    if draft.get("正式生效") is not False or draft.get("写正式规则") is not False:
        conflicts.add("正式规则自动生效")
    if draft.get("需总管确认") is not True:
        conflicts.add("缺少总管确认")
    if not str(draft.get("回滚办法", "")).strip():
        conflicts.add("缺少回滚办法")

    other_businesses = REQUIRED_BUSINESSES - {business}
    impact_scope = str(draft.get("影响范围", ""))
    title = str(draft.get("草案标题", ""))
    for other in other_businesses:
        if other in impact_scope or title.startswith(other):
            conflicts.add("跨业务职责冲突")

    if any(old_word in combined_text for old_word in ["自动吸收", "默认生效", "旧口径", "直接转正"]):
        conflicts.add("旧口径回潮")

    return sorted(conflicts, key=lambda name: list(REQUIRED_CONFLICT_TYPES).index(name) if name in REQUIRED_CONFLICT_TYPES else 99)


def build_result_md(report: dict[str, Any]) -> str:
    lines = [
        "# 三业务草案冲突扫描结果",
        "",
        f"- 扫描时间：{report['扫描时间']}",
        f"- 错误数：{report['错误数']}",
        "- 正式生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "| 草案ID | 业务 | 签收状态 | 命中冲突类型 |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["扫描明细"]:
        conflicts = "、".join(item["命中冲突类型"]) if item["命中冲突类型"] else "无"
        lines.append(f"| {item['草案ID']} | {item['业务']} | {item['签收状态']} | {conflicts} |")
    lines.append("")
    return "\n".join(lines)


def build_ledger_md(ledger: dict[str, Any]) -> str:
    lines = [
        "# 三业务正式规则申请草案签收台账",
        "",
        "- 默认状态：待签收",
        "- 正式生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "| 台账ID | 草案ID | 业务 | 冲突扫描状态 | 签收状态 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in ledger["台账"]:
        lines.append(
            f"| {item['台账ID']} | {item['草案ID']} | {item['业务']} | "
            f"{item['冲突扫描状态']} | {item['签收状态']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    required_files = [PACKAGE_JSON, SCAN_RULE_JSON, SIGNOFF_FIELD_JSON, DRAFT_EXAMPLE_JSON]
    for path in required_files:
        if not path.exists():
            errors.append(f"必要输入不存在：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    scan_rule = read_json(SCAN_RULE_JSON) if SCAN_RULE_JSON.exists() else {}
    signoff_fields = read_json(SIGNOFF_FIELD_JSON) if SIGNOFF_FIELD_JSON.exists() else {}
    examples = read_json(DRAFT_EXAMPLE_JSON) if DRAFT_EXAMPLE_JSON.exists() else {}
    drafts = examples.get("草案", []) if isinstance(examples, dict) else []

    generated_at = now_text()
    scan_details: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    for index, draft in enumerate(drafts, start=1):
        conflicts = detect_conflicts(draft)
        scan_state = "通过" if not conflicts else "待处理"
        signoff_state = "待签收"
        detail = {
            "草案ID": draft.get("草案ID", f"UNKNOWN-{index:03d}"),
            "业务": draft.get("业务", ""),
            "草案标题": draft.get("草案标题", ""),
            "冲突扫描状态": scan_state,
            "命中冲突类型": conflicts,
            "签收状态": signoff_state,
            "需总管确认": True,
            "正式生效": False,
            "写正式规则": False,
            "自动转正式规则": False,
            "触发外部系统": False,
            "回滚办法": draft.get("回滚办法", ""),
        }
        scan_details.append(detail)
        ledger_rows.append(
            {
                "台账ID": f"SIGNOFF-{index:03d}",
                "草案ID": detail["草案ID"],
                "业务": detail["业务"],
                "草案标题": detail["草案标题"],
                "冲突扫描状态": scan_state,
                "命中冲突类型": conflicts,
                "签收状态": signoff_state,
                "签收人": "",
                "签收时间": "",
                "需总管确认": True,
                "正式生效": False,
                "写正式规则": False,
                "自动转正式规则": False,
                "回滚办法": detail["回滚办法"],
            }
        )

    businesses = {item.get("业务") for item in scan_details}
    if businesses != REQUIRED_BUSINESSES:
        errors.append("扫描结果必须覆盖税收/股票/视频")
    if set(scan_rule.get("冲突类型", [])) != REQUIRED_CONFLICT_TYPES:
        errors.append("冲突扫描规则类型不齐全")
    for name, data in [("生成包", package), ("冲突扫描规则", scan_rule), ("签收字段", signoff_fields)]:
        if data.get("正式生效") is not False:
            errors.append(f"{name} 必须声明正式生效=false")
        if data.get("写正式规则") is not False:
            errors.append(f"{name} 必须声明写正式规则=false")
        if data.get("需总管确认") is not True:
            errors.append(f"{name} 必须声明需总管确认=true")

    report = {
        "名称": "三业务草案冲突扫描结果",
        "扫描时间": generated_at,
        "读取文件": [str(path) for path in required_files],
        "覆盖业务": sorted(businesses),
        "冲突类型": sorted(REQUIRED_CONFLICT_TYPES),
        "扫描明细": scan_details,
        "汇总": {
            "草案数": len(scan_details),
            "业务数": len(businesses),
            "命中冲突草案数": sum(1 for item in scan_details if item["命中冲突类型"]),
            "待签收数": sum(1 for item in scan_details if item["签收状态"] == "待签收"),
        },
        "默认状态": "待签收",
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "自动转正式规则": False,
        "触发外部系统": False,
        "错误数": len(errors),
        "错误": errors,
    }
    ledger = {
        "名称": "三业务正式规则申请草案签收台账",
        "生成时间": generated_at,
        "字段来源": str(SIGNOFF_FIELD_JSON),
        "默认状态": "待签收",
        "正式生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "自动转正式规则": False,
        "台账": ledger_rows,
        "错误数": len(errors),
        "错误": errors,
    }

    write_json(SCAN_RESULT_JSON, report)
    write_text(SCAN_RESULT_MD, build_result_md(report))
    write_json(SIGNOFF_LEDGER_JSON, ledger)
    write_text(SIGNOFF_LEDGER_MD, build_ledger_md(ledger))
    print(json.dumps({"通过": len(errors) == 0, "错误数": len(errors), "扫描结果": str(SCAN_RESULT_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
