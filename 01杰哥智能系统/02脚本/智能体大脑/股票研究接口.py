"""
名称：股票研究接口.py
作用：读取 v3 股票研究系统的计划、报告和状态，供智能体大脑生成组合响应。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 股票研究系统本地输出，不联网、不抓行情、不调用券商、不执行交易。
创建/修改记录：2026-04-26 创建第一阶段股票研究只读接口模块。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def _股票模块根目录() -> Path:
    return _系统根目录() / "02杰哥扩展系统" / "01股票研究系统"


def _读取_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as 异常:
        return {"状态": "异常", "错误": str(异常), "路径": str(path)}


def 股票研究状态() -> dict[str, Any]:
    root = _股票模块根目录()
    plan = root / "03数据" / "02研究计划" / "股票研究计划_最新.json"
    report = root / "03数据" / "03研究报告" / "股票研究报告_最新.md"
    return {
        "状态": "正常" if root.exists() else "异常",
        "模块路径": str(root),
        "最新计划存在": plan.exists(),
        "最新报告存在": report.exists(),
        "安全边界": "只读状态，不抓行情、不交易",
    }


def 读取股票研究计划() -> dict[str, Any]:
    path = _股票模块根目录() / "03数据" / "02研究计划" / "股票研究计划_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data


def 读取股票研究报告(最大字符: int = 2000) -> dict[str, Any]:
    path = _股票模块根目录() / "03数据" / "03研究报告" / "股票研究报告_最新.md"
    最大字符 = max(200, min(int(最大字符), 8000))
    if not path.exists():
        return {
            "状态": "未生成",
            "路径": str(path),
            "内容": "",
        }
    try:
        text = path.read_text(encoding="utf-8")
        return {
            "状态": "正常",
            "路径": str(path),
            "字符数": len(text),
            "内容": text[:最大字符],
        }
    except Exception as 异常:
        return {
            "状态": "异常",
            "路径": str(path),
            "错误": str(异常),
            "内容": "",
        }


def 读取股票风险摘要() -> dict[str, Any]:
    path = _股票模块根目录() / "03数据" / "03研究报告" / "股票风险摘要_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data
