# -*- coding: utf-8 -*-
"""
名称：生成无人值守巡检失败诊断模板.py
作用：根据巡检运行记录模板生成失败诊断报告模板，预设止损条件和人工介入建议。
触发方式：python 生成无人值守巡检失败诊断模板.py
依赖：Python标准库；无人值守巡检失败诊断模板规则.json；无人值守只读巡检运行记录模板_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成诊断模板；不自动修复；不重试执行；不重启服务；不删除；不覆盖；不触发n8n；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守巡检失败诊断模板脚本。
标识：unattended-patrol-failure-diagnosis-template-report
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
    rule_path = manager / "01配置" / "无人值守巡检失败诊断模板规则.json"
    run_record_path = manager / "03数据" / "无人值守守护" / "无人值守只读巡检运行记录模板_最新.json"
    rules = load_json(rule_path)
    run_records = load_json(run_record_path)
    templates = []
    for item in run_records.get("运行记录模板", []):
        templates.append({
            "诊断编号": f"DIAG-{item.get('运行编号')}",
            "来源运行编号": item.get("运行编号"),
            "巡检编号": item.get("巡检编号"),
            "巡检名称": item.get("巡检名称"),
            "失败现象": "待巡检失败后填写",
            "初步原因分类": rules.get("原因分类", []),
            "已尝试方案": [],
            "禁止动作": [
                "删除文件",
                "覆盖配置",
                "重启服务",
                "触发n8n",
                "真实发送",
                "写正式库",
                "写旧系统"
            ],
            "止损条件": rules.get("止损条件", []),
            "人工介入建议": "巡检失败后先查看日志、确认失败是否可复现，再决定是否生成低风险修复方案。",
            "是否允许自动修复": False,
            "是否允许重试执行": False,
            "是否触发真实动作": False
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "运行记录模板": str(run_record_path),
        "默认开关": rules.get("默认开关", {}),
        "诊断字段": rules.get("诊断字段", []),
        "诊断模板": templates,
        "汇总": {
            "模板数量": len(templates),
            "允许自动修复数量": sum(1 for item in templates if item["是否允许自动修复"]),
            "允许重试执行数量": sum(1 for item in templates if item["是否允许重试执行"]),
            "触发真实动作数量": sum(1 for item in templates if item["是否触发真实动作"])
        },
        "当前结论": "无人值守巡检失败诊断模板已生成；当前不自动修复、不重试执行、不触发真实动作。"
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守巡检失败诊断模板_最新.json"
    latest = output_dir / "无人值守巡检失败诊断模板_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"模板数量": len(templates), "允许自动修复数量": report["汇总"]["允许自动修复数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
