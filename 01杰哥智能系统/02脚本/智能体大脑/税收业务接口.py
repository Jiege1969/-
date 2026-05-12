"""
名称：税收业务接口.py
作用：读取 v3 税收业务系统的分类索引、处理计划和政策案例索引，供智能体大脑生成组合响应。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 税收业务系统本地输出，不抓取政策、不读取真实涉税资料、不替代正式判断。
创建/修改记录：2026-04-26 创建第一阶段税收业务只读接口模块；增加政策案例索引读取。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def _模块根目录() -> Path:
    return _系统根目录() / "02杰哥扩展系统" / "05税收业务系统"


def _读取_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as 异常:
        return {"状态": "异常", "错误": str(异常), "路径": str(path)}


def 税收业务状态() -> dict[str, Any]:
    root = _模块根目录()
    index = root / "03数据" / "02分类索引" / "税种分类索引_最新.json"
    policy_case_index = root / "03数据" / "02分类索引" / "税收政策案例索引_最新.json"
    plan = root / "03数据" / "04处理计划" / "税收业务处理计划_最新.json"
    return {
        "状态": "正常" if root.exists() else "异常",
        "模块路径": str(root),
        "最新分类索引存在": index.exists(),
        "最新政策案例索引存在": policy_case_index.exists(),
        "最新处理计划存在": plan.exists(),
        "安全边界": "只读状态，不抓取政策、不替代正式税务判断",
    }


def 读取税种分类索引() -> dict[str, Any]:
    path = _模块根目录() / "03数据" / "02分类索引" / "税种分类索引_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data


def 读取税收业务处理计划() -> dict[str, Any]:
    path = _模块根目录() / "03数据" / "04处理计划" / "税收业务处理计划_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data


def 读取税收政策案例索引() -> dict[str, Any]:
    path = _模块根目录() / "03数据" / "02分类索引" / "税收政策案例索引_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data
