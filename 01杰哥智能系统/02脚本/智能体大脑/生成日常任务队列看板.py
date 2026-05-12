"""
名称：生成日常任务队列看板.py
作用：读取日常任务人工确认队列，生成可阅读的任务看板文档。
触发方式：python 生成日常任务队列看板.py；验证阶段可使用 --demo。
依赖：Python 标准库；任务队列 jsonl 文件。
所属系统：01杰哥智能系统
安全边界：只读取任务队列并写入新系统文档；不触发n8n、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建日常任务队列看板脚本。
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="read temporary rehearsal queue")
    args = parser.parse_args()
    root = system_root()
    if args.demo:
        queue = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "任务队列_最新.jsonl"
        output = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "日常任务队列看板.md"
    else:
        queue = root / "01杰哥智能系统" / "03数据" / "任务队列" / "01待人工确认" / "任务队列_最新.jsonl"
        output = root / "01杰哥智能系统" / "07文档" / "日常任务队列看板.md"
    tasks = read_jsonl(queue)
    type_counter = Counter(item.get("路由结果", {}).get("任务类型", "未知") for item in tasks)
    paused = sum(1 for item in tasks if item.get("路由结果", {}).get("是否暂停") is True)
    lines = [
        "# 日常任务队列看板",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 队列文件：{queue}",
        f"- 任务数量：{len(tasks)}",
        f"- 暂停任务：{paused}",
        "",
        "## 类型统计",
        "",
    ]
    for name, count in sorted(type_counter.items()):
        lines.append(f"- {name}：{count}")
    lines.extend([
        "",
        "## 待人工确认任务",
        "",
        "| 任务ID | 类型 | 风险 | 状态 | 目标系统 | 摘要 |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for item in tasks:
        route = item.get("路由结果", {})
        content = item.get("原始内容", "").replace("|", " ")
        summary = content[:40] + ("..." if len(content) > 40 else "")
        lines.append(f"| {item.get('任务ID')} | {route.get('任务类型')} | {route.get('风险等级')} | {item.get('状态')} | {route.get('目标系统')} | {summary} |")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 看板只展示队列状态，不执行任务。",
        "- 税收业务只登记为暂停，不进入施工链路。",
        "- 高风险动作等待人工确认。",
        "- 不触发 n8n，不发送企业微信，不写入旧系统。",
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"任务数量": len(tasks), "暂停任务": paused, "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
