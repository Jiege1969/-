"""
名称：生成经验卡片.py
作用：根据经验分类规则生成一张可复用的问题/经验卡片，供进化系统后续提炼通用方法。
触发方式：python 生成经验卡片.py --self-test
依赖：Python 标准库。
所属系统：03杰哥进化系统
安全边界：只写入 03杰哥进化系统数据目录；不修改业务系统配置，不自动固化规则。
创建/修改记录：2026-04-26 创建经验卡片生成脚本。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_dir() -> Path:
    return system_root() / "01配置"


def card_dir() -> Path:
    target = system_root() / "03数据" / "01问题卡片"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_self_test_card() -> dict[str, Any]:
    rules = load_json(config_dir() / "经验分类规则.json")
    return {
        "生成时间": now_text(),
        "卡片类型": "类似借鉴",
        "来源系统": "03杰哥进化系统",
        "来源阶段": "进化系统底座搭建",
        "问题现象": "不同脚本在 Windows 子进程输出中文 JSON 时可能出现编码误读。",
        "根因分类": "编码问题",
        "根本原因": "Windows PowerShell 默认编码和 Python 子进程输出解码不一致，导致中文键名被误读。",
        "解决办法": "机器消费的自检输出使用 ASCII JSON；文件内容仍使用 UTF-8 保存中文。",
        "验证方法": "运行相关验证脚本，确认 JSON 字段可被稳定读取。",
        "可复用逻辑": "面向机器的接口优先使用无歧义编码；面向人的文档可以保留中文。",
        "可迁移场景": ["统一消息出口", "OpenClaw回环测试", "验收脚本", "工作流草案生成"],
        "不可迁移边界": "不能以牺牲人类可读文档为代价；配置和文档仍应保持中文可读。",
        "经验状态": "已提炼",
        "是否建议固化": True,
        "规则来源": rules.get("说明"),
    }


def save_card(card: dict[str, Any]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_type = card.get("卡片类型", "经验卡片")
    output = card_dir() / f"{safe_type}_{timestamp}.json"
    output.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = card_dir() / "经验卡片_最新.json"
    latest.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    card = build_self_test_card()
    output = save_card(card)
    print(json.dumps({"卡片类型": card["卡片类型"], "输出": str(output), "是否建议固化": card["是否建议固化"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
