# -*- coding: utf-8 -*-
"""
名称：生成人工确认回执状态回写草案.py
作用：根据人工确认单生成回执模板和状态回写建议草案，补齐人工确认后的闭环结构。
触发方式：python 生成人工确认回执状态回写草案.py
依赖：Python标准库；人工确认回执状态回写规则.json；日常任务人工确认单_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成回执草案；不回写任务状态；不签发许可令；不触发执行器；不触发n8n；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建人工确认回执状态回写草案脚本。
标识：human-confirmation-receipt-state-writeback-draft-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_receipt(item: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    task_type = item.get("任务类型", "")
    task_name = item.get("任务名称", "")
    blockers = [word for word in rules.get("强制阻断类型", []) if word in task_type or word in task_name]
    allowed_decisions = rules.get("允许决策", [])
    if blockers:
        decision_options = [value for value in allowed_decisions if value != "同意进入许可令草案"]
        default_decision = "拒绝执行"
        suggested_state = "禁止执行"
    else:
        decision_options = allowed_decisions
        default_decision = "延后处理"
        suggested_state = rules.get("状态建议映射", {}).get(default_decision, "待处理")
    return {
        "回执编号": f"RCPT-{item.get('任务编号', 'UNKNOWN')}",
        "来源任务编号": item.get("任务编号"),
        "来源任务名称": task_name,
        "任务类型": task_type,
        "当前状态": item.get("当前状态"),
        "允许决策": decision_options,
        "默认决策": default_decision,
        "建议状态": suggested_state,
        "命中阻断类型": blockers,
        "确认人": "待填写",
        "确认时间": "待填写",
        "确认意见": "待填写",
        "是否回写任务状态": False,
        "是否签发许可令": False,
        "是否触发执行器": False,
        "是否触发n8n": False,
        "是否真实发送": False,
        "是否写正式库": False,
        "是否写旧系统": False
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "人工确认回执状态回写规则.json"
    confirmation_path = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "人工确认单" / "日常任务人工确认单_最新.json"
    rules = load_json(rule_path)
    confirmations = load_json(confirmation_path) if confirmation_path.exists() else []
    receipts = [build_receipt(item, rules) for item in confirmations]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "人工确认单": str(confirmation_path),
        "默认开关": rules.get("默认开关", {}),
        "回执草案": receipts,
        "汇总": {
            "回执数量": len(receipts),
            "阻断回执数量": sum(1 for item in receipts if item["命中阻断类型"]),
            "回写任务状态数量": sum(1 for item in receipts if item["是否回写任务状态"]),
            "签发许可令数量": sum(1 for item in receipts if item["是否签发许可令"]),
            "触发执行器数量": sum(1 for item in receipts if item["是否触发执行器"]),
            "触发n8n数量": sum(1 for item in receipts if item["是否触发n8n"]),
            "真实发送数量": sum(1 for item in receipts if item["是否真实发送"]),
            "写正式库数量": sum(1 for item in receipts if item["是否写正式库"]),
            "写旧系统数量": sum(1 for item in receipts if item["是否写旧系统"])
        },
        "当前结论": "人工确认回执状态回写草案已生成；当前只形成回执模板和建议状态，不自动回写或执行。"
    }
    output_dir = manager / "03数据" / "人工确认回执"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "人工确认回执状态回写草案_最新.json"
    latest = output_dir / "人工确认回执状态回写草案_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"回执数量": len(receipts), "阻断回执数量": report["汇总"]["阻断回执数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
