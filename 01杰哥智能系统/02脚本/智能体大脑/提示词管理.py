"""
名称：提示词管理.py
作用：按任务类型读取 v3 智能体大脑提示词模板。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 配置目录内的提示词模板，不读取密钥。
创建/修改记录：2026-04-26 创建第一阶段提示词管理模块。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def 读取提示词配置() -> dict[str, Any]:
    配置路径 = _系统根目录() / "01杰哥智能系统" / "01配置" / "提示词模板.json"
    try:
        return json.loads(配置路径.read_text(encoding="utf-8"))
    except Exception:
        return {
            "默认提示词": "你是杰哥智能化系统v3的本地智能体大脑。回答要准确、简洁、稳健。",
            "模板": {},
        }


def 获取系统提示词(任务类型: str, 覆盖提示词: str | None = None) -> str:
    if 覆盖提示词:
        return 覆盖提示词
    配置 = 读取提示词配置()
    模板 = 配置.get("模板", {})
    return 模板.get(任务类型) or 配置.get("默认提示词", "")
