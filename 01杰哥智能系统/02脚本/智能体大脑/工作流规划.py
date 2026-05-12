"""
名称：工作流规划.py
作用：读取 v3 工作流注册表，并按任务类型生成 n8n 工作流规划结果。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只生成工作流计划，不触发 n8n，不执行外部动作。
创建/修改记录：2026-04-26 创建第一阶段工作流规划模块。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def 读取工作流注册表() -> dict[str, Any]:
    配置路径 = _系统根目录() / "01杰哥智能系统" / "01配置" / "工作流注册表.json"
    try:
        数据 = json.loads(配置路径.read_text(encoding="utf-8"))
        数据["配置来源"] = str(配置路径)
        return 数据
    except Exception as 异常:
        return {
            "说明": "内置兜底工作流注册表",
            "配置来源": "内置默认",
            "配置读取错误": str(异常),
            "工作流": [],
        }


def 工作流列表() -> list[dict[str, Any]]:
    return list(读取工作流注册表().get("工作流", []))


def 规划工作流(任务识别结果: dict[str, Any] | None = None) -> dict[str, Any]:
    任务识别结果 = 任务识别结果 or {}
    任务类型 = 任务识别结果.get("任务类型", "普通对话")
    风险等级 = 任务识别结果.get("风险等级", "低")
    候选 = [
        项 for 项 in 工作流列表()
        if 任务类型 in 项.get("适用任务", [])
    ]
    if not 候选:
        return {
            "任务类型": 任务类型,
            "是否需要工作流": False,
            "候选工作流": [],
            "是否允许自动触发": False,
            "需要人工确认": 风险等级 == "高",
            "当前动作": "无匹配工作流，仅返回模型答复",
        }

    是否允许自动触发 = all(bool(项.get("是否允许自动触发", False)) for 项 in 候选)
    return {
        "任务类型": 任务类型,
        "是否需要工作流": True,
        "候选工作流": 候选,
        "是否允许自动触发": 是否允许自动触发 and 风险等级 == "低",
        "需要人工确认": True,
        "当前动作": "仅生成工作流计划，不触发n8n",
    }
