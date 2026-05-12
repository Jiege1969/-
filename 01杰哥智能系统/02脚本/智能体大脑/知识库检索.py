"""
名称：知识库检索.py
作用：读取 v3 知识库配置、索引清单和全文索引，提供状态查询、元数据检索与轻量全文检索。
触发方式：由 v3 智能体大脑服务入口导入调用。
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 知识库配置、索引清单和全文索引，不读取旧系统资料，不写入数据库。
创建/修改记录：2026-04-26 创建第一阶段知识库检索占位模块；升级为轻量全文索引检索。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _系统根目录() -> Path:
    return Path(__file__).resolve().parents[3]


def _配置路径() -> Path:
    return _系统根目录() / "01杰哥智能系统" / "01配置" / "知识库配置.json"


def 读取知识库配置() -> dict[str, Any]:
    try:
        return json.loads(_配置路径().read_text(encoding="utf-8"))
    except Exception as 异常:
        return {
            "状态": "异常",
            "错误": str(异常),
            "数据目录": {},
            "支持扩展名": [],
        }


def _最新索引路径() -> Path | None:
    配置 = 读取知识库配置()
    索引目录 = 配置.get("数据目录", {}).get("索引清单")
    if not 索引目录:
        return None
    latest = Path(索引目录) / "知识库索引清单_最新.json"
    if latest.exists():
        return latest
    return None


def _最新全文索引路径() -> Path | None:
    配置 = 读取知识库配置()
    索引目录 = 配置.get("数据目录", {}).get("索引清单")
    if not 索引目录:
        return None
    latest = Path(索引目录) / "知识库全文索引_最新.json"
    if latest.exists():
        return latest
    return None


def 读取最新索引() -> dict[str, Any]:
    路径 = _最新索引路径()
    if 路径 is None:
        return {
            "状态": "未生成",
            "文档数量": 0,
            "文档": [],
        }
    try:
        数据 = json.loads(路径.read_text(encoding="utf-8"))
        数据["状态"] = "正常"
        数据["索引路径"] = str(路径)
        return 数据
    except Exception as 异常:
        return {
            "状态": "异常",
            "文档数量": 0,
            "文档": [],
            "错误": str(异常),
            "索引路径": str(路径),
        }


def 读取最新全文索引() -> dict[str, Any]:
    路径 = _最新全文索引路径()
    if 路径 is None:
        return {
            "状态": "未生成",
            "文档数量": 0,
            "分块数量": 0,
            "文档": [],
            "分块": [],
        }
    try:
        数据 = json.loads(路径.read_text(encoding="utf-8"))
        数据["状态"] = "正常"
        数据["全文索引路径"] = str(路径)
        return 数据
    except Exception as 异常:
        return {
            "状态": "异常",
            "文档数量": 0,
            "分块数量": 0,
            "文档": [],
            "分块": [],
            "错误": str(异常),
            "全文索引路径": str(路径),
        }


def 知识库状态() -> dict[str, Any]:
    配置 = 读取知识库配置()
    索引 = 读取最新索引()
    全文索引 = 读取最新全文索引()
    return {
        "状态": "正常" if 索引.get("状态") in ("正常", "未生成") and 全文索引.get("状态") in ("正常", "未生成") else "异常",
        "配置状态": 配置.get("状态", "未知"),
        "原始文档目录": 配置.get("数据目录", {}).get("原始文档"),
        "索引路径": 索引.get("索引路径"),
        "全文索引路径": 全文索引.get("全文索引路径"),
        "文档数量": 索引.get("文档数量", 0),
        "全文分块数量": 全文索引.get("分块数量", 0),
        "支持扩展名": 配置.get("支持扩展名", []),
        "当前阶段": "本地全文索引检索，不执行向量检索",
    }


def 检索知识库(关键词: str | None, 限制: int = 5) -> dict[str, Any]:
    关键词 = (关键词 or "").strip().lower()
    限制 = max(1, min(int(限制), 20))
    全文索引 = 读取最新全文索引()
    全文命中 = []
    if 关键词 and 全文索引.get("状态") == "正常":
        for 分块 in 全文索引.get("分块", []):
            内容 = 分块.get("内容", "")
            if 关键词 in 内容.lower() or 关键词 in 分块.get("文件名", "").lower():
                摘要 = 内容[:220]
                全文命中.append(
                    {
                        "匹配来源": "全文索引",
                        "文件名": 分块.get("文件名"),
                        "路径": 分块.get("路径"),
                        "分块序号": 分块.get("分块序号"),
                        "摘要": 摘要,
                        "清洗文本路径": 分块.get("清洗文本路径"),
                    }
                )
                if len(全文命中) >= 限制:
                    break
    if 全文命中:
        return {
            "状态": "成功",
            "关键词": 关键词,
            "命中数量": len(全文命中),
            "命中": 全文命中,
            "说明": "当前使用本地全文索引检索，尚未接入向量检索。",
        }

    索引 = 读取最新索引()
    文档 = 索引.get("文档", [])
    if not 关键词:
        命中 = 文档[:限制]
    else:
        命中 = [
            项 for 项 in 文档
            if 关键词 in 项.get("文件名", "").lower()
            or 关键词 in 项.get("路径", "").lower()
            or 关键词 in 项.get("文档类型", "").lower()
        ][:限制]

    return {
        "状态": "成功",
        "关键词": 关键词,
        "命中数量": len(命中),
        "命中": 命中,
        "说明": "未命中全文索引时，回退到索引清单元数据检索；尚未接入向量检索。",
    }
