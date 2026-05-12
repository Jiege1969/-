"""
名称：提交日常任务到人工确认队列.py
作用：将日常任务文本分类、分级并写入人工确认队列，作为真实业务执行前的缓冲层。
触发方式：python 提交日常任务到人工确认队列.py --content "任务内容"；或 --demo 生成演练样本。
依赖：Python 标准库；01配置/日常任务入口规则.json。
所属系统：01杰哥智能系统
安全边界：只写入新系统任务队列或演练目录；不触发n8n、不发送企业微信、不写旧系统、不执行税收业务。
创建/修改记录：2026-04-27 创建日常任务入口队列脚本。
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def classify(content: str, rules: dict[str, Any]) -> dict[str, Any]:
    text = normalize(content)
    matched_type: dict[str, Any] | None = None
    matched_keywords: list[str] = []
    for item in rules.get("任务类型", []):
        hits = [word for word in item.get("关键词", []) if word.lower() in text]
        if hits and len(hits) > len(matched_keywords):
            matched_type = item
            matched_keywords = hits
    if matched_type is None:
        matched_type = {
            "名称": "普通对话",
            "目标系统": "01杰哥智能系统",
            "默认风险": "低",
            "默认处理方式": "生成回答草稿",
        }
    high_hits = [word for word in rules.get("高风险关键词", []) if word.lower() in text]
    task_type = matched_type.get("名称", "普通对话")
    paused = task_type in set(rules.get("暂停任务类型", []))
    risk = "高" if high_hits or paused else matched_type.get("默认风险", "低")
    return {
        "任务类型": task_type,
        "目标系统": matched_type.get("目标系统", "01杰哥智能系统"),
        "命中关键词": matched_keywords,
        "高风险关键词": high_hits,
        "风险等级": risk,
        "建议处理方式": matched_type.get("默认处理方式", "生成回答草稿"),
        "是否暂停": paused,
        "是否需要人工确认": True,
    }


def build_task(content: str, source: str, priority: str, rules: dict[str, Any]) -> dict[str, Any]:
    route = classify(content, rules)
    now = datetime.now()
    status = "已暂停待人工决定" if route["是否暂停"] else rules.get("默认状态", "待人工确认")
    return {
        "任务ID": f"DT-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}",
        "创建时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "来源": source,
        "优先级": priority,
        "原始内容": content,
        "路由结果": route,
        "状态": status,
        "安全边界": {
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否执行税收业务": False,
            "是否执行真实交易": False,
        },
        "下一步": "等待人工确认后进入对应系统的只读计划或草稿流程",
    }


def write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", default="", help="task content")
    parser.add_argument("--source", default="local_cli", help="task source")
    parser.add_argument("--priority", default="normal", choices=["low", "normal", "high"], help="task priority")
    parser.add_argument("--demo", action="store_true", help="write demo tasks to temporary rehearsal queue")
    args = parser.parse_args()

    root = system_root()
    rules = load_json(root / "01杰哥智能系统" / "01配置" / "日常任务入口规则.json")
    if args.demo:
        contents = [
            "帮我做一份股票研究计划，先不要真实抓取数据",
            "把一段工作材料生成汇报草稿，等待人工确认",
            "检查系统健康状态，不要修复",
            "增值税政策分类需求登记，税收业务继续暂停",
        ]
        output = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "任务队列_最新.jsonl"
    else:
        if not args.content.strip():
            raise ValueError("缺少 --content，未写入任务队列")
        contents = [args.content]
        output = root / "01杰哥智能系统" / "03数据" / "任务队列" / "01待人工确认" / "任务队列_最新.jsonl"
    tasks = [build_task(content, args.source, args.priority, rules) for content in contents]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in tasks) + "\n", encoding="utf-8")
    print(json.dumps({"写入数量": len(tasks), "输出": str(output), "暂停数量": sum(1 for item in tasks if item["路由结果"]["是否暂停"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
