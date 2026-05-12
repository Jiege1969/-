# -*- coding: utf-8 -*-
"""
名称：验证散点共识归集落实.py
作用：验证散落在工作日志和施工记录中的成熟共识是否归属到既有开工索引、施工落地检查、学习提炼导航和总纲更新机制。
触发方式：python 验证散点共识归集落实.py
依赖：开工上下文索引、智能化施工落地检查规则、子系统继承规则、学习提炼导航规则、散点共识补充索引。
所属系统：00杰哥系统总管
输出：标准输出 JSON 验收结果。
安全边界：只读验证；不更新接续包、不触发n8n、不发送企业微信、不写正式业务库。
创建/修改记录：2026-05-03 创建；2026-05-03 按用户纠偏改为验证归属既有机制。
标识：scattered-consensus-existing-mechanism-verify
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
EVOLUTION = ROOT / "03杰哥进化系统"
INTELLIGENCE = ROOT / "01杰哥智能系统"

INDEX = MANAGER / "07文档" / "设计纲领" / "散点共识归集索引_20260503.md"
RULE = MANAGER / "01配置" / "散点共识归集规则.json"
METHOD = EVOLUTION / "03数据" / "04通用方法" / "散点共识归集_从日志到总纲计划具体工作_20260503.md"
START_CONTEXT_INDEX = MANAGER / "01配置" / "开工上下文索引.json"
CONSTRUCTION_RULE = MANAGER / "01配置" / "智能化施工落地检查规则.json"
INHERIT_RULE = MANAGER / "01配置" / "子系统全闭环继承规则.json"
LEARNING_RULE = EVOLUTION / "01配置" / "学习提炼导航规则.json"
CONSTITUTION = MANAGER / "07文档" / "设计纲领" / "系统宪法级原则与落地检查清单_20260503.md"
REPORT_REVIEW = INTELLIGENCE / "07文档" / "股票报告文稿质检融入方案_20260503.md"
FUSION_PANEL = MANAGER / "03数据" / "四系统小闭环" / "股票四系统融合闭环状态面板_最新.json"
WORK_LOG = MANAGER / "07文档" / "工作日志" / "2026-05-03.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def has_all(value: str, needles: list[str]) -> bool:
    return all(needle in value for needle in needles)


def main() -> int:
    index = text(INDEX)
    method = text(METHOD)
    start_context_index = text(START_CONTEXT_INDEX)
    construction_rule = text(CONSTRUCTION_RULE)
    inherit_rule = text(INHERIT_RULE)
    learning_rule = text(LEARNING_RULE)
    constitution = text(CONSTITUTION)
    review = text(REPORT_REVIEW)
    work_log = text(WORK_LOG)
    rule = load(RULE)
    fusion = load(FUSION_PANEL)

    checks = [
        {"名称": "归集索引存在", "通过": INDEX.exists()},
        {"名称": "归集规则存在", "通过": RULE.exists()},
        {"名称": "通用方法存在", "通过": METHOD.exists()},
        {"名称": "开工上下文索引已覆盖总纲更新触发", "通过": has_all(start_context_index, ["总纲更新触发条件", "工作日志"])},
        {"名称": "施工落地检查已覆盖学习提炼和接续边界", "通过": has_all(construction_rule, ["学习提炼", "接续包", "文稿质检"])},
        {"名称": "子系统继承规则已覆盖不反复刷新接续包", "通过": has_all(inherit_rule, ["施工过程中只写工作日志", "收工或新开对话"])},
        {"名称": "学习提炼导航已覆盖学什么怎么学", "通过": has_all(learning_rule, ["学什么", "怎么学", "不应该学习"])},
        {"名称": "工作日志来源存在", "通过": WORK_LOG.exists()},
        {"名称": "索引明确不是新机制", "通过": has_all(index, ["不是新机制", "不是新工作流", "不另立一摊"])},
        {"名称": "规则明确归属既有机制", "通过": bool(rule.get("归属机制")) and rule.get("硬边界", {}).get("另立独立归集系统") is False},
        {"名称": "索引包含股票样板共识", "通过": has_all(index, ["股票系统是样板", "不是终点"])},
        {"名称": "索引包含报告质检旁路共识", "通过": has_all(index, ["报告需要质检", "第一阶段必须旁路"])},
        {"名称": "索引包含手机端排版共识", "通过": has_all(index, ["手机端排版", "系统质量问题"])},
        {"名称": "索引包含硬件天花板共识", "通过": has_all(index, ["硬件天花板", "科学工作原则"])},
        {"名称": "索引包含影子试验失败隔离共识", "通过": has_all(index, ["影子试验", "失败隔离"])},
        {"名称": "索引包含学习提炼导航共识", "通过": has_all(index, ["知道学什么", "不乱学习"])},
        {"名称": "索引包含接续包边界共识", "通过": has_all(index, ["接续包", "收工或新开对话"])},
        {"名称": "索引包含循环依赖经验", "通过": has_all(index, ["循环依赖", "上层总闸口"])},
        {"名称": "归集规则区分应该和不应归集", "通过": bool(rule.get("应该归集")) and bool(rule.get("不应直接归集"))},
        {"名称": "归集规则禁止日常施工更新接续包", "通过": rule.get("硬边界", {}).get("日常施工更新接续包") is False},
        {"名称": "通用方法包含四层归集法且不重复造机制", "通过": has_all(method, ["日志层", "索引层", "规则层", "执行层", "不重复造机制"])},
        {"名称": "宪法原则已存在", "通过": has_all(constitution, ["硬件天花板原则", "平稳运行优先原则", "克制施工原则"])},
        {"名称": "报告质检方案已存在", "通过": has_all(review, ["内容完整性", "文章结构", "语言描述", "排版显示"])},
        {"名称": "融合面板仍可继续施工", "通过": fusion.get("融合结论") == "通过：可以按融合主线继续施工"},
        {"名称": "工作日志确有散点来源", "通过": has_all(work_log, ["文稿质检", "学习提炼导航", "接续包边界"])},
    ]
    ok = all(item["通过"] for item in checks)
    print(json.dumps({
        "状态": "完成",
        "验收结论": "通过：散点共识归集已归属既有机制，未另立独立工作" if ok else "未通过：散点共识归集归属或边界存在缺口",
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
        "安全边界": {
            "更新接续包": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式业务库": False
        }
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
