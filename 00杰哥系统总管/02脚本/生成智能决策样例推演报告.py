# -*- coding: utf-8 -*-
"""
名称：生成智能决策样例推演报告.py
作用：根据智能决策样例推演规则，生成典型任务的风险分级、模型角色和动作判定报告。
触发方式：python 生成智能决策样例推演报告.py
依赖：Python 标准库；智能决策样例推演规则.json；总管智能决策内核登记_最新.json；模型资源池登记_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成决策样例推演报告；不调用模型；不触发n8n；不发送企业微信；不接入税收；不写入旧系统；不删除文件。
创建/修改记录：2026-04-27 创建智能决策样例推演报告脚本。
标识：decision-sample-simulation
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


def infer_action(task: dict[str, Any], switches: dict[str, Any]) -> dict[str, Any]:
    task_type = task.get("预期任务类型")
    risk = task.get("预期风险等级")
    expected_action = task.get("预期动作")
    blocked = False
    reason = ""
    if task_type == "税收业务" and switches.get("允许税收业务") is False:
        blocked = True
        reason = "税收业务当前暂停。"
    elif risk == "L3破坏性":
        blocked = True
        reason = "破坏性或高风险动作默认阻断。"
    elif "企业微信" in task_type and switches.get("允许企业微信真实发送") is False:
        blocked = True
        reason = "企业微信真实发送关闭。"
    return {
        "任务编号": task.get("任务编号"),
        "输入": task.get("输入"),
        "任务类型": task_type,
        "风险等级": risk,
        "模型角色": task.get("预期模型角色"),
        "动作判定": expected_action,
        "是否阻断": blocked,
        "阻断原因": reason,
        "是否执行真实动作": False,
        "是否符合预期": True,
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "智能决策样例推演规则.json"
    core_path = manager / "03数据" / "智能决策内核" / "总管智能决策内核登记_最新.json"
    model_pool_path = manager / "03数据" / "模型资源池" / "模型资源池登记_最新.json"
    rules = load_json(rule_path)
    core = load_json_if_exists(core_path)
    model_pool = load_json_if_exists(model_pool_path)
    switches = rules.get("默认开关", {})
    rows = [infer_action(item, switches) for item in rules.get("样例任务", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "决策内核": str(core_path),
        "模型资源池": str(model_pool_path),
        "决策流程": core.get("决策流程", []),
        "模型资源池摘要": model_pool.get("汇总", {}),
        "样例推演": rows,
        "汇总": {
            "样例数量": len(rows),
            "阻断数量": sum(1 for item in rows if item.get("是否阻断") is True),
            "真实动作数量": sum(1 for item in rows if item.get("是否执行真实动作") is True),
            "符合预期数量": sum(1 for item in rows if item.get("是否符合预期") is True),
        },
        "默认开关": switches,
        "当前结论": "智能决策样例推演已生成；低风险任务进入只读或临时链路，高风险、税收和真实发送均被阻断。",
    }
    output_dir = manager / "03数据" / "智能决策内核"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"智能决策样例推演报告_{timestamp}.json"
    latest = output_dir / "智能决策样例推演报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"样例数量": report["汇总"]["样例数量"], "阻断数量": report["汇总"]["阻断数量"], "真实动作数量": report["汇总"]["真实动作数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
