# -*- coding: utf-8 -*-
"""
名称：生成视频任务ID与放行链一致性复核卡.py
作用：汇总轮次012任务单、人工复核链一致性检查、生成/发布放行清单，形成只读复核卡。
安全边界：只读本地文件并写入测试与审核目录；不修改任务单或放行清单，不真实渲染，不真实发布，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\02视频制作系统")
ROUND_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
OUTPUT_DIR = ROUND_DIR / "测试与审核"
LATEST_JSON = OUTPUT_DIR / "视频任务ID与放行链一致性复核卡_最新.json"
LATEST_MD = OUTPUT_DIR / "视频任务ID与放行链一致性复核卡_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def contains_task_line(text: str, task_id: str) -> str:
    for line in text.splitlines():
        if task_id and task_id in line:
            return line
    return "未找到当前任务"


def build_card() -> dict[str, Any]:
    task_path = ROUND_DIR / "视频工厂任务单_最新.json"
    consistency_path = ROUND_DIR / "人工复核链" / "一致性检查" / "复核结果与放行清单一致性检查_最新.json"
    generation_list_path = ROUND_DIR / "放行清单" / "视频生成放行清单_最新.md"
    publish_list_path = ROUND_DIR / "放行清单" / "视频发布放行清单_最新.md"

    task = read_json(task_path)
    consistency = read_json(consistency_path)
    generation_text = read_text(generation_list_path)
    publish_text = read_text(publish_list_path)
    task_id = str(task.get("任务ID") or consistency.get("任务ID") or "")
    generation_control = task.get("生成控制", {})

    manual_review_items = [
        item for item in consistency.get("检查结果", [])
        if isinstance(item, dict) and item.get("结果") == "需人工核对"
    ]
    blockers = list(consistency.get("阻断事项", []))
    if generation_control.get("允许真实渲染") is not False:
        blockers.append("任务单未明确禁止真实渲染，需总管确认")
    if generation_control.get("允许自动发布") is not False:
        blockers.append("任务单未明确禁止自动发布，需总管确认")
    if contains_task_line(publish_text, task_id) == "未找到当前任务":
        blockers.append("发布放行清单未登记当前任务，阻断发布")

    return {
        "名称": "视频任务ID与放行链一致性复核卡",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "任务状态": task.get("状态", "未知"),
        "来源文件": {
            "任务单": str(task_path),
            "一致性检查": str(consistency_path),
            "生成放行清单": str(generation_list_path),
            "发布放行清单": str(publish_list_path),
        },
        "链路摘录": {
            "人工复核状态": generation_control.get("人工复核状态"),
            "允许真实渲染": generation_control.get("允许真实渲染"),
            "允许自动发布": generation_control.get("允许自动发布"),
            "生成放行清单行": contains_task_line(generation_text, task_id),
            "发布放行清单行": contains_task_line(publish_text, task_id),
            "一致性检查任务ID": consistency.get("任务ID"),
        },
        "需人工核对项": manual_review_items,
        "阻断事项": blockers,
        "结论": "只读复核卡已生成；任务ID链路存在人工核对项，真实渲染和发布继续阻断。",
        "安全边界": {
            "修改任务单": False,
            "修改生成放行清单": False,
            "修改发布放行清单": False,
            "真实渲染": False,
            "真实发布": False,
            "访问平台": False,
            "连接真实账号": False,
            "触发n8n": False,
            "真实发送企业微信": False,
        },
    }


def build_markdown(card: dict[str, Any]) -> str:
    review_rows = [
        f"| {item.get('检查项')} | {item.get('结果')} | {item.get('说明')} |"
        for item in card["需人工核对项"]
    ] or ["| 无 | pass | 无需人工核对项 |"]
    blocker_rows = [f"- {item}" for item in card["阻断事项"]] or ["- 无"]
    return "\n".join(
        [
            "# 视频任务ID与放行链一致性复核卡",
            "",
            f"- 生成时间：{card['生成时间']}",
            f"- 任务ID：{card['任务ID']}",
            f"- 任务状态：{card['任务状态']}",
            f"- 结论：{card['结论']}",
            "",
            "## 链路摘录",
            "",
            f"- 人工复核状态：{card['链路摘录'].get('人工复核状态')}",
            f"- 允许真实渲染：{card['链路摘录'].get('允许真实渲染')}",
            f"- 允许自动发布：{card['链路摘录'].get('允许自动发布')}",
            f"- 生成放行清单行：{card['链路摘录'].get('生成放行清单行')}",
            f"- 发布放行清单行：{card['链路摘录'].get('发布放行清单行')}",
            "",
            "## 需人工核对项",
            "",
            "| 检查项 | 结果 | 说明 |",
            "| --- | --- | --- |",
            *review_rows,
            "",
            "## 阻断事项",
            "",
            *blocker_rows,
            "",
            "## 安全边界",
            "",
            "- 只读生成复核卡，不改任务单或放行清单。",
            "- 不真实渲染，不真实发布，不访问平台，不连接真实账号。",
            "- 不触发 n8n，不真实发送企业微信。",
        ]
    )


def main() -> int:
    card = build_card()
    write_json(LATEST_JSON, card)
    write_text(LATEST_MD, build_markdown(card))
    print(json.dumps({"任务ID": card["任务ID"], "需人工核对": len(card["需人工核对项"]), "阻断事项": len(card["阻断事项"]), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
