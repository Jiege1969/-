# -*- coding: utf-8 -*-
"""
名称：生成无人值守巡检用户摘要模板.py
作用：根据巡检运行记录模板和失败诊断模板，生成面向用户的巡检摘要模板。
触发方式：python 生成无人值守巡检用户摘要模板.py
依赖：Python标准库；无人值守巡检用户摘要规则.json；无人值守只读巡检运行记录模板_最新.json；无人值守巡检失败诊断模板_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成用户摘要模板；不真实推送；不发送企业微信；不触发n8n；不自动确认；不自动修复；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守巡检用户摘要模板脚本。
标识：unattended-patrol-user-summary-template-report
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
    rule_path = manager / "01配置" / "无人值守巡检用户摘要规则.json"
    run_record_path = manager / "03数据" / "无人值守守护" / "无人值守只读巡检运行记录模板_最新.json"
    diagnosis_path = manager / "03数据" / "无人值守守护" / "无人值守巡检失败诊断模板_最新.json"
    rules = load_json(rule_path)
    run_record = load_json(run_record_path)
    diagnosis = load_json(diagnosis_path)
    records = run_record.get("运行记录模板", [])
    diagnosis_templates = diagnosis.get("诊断模板", [])
    summary = {
        "摘要编号": f"SUMMARY-TEMPLATE-{datetime.now().strftime('%Y%m%d')}",
        "总体状态": "模板未执行",
        "通过数量": 0,
        "失败数量": 0,
        "阻断数量": 0,
        "需要人工确认数量": len(diagnosis_templates),
        "用户需关注事项": [
            "当前只是摘要模板，尚未启用真实巡检。",
            "未来出现失败或阻断时，只提示结论、影响和建议，不直接推送原始报错堆栈。"
        ],
        "系统已做事项": [
            "登记巡检项",
            "登记运行记录结构",
            "登记失败诊断结构",
            "登记经验候选入口"
        ],
        "系统未做事项": [
            "未真实推送",
            "未发送企业微信",
            "未触发n8n",
            "未自动确认",
            "未自动修复"
        ],
        "是否真实推送": False,
        "是否企业微信发送": False,
        "是否触发n8n": False,
        "是否自动确认": False,
        "是否自动修复": False,
        "是否写旧系统": False
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "运行记录模板": str(run_record_path),
        "失败诊断模板": str(diagnosis_path),
        "默认开关": rules.get("默认开关", {}),
        "摘要字段": rules.get("摘要字段", []),
        "用户可见原则": rules.get("用户可见原则", []),
        "巡检模板数量": len(records),
        "用户摘要模板": summary,
        "汇总": {
            "摘要数量": 1,
            "真实推送数量": 1 if summary["是否真实推送"] else 0,
            "企业微信发送数量": 1 if summary["是否企业微信发送"] else 0,
            "触发n8n数量": 1 if summary["是否触发n8n"] else 0,
            "自动确认数量": 1 if summary["是否自动确认"] else 0,
            "自动修复数量": 1 if summary["是否自动修复"] else 0,
            "写旧系统数量": 1 if summary["是否写旧系统"] else 0
        },
        "当前结论": "无人值守巡检用户摘要模板已生成；当前不推送、不发送、不触发真实动作。"
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守巡检用户摘要模板_最新.json"
    latest = output_dir / "无人值守巡检用户摘要模板_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"摘要数量": 1, "真实推送数量": report["汇总"]["真实推送数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
