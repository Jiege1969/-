# -*- coding: utf-8 -*-
"""
名称：生成总管智能决策内核登记.py
作用：根据总管智能决策内核规则，生成系统指挥协调、模型角色、OpenClaw边界和执行器权限登记报告。
触发方式：python 生成总管智能决策内核登记.py
依赖：Python 标准库；总管智能决策内核规则.json；模型资源池登记_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成决策内核登记报告；不调用模型；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建总管智能决策内核登记脚本。
标识：manager-decision-core-register
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
    rule_path = manager / "01配置" / "总管智能决策内核规则.json"
    model_pool_path = manager / "03数据" / "模型资源池" / "模型资源池登记_最新.json"
    rules = load_json(rule_path)
    model_pool = load_json_if_exists(model_pool_path)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "最高原则": rules.get("最高原则", []),
        "决策流程": rules.get("决策流程", []),
        "风险分级": rules.get("风险分级", {}),
        "模型角色": rules.get("模型角色", {}),
        "模型资源池摘要": model_pool.get("汇总", {}),
        "OpenClaw边界": rules.get("OpenClaw边界", {}),
        "当前默认开关": rules.get("当前默认开关", {}),
        "指挥链": [
            "宪章与规则",
            "00杰哥系统总管",
            "任务队列",
            "n8n统一调度",
            "模型路由器",
            "执行器脚本",
            "统一日志",
            "03进化系统复盘提炼"
        ],
        "职责分工": {
            "大模型": "思考、分析、拆解、总结、提炼，不直接执行真实动作。",
            "OpenClaw": "企业微信消息入口和出口，不做业务判断。",
            "n8n": "唯一逻辑调度中心。",
            "执行器": "在任务队列和闸口授权后执行具体动作。",
            "闸口": "阻断真实抓取、发送、写库和破坏性操作。",
            "进化系统": "从日志、成功、失败中提炼经验并反向优化规则。"
        },
        "当前结论": "总管智能决策内核已登记；当前不调用模型、不触发n8n、不放开真实动作。",
    }
    output_dir = manager / "03数据" / "智能决策内核"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"总管智能决策内核登记_{timestamp}.json"
    latest = output_dir / "总管智能决策内核登记_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"阶段": report["阶段"], "决策流程数": len(report["决策流程"]), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
