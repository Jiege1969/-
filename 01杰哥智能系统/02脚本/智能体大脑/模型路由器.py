"""
名称：模型路由器.py
作用：按照任务类型、复杂度和本机资源策略选择本地大模型。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
创建/修改记录：2026-04-26 创建第一阶段最小可运行版本。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Ollama客户端 import 读取模型列表


默认模型分层: dict[str, list[str]] = {
    "快速模型": ["qwen2.5:7b", "deepseek-r1:7b"],
    "日常模型": ["qwen3:14b"],
    "深度模型": ["qwen3:30b", "deepseek-r1:32b"],
    "代码模型": ["qwen3-coder:30b"],
    "视觉模型": ["gemma3:27b"],
    "金融模型": ["mychen76/Fin-R1:Q5", "martain7r/finance-llama-8b:q4_k_m"],
}


任务到模型: dict[str, tuple[str, str]] = {
    "空输入": ("规则引擎", "不调用模型"),
    "普通对话": ("qwen3:14b", "qwen2.5:7b"),
    "知识库问答": ("qwen3:14b", "qwen3:30b"),
    "股票研究": ("qwen3:14b", "deepseek-r1:32b"),
    "视频制作": ("qwen3:14b", "qwen3:30b"),
    "本职工作": ("qwen3:14b", "qwen3:30b"),
    "代码开发": ("qwen3-coder:30b", "qwen3:30b"),
    "自动化办公": ("qwen3:14b", "qwen3-coder:30b"),
    "系统运维": ("qwen3-coder:30b", "qwen3:14b"),
}


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def 读取模型配置() -> dict[str, Any]:
    配置路径 = _系统根目录() / "00杰哥系统总管" / "01配置" / "machine" / "model_router.json"
    if not 配置路径.exists():
        return {"模型分层": 默认模型分层, "配置来源": "内置默认"}
    try:
        数据 = json.loads(配置路径.read_text(encoding="utf-8"))
        数据["配置来源"] = str(配置路径)
        return 数据
    except Exception as 异常:
        return {"模型分层": 默认模型分层, "配置来源": "内置默认", "配置读取错误": str(异常)}


def 读取大脑规则配置() -> dict[str, Any]:
    配置路径 = _系统根目录() / "01杰哥智能系统" / "01配置" / "智能体大脑规则.json"
    try:
        return json.loads(配置路径.read_text(encoding="utf-8"))
    except Exception:
        return {}


def 读取任务模型映射() -> dict[str, tuple[str, str]]:
    映射: dict[str, tuple[str, str]] = {}
    for 项 in 读取大脑规则配置().get("模型路由规则", []):
        任务类型 = 项.get("任务类型")
        首选 = 项.get("首选模型")
        兜底 = 项.get("兜底模型")
        if 任务类型 and 首选 and 兜底:
            映射[任务类型] = (首选, 兜底)
    return 映射 or 任务到模型


def 选择模型(任务识别结果: dict[str, Any] | None = None, 偏好: dict[str, Any] | None = None) -> dict[str, Any]:
    任务识别结果 = 任务识别结果 or {}
    偏好 = 偏好 or {}
    任务类型 = 任务识别结果.get("任务类型", "普通对话")
    复杂度 = 任务识别结果.get("复杂度", "低")
    风险等级 = 任务识别结果.get("风险等级", "低")

    任务模型映射 = 读取任务模型映射()
    首选, 兜底 = 任务模型映射.get(任务类型, ("qwen3:14b", "qwen2.5:7b"))
    if 复杂度 == "高" and 任务类型 not in ("代码开发", "股票研究", "空输入"):
        首选 = "qwen3:30b"
        兜底 = "qwen3:14b"

    if 偏好.get("速度优先") is True and 任务类型 != "代码开发":
        首选 = "qwen3:14b" if 首选 != "规则引擎" else 首选
        兜底 = "qwen2.5:7b"

    模型状态 = 读取模型列表()
    可用模型 = set(模型状态.get("模型列表", []))
    原始首选 = 首选
    原始兜底 = 兜底
    if 首选 != "规则引擎" and 可用模型:
        if 首选 not in 可用模型 and 兜底 in 可用模型:
            首选 = 兜底
        elif 首选 not in 可用模型 and "qwen3:14b" in 可用模型:
            首选 = "qwen3:14b"
            兜底 = "qwen2.5:7b" if "qwen2.5:7b" in 可用模型 else 原始兜底
        elif 首选 not in 可用模型:
            首选 = sorted(可用模型)[0]

    是否允许自动执行 = 风险等级 == "低"
    if 任务类型 == "空输入":
        是否允许自动执行 = True

    return {
        "任务类型": 任务类型,
        "复杂度": 复杂度,
        "首选模型": 首选,
        "兜底模型": 兜底,
        "是否允许自动执行": 是否允许自动执行,
        "需要人工确认": 风险等级 == "高",
        "路由理由": f"{任务类型}/{复杂度}/{风险等级} -> {首选}",
        "原始首选模型": 原始首选,
        "原始兜底模型": 原始兜底,
        "Ollama状态": {
            "状态": 模型状态.get("状态"),
            "地址": 模型状态.get("地址"),
            "模型数量": 模型状态.get("模型数量"),
        },
        "配置摘要": 读取模型配置().get("说明", "使用内置模型路由规则"),
        "规则来源": "智能体大脑规则.json" if 任务模型映射 != 任务到模型 else "内置默认",
    }
