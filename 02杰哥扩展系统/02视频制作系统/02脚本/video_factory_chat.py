# -*- coding: utf-8 -*-
"""
名称：video_factory_chat.py
作用：轮次012视频工厂聊天式入口，把用户一句想法转成任务单和对话草案。
触发方式：python video_factory_chat.py --input "我想聊聊为什么人过30，交朋友就变成了一种奢侈。"
依赖：Python 标准库；task_generator.generate_task。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只写入轮次012本地预演目录；不触发真实渲染、发布、企业微信真实外发或外部执行器。
创建/修改记录：2026-05-07 创建轮次012视频工厂总控层聊天入口。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from task_generator import generate_task


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
OUTPUT_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_dialogue_draft(task: dict[str, Any]) -> str:
    task_def = task.get("任务定义", {})
    control = task.get("生成控制", {})
    gate_items = control.get("门禁检查项", [])
    gate_text = "\n".join(f"- {item}" for item in gate_items)
    confirm_items = task.get("等待用户确认项", [])
    confirm_text = "\n".join(f"- {item}" for item in confirm_items)
    return "\n".join([
        "# 轮次012 视频工厂对话草案",
        "",
        f"- 生成时间：{task.get('任务生成时间')}",
        f"- 任务ID：{task.get('任务ID')}",
        f"- 会话来源：{task.get('会话来源')}",
        f"- 会话ID：{task.get('会话ID') or '未提供'}",
        f"- 当前状态：{task.get('状态')}",
        "",
        "## 1. 用户原始输入",
        "",
        str(task.get("原始输入", "")),
        "",
        "## 2. 系统识别结果",
        "",
        f"- 主题：{task_def.get('主题')}",
        f"- 表达角度：{task_def.get('表达角度')}",
        f"- 受众人群：{task_def.get('受众人群')}",
        f"- 视频类型：{task_def.get('视频类型')}",
        f"- 目标画面比例：{', '.join(task_def.get('目标画面比例', []))}",
        f"- 关键情绪：{task_def.get('关键情绪')}",
        "",
        "## 3. 门禁状态",
        "",
        f"- 阶段：{control.get('阶段')}",
        f"- 允许真实渲染：{control.get('允许真实渲染')}",
        f"- 允许调用外部素材API：{control.get('允许调用外部素材API')}",
        f"- 允许自动发布：{control.get('允许自动发布')}",
        f"- 人工复核状态：{control.get('人工复核状态')}",
        "",
        "## 4. 门禁检查项",
        "",
        gate_text,
        "",
        "## 5. 等待用户确认项",
        "",
        confirm_text,
        "",
        "## 6. 生成建议",
        "",
        str(task.get("生成建议", "")),
        "",
        "## 7. 当前结论",
        "",
        "预演完成，等待人工复核。真实渲染、自动发布和企业微信真实外发均未放行。",
        "",
    ])


def save_outputs(task: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    latest_json = OUTPUT_DIR / "视频工厂任务单_最新.json"
    latest_md = OUTPUT_DIR / "视频工厂对话草案_最新.md"
    dialogue_draft = build_dialogue_draft(task)
    write_json(latest_json, task)
    write_text(latest_md, dialogue_draft)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = str(task.get("任务ID", "VF-UNKNOWN"))
    # 企业微信可能连续输入多条指令；归档直接写唯一文件，减少并发复制 latest 文件时的占用风险。
    write_json(ARCHIVE_DIR / f"视频工厂任务单_{task_id}_{timestamp}.json", task)
    write_text(ARCHIVE_DIR / f"视频工厂对话草案_{task_id}_{timestamp}.md", dialogue_draft)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012视频工厂聊天式任务入口")
    parser.add_argument("--input", required=True, help="用户在聊天入口输入的一句话想法")
    parser.add_argument("--session-id", default="", help="企业微信或其他聊天入口传入的会话ID")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task = generate_task(args.input, session_id=args.session_id)
    save_outputs(task)
    print("预演完成，等待人工复核")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
