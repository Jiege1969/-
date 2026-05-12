"""
名称：Ollama客户端.py
作用：读取本机 Ollama 服务状态、已安装模型列表，并提供受控文本生成能力。
触发方式：由 v3 智能体大脑服务入口和模型路由器导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
创建/修改记录：2026-04-26 创建第一阶段只读客户端；2026-04-30 默认切换到v3 Ollama端口29134。
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import request


默认地址 = "http://127.0.0.1:29134"


def Ollama地址() -> str:
    return os.environ.get("JIEGE_OLLAMA_URL", 默认地址).rstrip("/")


def 读取模型列表(超时秒: int = 5) -> dict[str, Any]:
    地址 = Ollama地址()
    try:
        with request.urlopen(f"{地址}/api/tags", timeout=超时秒) as 响应:
            数据 = json.loads(响应.read().decode("utf-8"))
        模型 = [项.get("name", "") for 项 in 数据.get("models", []) if 项.get("name")]
        return {
            "状态": "正常",
            "地址": 地址,
            "模型数量": len(模型),
            "模型列表": 模型,
        }
    except Exception as 异常:
        return {
            "状态": "异常",
            "地址": 地址,
            "模型数量": 0,
            "模型列表": [],
            "错误": str(异常),
        }


def 生成文本(
    模型: str,
    提示词: str,
    系统提示: str = "",
    最大输出: int = 256,
    温度: float = 0.2,
    超时秒: int = 180,
) -> dict[str, Any]:
    地址 = Ollama地址()
    if not 模型 or 模型 == "规则引擎":
        return {
            "状态": "跳过",
            "地址": 地址,
            "模型": 模型,
            "答复": "",
            "原因": "规则引擎任务不需要调用大模型",
        }

    最大输出 = max(32, min(int(最大输出), 1024))
    温度 = max(0.0, min(float(温度), 1.5))
    payload = {
        "model": 模型,
        "prompt": 提示词,
        "system": 系统提示,
        "stream": False,
        "options": {
            "num_predict": 最大输出,
            "temperature": 温度,
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{地址}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=超时秒) as 响应:
            结果 = json.loads(响应.read().decode("utf-8"))
        return {
            "状态": "成功",
            "地址": 地址,
            "模型": 模型,
            "答复": 结果.get("response", ""),
            "耗时纳秒": 结果.get("total_duration"),
            "完成原因": "正常",
        }
    except Exception as 异常:
        return {
            "状态": "失败",
            "地址": 地址,
            "模型": 模型,
            "答复": "",
            "错误": str(异常),
            "完成原因": "超时或调用异常，已降级返回路由结果",
        }
