"""
名称：统一消息出口.py
作用：提供 v3 面向用户主动消息的本地队列、优先级排序和合并消息生成能力。
触发方式：python 统一消息出口.py --self-test
依赖：Python 标准库。
所属系统：02杰哥扩展系统/00公共组件
安全边界：当前只写入本地消息队列和合并文件，不调用企业微信接口，不发送真实消息。
创建/修改记录：2026-04-26 创建统一消息出口本地队列版本；自检输出改为 ASCII JSON，避免 Windows 控制台编码误判。
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_path() -> Path:
    return module_root() / "01配置" / "统一消息出口配置.json"


def queue_dir() -> Path:
    target = module_root() / "03数据" / "01待发送队列"
    target.mkdir(parents=True, exist_ok=True)
    return target


def merged_dir() -> Path:
    target = module_root() / "03数据" / "02合并消息"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_config() -> dict[str, Any]:
    return json.loads(config_path().read_text(encoding="utf-8"))


def today_queue_file() -> Path:
    return queue_dir() / f"消息队列_{datetime.now().strftime('%Y%m%d')}.jsonl"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def enqueue_message(
    source_system: str,
    business_type: str,
    priority: str,
    title: str,
    content: str,
) -> dict[str, Any]:
    config = load_config()
    priority_map = config.get("优先级", {})
    message = {
        "消息ID": str(uuid.uuid4()),
        "来源系统": source_system,
        "业务类型": business_type,
        "优先级": priority if priority in priority_map else "中",
        "优先级分值": priority_map.get(priority, priority_map.get("中", 50)),
        "标题": title,
        "内容": content,
        "创建时间": now_text(),
        "发送状态": "待发送",
        "真实发送": False,
    }
    with today_queue_file().open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(message, ensure_ascii=False) + "\n")
    return message


def read_queue() -> list[dict[str, Any]]:
    path = today_queue_file()
    if not path.exists():
        return []
    messages = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        messages.append(json.loads(line))
    return messages


def build_merged_message(limit: int = 20) -> dict[str, Any]:
    messages = sorted(read_queue(), key=lambda item: (-int(item.get("优先级分值", 0)), item.get("创建时间", "")))
    selected = messages[: max(1, min(limit, 100))]
    merged = {
        "生成时间": now_text(),
        "发送模式": "本地合并预览",
        "真实发送": False,
        "消息数量": len(selected),
        "消息": selected,
        "合并文本": "\n\n".join(f"[{item.get('优先级')}] {item.get('标题')}\n{item.get('内容')}" for item in selected),
    }
    output = merged_dir() / f"统一消息合并_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = merged_dir() / "统一消息合并_最新.json"
    latest.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def self_test() -> dict[str, Any]:
    message = enqueue_message(
        source_system="00杰哥系统总管",
        business_type="系统测试",
        priority="低",
        title="统一消息出口自检",
        content="这是一条本地队列测试消息，不会发送到企业微信。",
    )
    merged = build_merged_message(limit=10)
    return {
        "入队消息ID": message["消息ID"],
        "队列文件": str(today_queue_file()),
        "合并消息数量": merged["消息数量"],
        "真实发送": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=True))
    else:
        print(json.dumps(build_merged_message(), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
