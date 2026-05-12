# -*- coding: utf-8 -*-
"""生成稳定交付版运行观察基线与改进闭环包。

本包用于把后续施工重心收回到稳定版真实运行观察：
只生成基线、台账模板、问题分级和改进闭环候选流程，不写正式规则，
不触发外部系统，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "77稳定交付版运行观察基线与改进闭环包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版运行观察基线与改进闭环包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版运行观察基线与改进闭环包_最新.md"
LEDGER_JSON = OUTPUT_DIR / "稳定版运行观察台账模板_最新.json"
LEDGER_MD = OUTPUT_DIR / "稳定版运行观察台账模板_最新.md"
LEVEL_JSON = OUTPUT_DIR / "稳定版运行问题分级表_最新.json"
LOOP_JSON = OUTPUT_DIR / "稳定版改进闭环候选流程_最新.json"
LOOP_MD = OUTPUT_DIR / "稳定版改进闭环候选流程_最新.md"


EVIDENCE = [
    {
        "编号": "EV-001",
        "名称": "日常可用版自主巡检快照",
        "路径": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
        "通过字段": ["总体状态"],
        "通过值": "pass",
    },
    {
        "编号": "EV-002",
        "名称": "日常可用交付版一键只读总回归验收",
        "路径": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
        "通过字段": ["通过"],
        "通过值": True,
    },
    {
        "编号": "EV-003",
        "名称": "稳定版候选正式封版申请草案验收",
        "路径": EVOLUTION_ROOT / "04日志" / "稳定版候选正式封版申请草案与最终交付封面收紧包验收" / "stable-candidate-formal-freeze-request-draft-verify-最新.json",
        "通过字段": ["通过"],
        "通过值": True,
    },
    {
        "编号": "EV-004",
        "名称": "三日巡检第2天待执行链路验收",
        "路径": EVOLUTION_ROOT / "04日志" / "三日巡检第2天待执行链路与防伪检查包验收" / "three-day-patrol-day2-pending-chain-verify-最新.json",
        "通过字段": ["通过"],
        "通过值": True,
    },
    {
        "编号": "EV-005",
        "名称": "稳定版最后收口总回传与候选交付封面验收",
        "路径": EVOLUTION_ROOT / "04日志" / "稳定版最后收口总回传与候选交付封面包验收" / "stable-final-closeout-cover-verify-最新.json",
        "通过字段": ["通过"],
        "通过值": True,
    },
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


ISSUE_LEVELS = [
    {
        "级别": "P0",
        "名称": "红线风险",
        "判定": "涉及真实发送、n8n真实触发、交易、税局/财税软件登录、真实渲染发布、服务未确认重载、正式规则自动写入。",
        "处理": "立即阻断，登记需总管确认，不进入自动修复。",
    },
    {
        "级别": "P1",
        "名称": "稳定版不可用",
        "判定": "日常入口不可达、职责分流错乱、税收/股票/视频核心只读能力失效、一键回归失败。",
        "处理": "优先复现，最小修复，复跑一键只读总回归和自主巡检快照。",
    },
    {
        "级别": "P2",
        "名称": "稳定版体验错误",
        "判定": "口径冲突、路由遗漏、阻断提示不清、报告标题或事项识别错误。",
        "处理": "限定展示层/路由层/提示层最小修复，不扩展核心引擎。",
    },
    {
        "级别": "P3",
        "名称": "交接与观察不足",
        "判定": "证据链不完整、台账字段不够、复验入口不顺、人工反馈无法沉淀。",
        "处理": "补模板、补只读核对、补候选案例，不转正式规则。",
    },
    {
        "级别": "P4",
        "名称": "增强建议",
        "判定": "不影响稳定版使用，但可提升完全交付或自主运行能力。",
        "处理": "进入候选池，等待稳定版真实运行样本支持后再推进。",
    },
]


OBSERVATION_FIELDS = [
    "日期",
    "来源入口",
    "业务域",
    "用户原始输入",
    "系统返回摘要",
    "是否通过",
    "问题级别",
    "是否触碰红线",
    "复现方式",
    "只读证据路径",
    "候选改进建议",
    "是否需总管确认",
    "处理状态",
]


IMPROVEMENT_LOOP = [
    "稳定版真实运行或只读巡检暴露问题",
    "进入运行观察台账，不直接改正式规则",
    "按 P0-P4 分级，P0 立即阻断并登记需总管确认",
    "只读复现并形成证据路径",
    "低风险问题做最小修复，高风险问题只生成候选方案",
    "复跑一键只读总回归、自主巡检快照和相关专项验收",
    "通过后形成进化候选，正式规则仍需总管确认",
]


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def nested_get(data: dict[str, Any], keys: list[str]) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def evaluate_evidence(item: dict[str, Any]) -> dict[str, Any]:
    path = item["路径"]
    data = read_json_if_exists(path)
    actual = nested_get(data, item["通过字段"])
    summary = {
        "编号": item["编号"],
        "名称": item["名称"],
        "路径": str(path),
        "存在": path.exists(),
        "期望值": item["通过值"],
        "实际值": actual,
        "通过": path.exists() and actual == item["通过值"],
    }
    if data.get("汇总"):
        summary["汇总"] = data.get("汇总")
    if data.get("指标"):
        summary["指标"] = data.get("指标")
    return summary


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_ledger() -> dict[str, Any]:
    return {
        "名称": "稳定版运行观察台账模板",
        "用途": "稳定版真实运行后记录问题、复现证据、候选改进和总管确认状态。",
        "字段": OBSERVATION_FIELDS,
        "样例": [
            {
                "日期": "YYYY-MM-DD",
                "来源入口": "企业微信公共接入层/本地只读巡检/业务专项验收",
                "业务域": "税收/股票/视频/公共接入/进化系统",
                "用户原始输入": "",
                "系统返回摘要": "",
                "是否通过": None,
                "问题级别": "P0/P1/P2/P3/P4",
                "是否触碰红线": False,
                "复现方式": "只读命令或本地预演路径",
                "只读证据路径": "",
                "候选改进建议": "",
                "是否需总管确认": False,
                "处理状态": "待观察/待复现/候选中/已修复/已复验/需总管确认",
            }
        ],
    }


def build_ledger_md(ledger: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版运行观察台账模板",
            "",
            f"- 用途：{ledger['用途']}",
            "",
            "## 字段",
            "",
            *[f"- {field}" for field in ledger["字段"]],
            "",
            "## 使用边界",
            "",
            "- 只记录稳定版运行观察和只读复现证据。",
            "- 不自动写正式规则，不自动触发外部动作。",
            "- P0 和需要服务重载的问题必须登记为需总管确认。",
            "",
        ]
    )


def build_loop_md(loop: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版改进闭环候选流程",
            "",
            f"- 性质：{loop['性质']}",
            "",
            "## 流程",
            "",
            *[f"{idx}. {step}" for idx, step in enumerate(loop["步骤"], start=1)],
            "",
            "## 禁止事项",
            "",
            *[f"- {name}={value}" for name, value in SAFETY_BOUNDARY.items()],
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['存在']} | {item['通过']} | {item['路径']} |"
        for item in report["证据"]
    ]
    return "\n".join(
        [
            "# 稳定交付版运行观察基线与改进闭环包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 当前策略：{report['当前策略']}",
            f"- 证据通过：{report['指标']['证据通过']} / {report['指标']['证据总数']}",
            f"- 问题分级：{report['指标']['问题分级数']} 类",
            "",
            "## 证据基线",
            "",
            "| 编号 | 名称 | 存在 | 通过 | 路径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 运行原则",
            "",
            "- 先稳定运行，再从真实运行观察里找改进点。",
            "- 只读巡检和一键回归是稳定版地基。",
            "- 所有进化先形成候选，不自动转正式规则。",
            "- 所有红线动作继续关闭。",
            "",
        ]
    )


def main() -> int:
    evidence = [evaluate_evidence(item) for item in EVIDENCE]
    evidence_passed = sum(1 for item in evidence if item["通过"])
    ledger = build_ledger()
    loop = {
        "名称": "稳定版改进闭环候选流程",
        "性质": "候选流程，不是正式规则",
        "步骤": IMPROVEMENT_LOOP,
        "红线动作全部关闭": all(value is False for value in SAFETY_BOUNDARY.values()),
    }
    report = {
        "名称": "稳定交付版运行观察基线与改进闭环包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_runtime_observation_baseline_ready",
        "当前策略": "优先稳定交付版；完全交付和自主运行必须基于稳定版真实运行观察继续演进。",
        "证据": evidence,
        "运行观察台账模板": str(LEDGER_JSON),
        "问题分级表": ISSUE_LEVELS,
        "改进闭环候选流程": str(LOOP_JSON),
        "指标": {
            "证据总数": len(evidence),
            "证据通过": evidence_passed,
            "问题分级数": len(ISSUE_LEVELS),
            "台账字段数": len(OBSERVATION_FIELDS),
            "闭环步骤数": len(IMPROVEMENT_LOOP),
            "红线关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "运行观察台账模板JSON": str(LEDGER_JSON),
            "运行观察台账模板Markdown": str(LEDGER_MD),
            "问题分级表JSON": str(LEVEL_JSON),
            "改进闭环候选流程JSON": str(LOOP_JSON),
            "改进闭环候选流程Markdown": str(LOOP_MD),
        },
    }

    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))
    write_json(LEVEL_JSON, {"名称": "稳定版运行问题分级表", "分级": ISSUE_LEVELS})
    write_json(LOOP_JSON, loop)
    write_text(LOOP_MD, build_loop_md(loop))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))

    print(json.dumps({"状态": report["状态"], "证据通过": evidence_passed, "证据总数": len(evidence), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
