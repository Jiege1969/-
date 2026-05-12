"""
名称：本职工作接口.py
作用：读取 v3 本职工作系统的任务计划和草稿框架，供智能体大脑生成组合响应。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 本职工作系统本地输出，不读取真实涉密资料、不自动发送。
创建/修改记录：2026-04-26 创建第一阶段本职工作只读接口模块。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def _模块根目录() -> Path:
    return _系统根目录() / "02杰哥扩展系统" / "03本职工作系统"


def _读取_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as 异常:
        return {"状态": "异常", "错误": str(异常), "路径": str(path)}


def 本职工作状态() -> dict[str, Any]:
    root = _模块根目录()
    plan = root / "03数据" / "02任务计划" / "办公材料计划_最新.json"
    draft = root / "03数据" / "03输出草稿" / "办公材料草稿框架_最新.json"
    return {
        "状态": "正常" if root.exists() else "异常",
        "模块路径": str(root),
        "最新计划存在": plan.exists(),
        "最新草稿框架存在": draft.exists(),
        "安全边界": "只读状态，不读取真实涉密资料、不自动发送",
    }


def 读取办公材料计划() -> dict[str, Any]:
    path = _模块根目录() / "03数据" / "02任务计划" / "办公材料计划_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data


def 读取办公材料草稿框架() -> dict[str, Any]:
    path = _模块根目录() / "03数据" / "03输出草稿" / "办公材料草稿框架_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data
