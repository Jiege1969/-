# -*- coding: utf-8 -*-
"""
名称：生成巡检结果经验卡片候选模板.py
作用：根据无人值守巡检失败诊断模板，生成进入进化系统前的经验卡片候选模板。
触发方式：python 生成巡检结果经验卡片候选模板.py
依赖：Python标准库；巡检结果经验卡片候选规则.json；无人值守巡检失败诊断模板_最新.json。
所属系统：03杰哥进化系统
安全边界：只生成经验候选模板；不生成正式经验卡片；不自动提炼通用方法；不自动固化规则；不删除；不移动；不写旧系统。
创建/修改记录：2026-04-28 创建巡检结果经验卡片候选模板脚本。
标识：patrol-result-experience-candidate-template-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def evolution_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = v3_root()
    evolution = evolution_root()
    manager = root / "00杰哥系统总管"
    rule_path = evolution / "01配置" / "巡检结果经验卡片候选规则.json"
    diagnosis_path = manager / "03数据" / "无人值守守护" / "无人值守巡检失败诊断模板_最新.json"
    rules = load_json(rule_path)
    diagnosis = load_json(diagnosis_path)
    candidates = []
    for item in diagnosis.get("诊断模板", []):
        candidates.append({
            "候选编号": f"EXP-CAND-{item.get('诊断编号')}",
            "来源诊断编号": item.get("诊断编号"),
            "来源巡检名称": item.get("巡检名称"),
            "问题现象": item.get("失败现象"),
            "根因假设": "待真实失败后补充",
            "复用价值判断": "待人工复核",
            "适用场景": [],
            "不可迁移边界": [],
            "人工复核状态": "待真实失败后复核",
            "是否生成正式经验卡片": False,
            "是否自动提炼通用方法": False,
            "是否自动固化规则": False,
            "是否删除样本": False,
            "是否移动样本": False,
            "是否写旧系统": False
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "诊断模板": str(diagnosis_path),
        "默认开关": rules.get("默认开关", {}),
        "候选字段": rules.get("候选字段", []),
        "进入条件": rules.get("进入条件", []),
        "经验卡片候选模板": candidates,
        "汇总": {
            "候选数量": len(candidates),
            "正式经验卡片数量": sum(1 for item in candidates if item["是否生成正式经验卡片"]),
            "自动提炼通用方法数量": sum(1 for item in candidates if item["是否自动提炼通用方法"]),
            "自动固化规则数量": sum(1 for item in candidates if item["是否自动固化规则"]),
            "删除样本数量": sum(1 for item in candidates if item["是否删除样本"]),
            "移动样本数量": sum(1 for item in candidates if item["是否移动样本"]),
            "写旧系统数量": sum(1 for item in candidates if item["是否写旧系统"])
        },
        "当前结论": "巡检结果经验卡片候选模板已生成；当前不生成正式经验卡片，不自动提炼或固化。"
    }
    output_dir = evolution / "03数据" / "06巡检经验候选"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"巡检结果经验卡片候选模板_{timestamp}.json"
    latest = output_dir / "巡检结果经验卡片候选模板_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"候选数量": len(candidates), "正式经验卡片数量": report["汇总"]["正式经验卡片数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
