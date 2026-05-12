# -*- coding: utf-8 -*-
"""生成税收/股票/视频三业务用户反馈样本闭环模板包。

本脚本只生成只读模板和候选资料，不自动吸收反馈，不转正式规则，
不连接税局、券商、企业微信、n8n 或真实视频发布链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "71三业务用户反馈样本闭环模板包"
LATEST_JSON = OUTPUT_DIR / "三业务用户反馈样本闭环模板包_最新.json"
TEMPLATE_MD = OUTPUT_DIR / "三业务用户反馈样本闭环采集模板_最新.md"
BOUNDARY_MD = OUTPUT_DIR / "三业务反馈闭环安全边界_最新.md"


REQUIRED_FIELDS = [
    "输入原文",
    "系统输出摘要",
    "用户判定",
    "问题类型",
    "是否触红线",
    "建议候选",
    "是否可自动吸收",
    "需总管确认",
]


BUSINESS_TEMPLATES: list[dict[str, Any]] = [
    {
        "业务": "税收",
        "模板编号": "TBFL-TAX-001",
        "输入原文": "用户粘贴的税收问答、草稿、事项描述或系统输入片段。",
        "系统输出摘要": "只摘录系统已给出的摘要、口径说明或待复核要点，不生成正式税务结论。",
        "用户判定": "正确 / 部分正确 / 错误 / 不清楚 / 需人工复核",
        "问题类型": ["理解偏差", "摘要遗漏", "口径不清", "红线请求", "其他"],
        "是否触红线": False,
        "建议候选": "可记录候选改写、补充字段、待复核说明或样本标签。",
        "是否可自动吸收": False,
        "需总管确认": True,
        "禁止动作": ["登录税局", "连接财税软件", "生成正式税务结论", "修改正式规则"],
    },
    {
        "业务": "股票",
        "模板编号": "TBFL-STOCK-001",
        "输入原文": "用户粘贴的股票研究、复盘反馈、展示问题或风险提示反馈。",
        "系统输出摘要": "只摘录系统已给出的展示摘要、研究说明或风险表述，不形成交易建议。",
        "用户判定": "正确 / 部分正确 / 错误 / 表达有交易化倾向 / 需人工复核",
        "问题类型": ["摘要遗漏", "风险提示不足", "交易化表达", "展示错误", "其他"],
        "是否触红线": False,
        "建议候选": "可记录候选措辞、展示层修正建议、风险提示补充或样本标签。",
        "是否可自动吸收": False,
        "需总管确认": True,
        "禁止动作": ["接券商", "交易", "修改核心评分引擎", "修改正式规则"],
    },
    {
        "业务": "视频",
        "模板编号": "TBFL-VIDEO-001",
        "输入原文": "用户粘贴的视频脚本、分镜、预检反馈或发布前问题描述。",
        "系统输出摘要": "只摘录系统已给出的脚本摘要、分镜摘要或预检阻断说明，不真实渲染发布。",
        "用户判定": "正确 / 部分正确 / 错误 / 不清楚 / 需人工复核",
        "问题类型": ["脚本不清", "分镜遗漏", "预检误判", "红线请求", "其他"],
        "是否触红线": False,
        "建议候选": "可记录候选脚本改写、分镜补充、预检说明或样本标签。",
        "是否可自动吸收": False,
        "需总管确认": True,
        "禁止动作": ["真实渲染", "上传发布", "触发n8n", "修改正式规则"],
    },
]


SAFETY_BOUNDARY: dict[str, bool] = {
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "真实发送企业微信": False,
    "触发n8n": False,
    "接券商或交易": False,
    "登录税局或接财税软件": False,
    "真实渲染或发布视频": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_template_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 三业务用户反馈样本闭环采集模板",
        "",
        "本模板只用于税收、股票、视频三类反馈样本闭环沉淀；默认不自动吸收，不转正式规则。",
        "",
    ]
    for item in report["模板列表"]:
        lines.extend(
            [
                f"## {item['模板编号']} {item['业务']}",
                "",
                f"- 输入原文：{item['输入原文']}",
                f"- 系统输出摘要：{item['系统输出摘要']}",
                f"- 用户判定：{item['用户判定']}",
                f"- 问题类型：{', '.join(item['问题类型'])}",
                f"- 是否触红线：{item['是否触红线']}",
                f"- 建议候选：{item['建议候选']}",
                f"- 是否可自动吸收：{item['是否可自动吸收']}",
                f"- 需总管确认：{item['需总管确认']}",
                f"- 禁止动作：{', '.join(item['禁止动作'])}",
                "",
            ]
        )
    return "\n".join(lines)


def build_boundary_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 三业务反馈闭环安全边界",
        "",
        "| 边界项 | 是否允许 |",
        "| --- | --- |",
    ]
    for name, allowed in report["安全边界"].items():
        lines.append(f"| {name} | {allowed} |")
    lines.extend(["", "所有样本候选必须先保留在模板包中，等待总管确认后再进入后续人工流程。", ""])
    return "\n".join(lines)


def main() -> int:
    report = {
        "名称": "三业务用户反馈样本闭环模板包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "three_business_feedback_loop_template_ready",
        "覆盖业务": ["税收", "股票", "视频"],
        "必填字段": REQUIRED_FIELDS,
        "模板列表": BUSINESS_TEMPLATES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "采集模板Markdown": str(TEMPLATE_MD),
            "安全边界Markdown": str(BOUNDARY_MD),
        },
    }

    write_json(LATEST_JSON, report)
    write_text(TEMPLATE_MD, build_template_markdown(report))
    write_text(BOUNDARY_MD, build_boundary_markdown(report))
    print(json.dumps({"状态": report["状态"], "模板数": len(BUSINESS_TEMPLATES), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
