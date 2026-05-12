# -*- coding: utf-8 -*-
"""
名称：agent_shadow_common.py
作用：轮次012视频创作智能体影子层本地生成工具函数。
安全边界：只写本地影子文档；不调用真实大模型、不发送企业微信、不连接 n8n、不渲染、不发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
DATA_ROOT = ROOT / "03数据" / "18轮次012视频工厂总控层"
SHADOW_ROOT = DATA_ROOT / "智能体影子层"
ARCHIVE_ROOT = SHADOW_ROOT / "archive"


BOUNDARY_STATEMENTS = [
    "本文件是轮次012视频创作智能体影子层设计，不是正式上线能力。",
    "不调用真实大模型，只预留未来适配器契约。",
    "不发送企业微信，只保留未来输入输出终端口径。",
    "不读取真实素材、不访问平台、不连接真实账号。",
    "不接 n8n。",
    "不真实渲染、不真实发布。",
    "生成放行、真实渲染放行、发布放行必须拆开。",
    "“发吧”“生成”“发布”等命令只能解析为待复核意图，不能直接执行。",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_value(value: Any, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            lines.append(f"{prefix}- {key}：")
            lines.extend(render_value(item, indent + 1))
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(render_value(item, indent + 1))
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}- {value}")
    return lines


def render_markdown(title: str, data: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{data.get('生成时间', now_text())}",
        "- 真实系统触发：否",
        "",
        "## 内容",
        "",
    ]
    for key, value in data.items():
        if key in {"生成时间", "边界声明"}:
            continue
        lines.append(f"### {key}")
        lines.extend(render_value(value))
        lines.append("")
    lines.extend(["## 边界声明", ""])
    for item in data.get("边界声明", BOUNDARY_STATEMENTS):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_artifact(name: str, title: str, data: dict[str, Any]) -> None:
    data = {
        "生成时间": now_text(),
        **data,
        "边界声明": data.get("边界声明", BOUNDARY_STATEMENTS),
    }
    markdown = render_markdown(title, data)
    stamp = stamp_text()
    write_json(SHADOW_ROOT / f"{name}_最新.json", data)
    write_text(SHADOW_ROOT / f"{name}_最新.md", markdown)
    write_json(ARCHIVE_ROOT / f"{name}_{stamp}.json", data)
    write_text(ARCHIVE_ROOT / f"{name}_{stamp}.md", markdown)
