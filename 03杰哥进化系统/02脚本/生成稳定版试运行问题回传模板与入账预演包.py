# -*- coding: utf-8 -*-
"""生成稳定版试运行问题回传模板与入账预演包。

用于稳定版真实使用后的问题回收：只生成回传模板、入账预演和处理口径，
不写正式规则，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包"

LATEST_JSON = OUTPUT_DIR / "稳定版试运行问题回传模板与入账预演包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版试运行问题回传模板与入账预演包_最新.md"
TEMPLATE_JSON = OUTPUT_DIR / "稳定版试运行问题回传模板_最新.json"
TEMPLATE_MD = OUTPUT_DIR / "稳定版试运行问题回传模板_最新.md"
LEDGER_JSON = OUTPUT_DIR / "稳定版试运行问题入账预演台账_最新.json"
LEDGER_MD = OUTPUT_DIR / "稳定版试运行问题入账预演台账_最新.md"
POLICY_MD = OUTPUT_DIR / "稳定版试运行问题处理口径_最新.md"


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


FIELDS = [
    "回传日期",
    "使用入口",
    "业务域",
    "用户原始输入",
    "系统返回摘要",
    "期望结果",
    "实际结果",
    "是否影响日常使用",
    "是否疑似红线",
    "复现步骤",
    "相关截图或文件路径",
    "建议处理级别",
]


SAMPLE_ITEMS = [
    {
        "编号": "FB-SAMPLE-001",
        "业务域": "公共接入",
        "问题类型": "职责分流疑问",
        "默认级别": "P2",
        "处理口径": "只读复现，确认是否路由或提示层问题。",
    },
    {
        "编号": "FB-SAMPLE-002",
        "业务域": "税收",
        "问题类型": "事项识别或草案摘要问题",
        "默认级别": "P2",
        "处理口径": "只生成待复核草案候选，不生成正式税务结论。",
    },
    {
        "编号": "FB-SAMPLE-003",
        "业务域": "股票",
        "问题类型": "展示口径冲突",
        "默认级别": "P2",
        "处理口径": "限定展示层修复，不接券商、不交易。",
    },
    {
        "编号": "FB-SAMPLE-004",
        "业务域": "视频",
        "问题类型": "渲染或发布阻断提示问题",
        "默认级别": "P3",
        "处理口径": "只补阻断提示或材料清单，不真实渲染发布。",
    },
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_template() -> dict[str, Any]:
    return {
        "名称": "稳定版试运行问题回传模板",
        "字段": FIELDS,
        "填写说明": {
            "是否疑似红线": "只要涉及真实发送、n8n、交易、税局/财税软件、真实渲染发布、服务重载、正式规则，填 true。",
            "建议处理级别": "P0红线/P1不可用/P2体验错误/P3交接观察/P4增强建议。",
        },
        "空白模板": {field: "" for field in FIELDS},
    }


def build_template_md(template: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版试运行问题回传模板",
            "",
            "## 字段",
            "",
            *[f"- {field}" for field in template["字段"]],
            "",
            "## 红线提醒",
            "",
            "- 涉及真实发送、n8n、交易、税局/财税软件、真实渲染发布、服务重载、正式规则时，标记疑似红线。",
            "- 疑似红线只登记需总管确认，不进入自动修复。",
            "",
        ]
    )


def build_ledger() -> dict[str, Any]:
    return {
        "名称": "稳定版试运行问题入账预演台账",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "入账方式": "预演台账，等待真实使用者回传后按模板入账。",
        "当前问题数": 0,
        "问题项": [],
        "样例分类": SAMPLE_ITEMS,
        "安全边界": SAFETY_BOUNDARY,
    }


def build_ledger_md(ledger: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['业务域']} | {item['问题类型']} | {item['默认级别']} | {item['处理口径']} |"
        for item in ledger["样例分类"]
    ]
    return "\n".join(
        [
            "# 稳定版试运行问题入账预演台账",
            "",
            f"- 生成时间：{ledger['生成时间']}",
            f"- 当前问题数：{ledger['当前问题数']}",
            "",
            "| 编号 | 业务域 | 问题类型 | 默认级别 | 处理口径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_policy_md() -> str:
    return "\n".join(
        [
            "# 稳定版试运行问题处理口径",
            "",
            "- P0：红线风险，立即停止自动处理，登记需总管确认。",
            "- P1：稳定版不可用，优先只读复现，最小修复后复跑总回归和指挥台刷新。",
            "- P2：体验或展示错误，只修提示层、路由层、展示层，不扩展核心引擎。",
            "- P3：交接或观察不足，补模板、补说明、补只读核对。",
            "- P4：增强建议，进入后续迭代队列，不影响稳定版签收。",
            "",
            "## 禁止",
            "",
            "- 不自动转正式规则。",
            "- 不触发外部真实动作。",
            "- 不重载 19310/19302，除非总管确认。",
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版试运行问题回传模板与入账预演包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 模板字段数：{report['指标']['模板字段数']}",
            f"- 当前问题数：{report['指标']['当前问题数']}",
            "",
            "## 输出",
            "",
            f"- 回传模板：{TEMPLATE_MD}",
            f"- 入账预演台账：{LEDGER_MD}",
            f"- 处理口径：{POLICY_MD}",
            "",
        ]
    )


def main() -> int:
    template = build_template()
    ledger = build_ledger()
    report = {
        "名称": "稳定版试运行问题回传模板与入账预演包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_trial_feedback_intake_preview_ready",
        "回传模板": str(TEMPLATE_JSON),
        "入账预演台账": str(LEDGER_JSON),
        "处理口径": str(POLICY_MD),
        "指标": {
            "模板字段数": len(FIELDS),
            "样例分类数": len(SAMPLE_ITEMS),
            "当前问题数": ledger["当前问题数"],
            "安全边界关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "回传模板JSON": str(TEMPLATE_JSON),
            "回传模板Markdown": str(TEMPLATE_MD),
            "入账预演台账JSON": str(LEDGER_JSON),
            "入账预演台账Markdown": str(LEDGER_MD),
            "处理口径Markdown": str(POLICY_MD),
        },
    }
    write_json(TEMPLATE_JSON, template)
    write_text(TEMPLATE_MD, build_template_md(template))
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))
    write_text(POLICY_MD, build_policy_md())
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "模板字段数": len(FIELDS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
