# -*- coding: utf-8 -*-
"""
名称：生成无人值守任务状态机报告.py
作用：根据无人值守任务状态机规则，生成任务状态、允许流转和禁止流转报告。
触发方式：python 生成无人值守任务状态机报告.py
依赖：Python 标准库；无人值守任务状态机规则.json。
所属系统：00杰哥系统总管
安全边界：只生成任务状态机报告；不触发真实任务；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建无人值守任务状态机报告脚本。
标识：unattended-task-state-machine
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "无人值守任务状态机规则.json"
    rules = load_json(rule_path)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "允许状态": rules.get("允许状态", []),
        "允许流转": rules.get("允许流转", []),
        "禁止流转": rules.get("禁止流转", []),
        "默认开关": rules.get("默认开关", {}),
        "汇总": {
            "状态数量": len(rules.get("允许状态", [])),
            "允许流转数量": len(rules.get("允许流转", [])),
            "禁止流转数量": len(rules.get("禁止流转", [])),
        },
        "是否触发真实任务": False,
        "当前结论": "无人值守任务状态机报告已生成；当前只登记状态规则，不触发真实任务。",
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守任务状态机报告_最新.json"
    latest = output_dir / "无人值守任务状态机报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"状态数量": report["汇总"]["状态数量"], "允许流转数量": report["汇总"]["允许流转数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
