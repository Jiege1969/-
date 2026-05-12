# -*- coding: utf-8 -*-
"""
只读验证03进化最终封版一致性复核包与交付后巡检种子。

本脚本只读取本地 JSON/Markdown 文件并输出验证结果到 stdout；
不连接网络、不调用 Redis、不触发 n8n、不调用 webhook、不写正式库、
不调用券商接口、不下单、不自动交易、不修改被验证文件。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "31最终封版一致性复核与交付后巡检种子"
O_DIR = ROOT / "03数据" / "30最终规则封版冻结包"
RECYCLE_DIR = Path(r"D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收")

FILES = {
    "O规则封版JSON": O_DIR / "03进化最终规则封版包_最新.json",
    "O反退化清单JSON": O_DIR / "反退化冻结清单_最新.json",
    "复核包JSON": BASE_DIR / "最终封版一致性复核包_最新.json",
    "复核包MD": BASE_DIR / "最终封版一致性复核包_最新.md",
    "巡检种子JSON": BASE_DIR / "交付后只读反退化巡检种子_最新.json",
    "巡检种子MD": BASE_DIR / "交付后只读反退化巡检种子_最新.md",
}

REQUIRED_PRINCIPLES = ["学逻辑不搬壳子", "总管唯一中枢", "任务契约优先", "SQLite影子台账", "Redis/n8n升级门槛", "真实动作闸门", "股票analysis-only", "并行收口格式", "进度口径不得虚高", "旧口径可纠偏"]
REQUIRED_CORE_SCOPE = ["总管唯一中枢", "任务契约优先", "SQLite影子台账", "Redis/n8n升级门槛", "真实动作闸门", "股票analysis-only", "进度口径不得虚高", "旧口径可纠偏"]
REQUIRED_FORBIDDEN = ["外部网络调用", "Redis连接或真实队列写入", "n8n导入、启用、触发或webhook调用", "企业微信真实发送", "正式库写入", "券商接口调用", "下单或自动交易", "修改被巡检文件", "绕过00总管建立第二中枢"]
EXPECTED_RECYCLE_JSON = RECYCLE_DIR / "03进化系统_最终封版一致性复核回收报告_最新.json"
EXPECTED_RECYCLE_MD = RECYCLE_DIR / "03进化系统_最终封版一致性复核回收报告_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def all_false(mapping: dict[str, Any]) -> bool:
    return all(value is False for value in mapping.values())


def main() -> int:
    checks: list[dict[str, Any]] = []
    real_action_count = 0
    external_service_count = 0

    for name, file_path in FILES.items():
        add_check(checks, f"{name}存在", file_path.exists(), str(file_path))

    if not all(item["通过"] for item in checks):
        failed = [item for item in checks if not item["通过"]]
        print(json.dumps({"名称": "03进化最终封版一致性复核与巡检种子只读验证", "状态": "失败", "通过": len(checks) - len(failed), "失败": len(failed), "阻断项": len(failed), "真实动作数量": real_action_count, "外部服务调用数量": external_service_count, "检查明细": checks}, ensure_ascii=False, indent=2))
        return 1

    o_rule = load_json(FILES["O规则封版JSON"])
    o_freeze = load_json(FILES["O反退化清单JSON"])
    review = load_json(FILES["复核包JSON"])
    seed = load_json(FILES["巡检种子JSON"])
    review_md = load_text(FILES["复核包MD"])
    seed_md = load_text(FILES["巡检种子MD"])

    o_rule_names = [item.get("规则名") for item in o_rule.get("最终冻结原则", [])]
    o_freeze_names = [item.get("冻结项") for item in o_freeze.get("反退化检查项", [])]
    review_names = [item.get("规则名") for item in review.get("复核项", [])]
    seed_names = [item.get("巡检项") for item in seed.get("巡检种子项", [])]

    add_check(checks, "O封版原则数量为10", len(o_rule_names) == 10, len(o_rule_names))
    add_check(checks, "O反退化检查项数量为10", len(o_freeze_names) == 10, len(o_freeze_names))
    add_check(checks, "W复核项数量为10", len(review_names) == 10, len(review_names))
    add_check(checks, "W巡检种子数量为10", len(seed_names) == 10, len(seed_names))
    add_check(checks, "O/W原则名称完全一致", o_rule_names == review_names == seed_names, {"O": o_rule_names, "W": review_names, "seed": seed_names})

    for name in REQUIRED_PRINCIPLES:
        add_check(checks, f"原则覆盖：{name}", name in review_names and name in seed_names and name in o_freeze_names, name)
        add_check(checks, f"Markdown覆盖：{name}", name in review_md and name in seed_md, name)

    scope = seed.get("巡检范围", [])
    for name in REQUIRED_CORE_SCOPE:
        add_check(checks, f"巡检范围覆盖：{name}", name in scope, scope)

    forbidden = seed.get("全局禁止行为", [])
    for item in REQUIRED_FORBIDDEN:
        add_check(checks, f"全局禁止行为存在：{item}", item in forbidden, item)

    boundary = review.get("执行边界", {})
    add_check(checks, "复核包执行边界全部为true", all(value is True for value in boundary.values()), boundary)
    add_check(checks, "巡检种子安全边界全部关闭", all_false(seed.get("安全边界", {})), seed.get("安全边界", {}))

    result = review.get("一致性复核结果", {})
    real_action_count = int(result.get("真实动作数量", -1))
    external_service_count = int(result.get("外部服务调用数量", -1))
    add_check(checks, "一致性复核结论通过", result.get("结论") == "通过" and result.get("全部一致") is True, result)
    add_check(checks, "冲突项数量为0", result.get("冲突项数量") == 0, result.get("冲突项数量"))
    add_check(checks, "阻断项数量为0", result.get("阻断项数量") == 0, result.get("阻断项数量"))
    add_check(checks, "真实动作数量为0", real_action_count == 0, real_action_count)
    add_check(checks, "外部服务调用数量为0", external_service_count == 0, external_service_count)

    progress = review.get("进度口径复核", {})
    add_check(checks, "进度口径不得虚高", progress.get("不得虚高") is True and progress.get("未验收不得称完成") is True and progress.get("dry_run不得冒充上线") is True, progress)

    legacy = review.get("旧口径纠偏复核", {})
    add_check(checks, "旧口径可纠偏且不删历史", legacy.get("允许纠偏") is True and legacy.get("不得删除历史证据") is True and legacy.get("必须声明替代范围") is True, legacy)

    acceptance = seed.get("验收口径", {})
    add_check(checks, "巡检种子验收口径要求10项", acceptance.get("巡检项数量") == 10, acceptance)
    add_check(checks, "巡检种子要求真实动作0", acceptance.get("真实动作数量必须为") == 0, acceptance)
    add_check(checks, "巡检种子要求外部服务0", acceptance.get("外部服务调用数量必须为") == 0, acceptance)

    seed_items = seed.get("巡检种子项", [])
    add_check(checks, "巡检种子均有阻断条件", all(item.get("阻断条件") for item in seed_items), seed_items)
    add_check(checks, "巡检种子均声明只读输入", all(item.get("只读输入") for item in seed_items), seed_items)
    add_check(checks, "巡检种子均声明通过条件", all("真实动作数量=0" in item.get("通过条件", "") for item in seed_items), seed_items)

    add_check(checks, "固定回收报告JSON路径正确", EXPECTED_RECYCLE_JSON.exists(), str(EXPECTED_RECYCLE_JSON))
    add_check(checks, "固定回收报告MD路径正确", EXPECTED_RECYCLE_MD.exists(), str(EXPECTED_RECYCLE_MD))

    failed = [item for item in checks if not item["通过"]]
    output = {
        "名称": "03进化最终封版一致性复核与巡检种子只读验证",
        "验证日期": "2026-05-05",
        "验证方式": "只读本地文件解析",
        "状态": "通过" if not failed else "失败",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "阻断项": len(failed),
        "真实动作数量": real_action_count,
        "外部服务调用数量": external_service_count,
        "禁止行为确认": {"外部网络调用": False, "Redis连接": False, "n8n触发": False, "webhook调用": False, "正式库写入": False, "券商接口调用": False, "下单或自动交易": False, "修改被验证文件": False},
        "检查明细": checks,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
