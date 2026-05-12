# -*- coding: utf-8 -*-
"""
只读验证03进化最终规则封版包。

本脚本只读取本地 JSON/Markdown 文件并输出验证结果到 stdout；
不连接网络、不调用 Redis、不触发 n8n、不写正式库、不执行真实动作。
"""

from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\03杰哥进化系统\03数据\30最终规则封版冻结包")
RULE_JSON = BASE_DIR / "03进化最终规则封版包_最新.json"
RULE_MD = BASE_DIR / "03进化最终规则封版包_最新.md"
FREEZE_JSON = BASE_DIR / "反退化冻结清单_最新.json"
FREEZE_MD = BASE_DIR / "反退化冻结清单_最新.md"

REQUIRED_PRINCIPLES = [
    "学逻辑不搬壳子",
    "总管唯一中枢",
    "任务契约优先",
    "SQLite影子台账",
    "Redis/n8n升级门槛",
    "真实动作闸门",
    "股票analysis-only",
    "并行收口格式",
    "进度口径不得虚高",
    "旧口径可纠偏",
]

REQUIRED_BLOCKERS = [
    "触发外部服务",
    "执行真实动作",
    "写正式库",
    "调用Redis服务",
    "导入、启用或触发n8n workflow",
    "调用webhook",
    "调用券商接口",
    "下单或自动交易",
    "未验收宣称完成",
    "绕过00总管建立第二中枢",
]

FORBIDDEN_TRUE_FIELDS = [
    ("执行边界", "不触发外部服务"),
    ("执行边界", "不执行真实动作"),
    ("执行边界", "不调用Redis服务"),
    ("执行边界", "不触发n8n"),
    ("执行边界", "不调用webhook"),
    ("执行边界", "不写正式库"),
    ("执行边界", "不调用券商接口"),
    ("执行边界", "不下单或自动交易"),
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def add_check(checks: list[dict], name: str, passed: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    checks: list[dict] = []
    real_action_count = 0
    external_service_count = 0

    files = [RULE_JSON, RULE_MD, FREEZE_JSON, FREEZE_MD]
    for path in files:
        add_check(checks, f"文件存在：{path.name}", path.exists(), str(path))

    if not all(path.exists() for path in files):
        result = {
            "名称": "03进化系统最终规则封版包只读验证",
            "验证方式": "只读本地文件解析",
            "状态": "失败",
            "通过": sum(1 for item in checks if item["通过"]),
            "失败": sum(1 for item in checks if not item["通过"]),
            "真实动作数量": real_action_count,
            "外部服务调用数量": external_service_count,
            "检查明细": checks,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    rule = load_json(RULE_JSON)
    freeze = load_json(FREEZE_JSON)
    rule_md = load_text(RULE_MD)
    freeze_md = load_text(FREEZE_MD)

    rule_names = [item.get("规则名") for item in rule.get("最终冻结原则", [])]
    freeze_names = [item.get("冻结项") for item in freeze.get("反退化检查项", [])]

    add_check(checks, "封版原则数量为10", len(rule_names) == 10, f"实际数量={len(rule_names)}")
    add_check(checks, "反退化检查项数量为10", len(freeze_names) == 10, f"实际数量={len(freeze_names)}")

    for name in REQUIRED_PRINCIPLES:
        add_check(checks, f"封版原则存在：{name}", name in rule_names, name)
        add_check(checks, f"反退化冻结项存在：{name}", name in freeze_names, name)
        add_check(checks, f"Markdown包含原则：{name}", name in rule_md and name in freeze_md, name)

    blockers = freeze.get("全局阻断项", [])
    for blocker in REQUIRED_BLOCKERS:
        add_check(checks, f"全局阻断项存在：{blocker}", blocker in blockers, blocker)

    boundary = rule.get("执行边界", {})
    for group, field in FORBIDDEN_TRUE_FIELDS:
        add_check(checks, f"{group}确认：{field}", boundary.get(field) is True, str(boundary.get(field)))

    conclusion = rule.get("封版结论", {})
    real_action_count = int(conclusion.get("真实动作数量", -1))
    external_service_count = int(conclusion.get("外部服务调用数量", -1))
    add_check(checks, "真实动作数量为0", real_action_count == 0, f"实际数量={real_action_count}")
    add_check(checks, "外部服务调用数量为0", external_service_count == 0, f"实际数量={external_service_count}")

    acceptance = freeze.get("验收口径", {})
    add_check(checks, "验收方式为只读本地文件解析", acceptance.get("验收方式") == "只读本地文件解析", str(acceptance.get("验收方式")))
    add_check(checks, "封版状态为已封版", conclusion.get("状态") == "已封版", str(conclusion.get("状态")))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "03进化系统最终规则封版包只读验证",
        "验证时间": "2026-05-05",
        "验证方式": "只读本地文件解析",
        "状态": "通过" if not failed else "失败",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "阻断项": len(failed),
        "真实动作数量": real_action_count,
        "外部服务调用数量": external_service_count,
        "禁止行为确认": {
            "外部网络调用": False,
            "Redis连接": False,
            "n8n触发": False,
            "webhook调用": False,
            "正式库写入": False,
            "券商接口调用": False,
            "下单或自动交易": False,
            "修改被验证文件": False
        },
        "检查明细": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
