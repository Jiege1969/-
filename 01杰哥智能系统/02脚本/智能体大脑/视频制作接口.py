"""
名称：视频制作接口.py
作用：读取 v3 视频制作系统的任务计划、脚本草稿、分镜计划和状态，供智能体大脑生成组合响应。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 视频制作系统本地输出，不处理真实媒体、不上传、不发布。
创建/修改记录：2026-04-26 创建第一阶段视频制作只读接口模块。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def _视频模块根目录() -> Path:
    return _系统根目录() / "02杰哥扩展系统" / "02视频制作系统"


def _读取_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as 异常:
        return {"状态": "异常", "错误": str(异常), "路径": str(path)}


def 视频制作状态() -> dict[str, Any]:
    root = _视频模块根目录()
    plan = root / "03数据" / "04任务计划" / "视频制作计划_最新.json"
    script = root / "03数据" / "02脚本草稿" / "视频脚本草稿_最新.json"
    storyboard = root / "03数据" / "03分镜计划" / "视频分镜计划_最新.json"
    return {
        "状态": "正常" if root.exists() else "异常",
        "模块路径": str(root),
        "最新计划存在": plan.exists(),
        "最新脚本草稿存在": script.exists(),
        "最新分镜计划存在": storyboard.exists(),
        "安全边界": "只读状态，不处理真实媒体、不上传、不发布",
    }


def 读取视频制作计划() -> dict[str, Any]:
    path = _视频模块根目录() / "03数据" / "04任务计划" / "视频制作计划_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data


def 读取视频脚本草稿() -> dict[str, Any]:
    path = _视频模块根目录() / "03数据" / "02脚本草稿" / "视频脚本草稿_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data


def 读取视频分镜计划() -> dict[str, Any]:
    path = _视频模块根目录() / "03数据" / "03分镜计划" / "视频分镜计划_最新.json"
    data = _读取_json(path)
    data["路径"] = str(path)
    return data
