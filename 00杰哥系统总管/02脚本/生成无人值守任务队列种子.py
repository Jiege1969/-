# -*- coding: utf-8 -*-
"""
名称：生成无人值守任务队列种子.py
作用：根据无人值守任务队列种子规则，生成dry-run样例任务队列。
触发方式：python 生成无人值守任务队列种子.py
依赖：Python 标准库；无人值守任务队列种子规则.json；无人值守任务状态机报告_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成样例任务队列；不触发执行器；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建无人值守任务队列种子脚本。
标识：unattended-task-queue-seed
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_json_if_exists(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "无人值守任务队列种子规则.json"
    state_machine_path = manager / "03数据" / "无人值守守护" / "无人值守任务状态机报告_最新.json"
    rules = load_json(rule_path)
    state_machine = load_json_if_exists(state_machine_path)
    allowed_states = set(state_machine.get("允许状态", []))
    queue = []
    for item in rules.get("样例任务", []):
        queue.append({
            "任务编号": item.get("任务编号"),
            "任务名称": item.get("任务名称"),
            "所属模块": item.get("所属模块"),
            "风险等级": item.get("风险等级"),
            "当前状态": item.get("初始状态"),
            "状态是否合法": item.get("初始状态") in allowed_states,
            "执行器标识": item.get("执行器标识"),
            "是否触发执行器": False,
            "是否触发n8n": False,
            "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "队列状态": rules.get("队列状态"),
        "规则文件": str(rule_path),
        "状态机文件": str(state_machine_path),
        "任务队列": queue,
        "默认开关": rules.get("默认开关", {}),
        "汇总": {
            "任务数量": len(queue),
            "禁止执行数量": sum(1 for item in queue if item.get("当前状态") == "禁止执行"),
            "触发执行器数量": sum(1 for item in queue if item.get("是否触发执行器") is True),
            "触发n8n数量": sum(1 for item in queue if item.get("是否触发n8n") is True),
        },
        "当前结论": "无人值守任务队列种子已生成；当前不触发执行器和n8n。",
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守任务队列种子_最新.json"
    latest = output_dir / "无人值守任务队列种子_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"任务数量": report["汇总"]["任务数量"], "触发执行器数量": report["汇总"]["触发执行器数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
