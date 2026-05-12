# -*- coding: utf-8 -*-
"""生成低风险用户反馈样本模板包。

只生成使用者反馈模板和只读验收资料，不连接任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "71低风险用户反馈样本模板包"
LATEST_JSON = OUTPUT_DIR / "低风险用户反馈样本模板包_最新.json"
LATEST_MD = OUTPUT_DIR / "低风险用户反馈样本模板包_最新.md"
TEMPLATE_MD = OUTPUT_DIR / "用户反馈样本模板_最新.md"
CLASSIFY_MD = OUTPUT_DIR / "反馈分级与处理边界_最新.md"


FEEDBACK_TEMPLATES: list[dict[str, Any]] = [
    {
        "编号": "UFT-001",
        "业务线": "企业微信公共接入层",
        "反馈问题": "手机端/本地接口回复是否符合职责分流。",
        "必填字段": ["输入文本", "调用入口", "实际回复", "预期归属", "是否触发真实发送"],
        "允许处理": "只读巡检、路由说明候选、传参问题定位。",
        "禁止处理": "真实发送企业微信、触发 n8n、自行重载 19310。",
    },
    {
        "编号": "UFT-002",
        "业务线": "税收业务",
        "反馈问题": "待复核草案摘要是否识别到正确事项。",
        "必填字段": ["输入文本", "返回标题", "识别事项", "不满意点", "是否需要人工复核"],
        "允许处理": "补充候选案例、只读验收样本、公共层传参核对。",
        "禁止处理": "生成正式税务结论、登录税局、接财税软件。",
    },
    {
        "编号": "UFT-003",
        "业务线": "股票研究",
        "反馈问题": "前台展示是否清楚、是否仍有交易化表达。",
        "必填字段": ["股票名称", "报告类型", "实际表述", "期望表述", "是否出现交易化措辞"],
        "允许处理": "展示层措辞修复、只读扫雷、候选样本沉淀。",
        "禁止处理": "接券商、交易、修改核心评分引擎。",
    },
    {
        "编号": "UFT-004",
        "业务线": "视频制作",
        "反馈问题": "脚本、分镜、预检阻断是否可理解。",
        "必填字段": ["任务ID", "阶段", "实际输出", "不清楚点", "是否请求真实渲染/发布"],
        "允许处理": "预检说明、放行链复核卡、脚本/分镜候选优化。",
        "禁止处理": "真实渲染、上传、自动发布、触发 n8n。",
    },
    {
        "编号": "UFT-005",
        "业务线": "智能进化候选",
        "反馈问题": "候选经验是否应该继续保留、合并或撤回。",
        "必填字段": ["候选包名称", "反馈类型", "理由", "是否影响正式规则", "建议下一步"],
        "允许处理": "候选补充、只读验收建议、差异说明。",
        "禁止处理": "自动转正式规则、修改运行配置、修改总管面板或一键接续包。",
    },
]


CLASSIFICATION_RULES = [
    {"级别": "F1", "含义": "措辞/说明不清楚", "处理": "允许补文档、模板、候选说明。"},
    {"级别": "F2", "含义": "只读验收样本缺口", "处理": "允许新增候选样本和只读核对。"},
    {"级别": "F3", "含义": "运行态或服务加载相关", "处理": "停止，登记需总管确认。"},
    {"级别": "F4", "含义": "真实外部动作请求", "处理": "停止，红线未开放。"},
    {"级别": "F5", "含义": "正式规则/总管资产变更", "处理": "停止，只写候选差异说明。"},
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_template_md(report: dict[str, Any]) -> str:
    lines = ["# 用户反馈样本模板", "", "反馈只用于低风险候选改进，不授权真实外部动作。", ""]
    for item in report["反馈模板"]:
        lines.extend(
            [
                f"## {item['编号']} {item['业务线']}",
                "",
                f"- 反馈问题：{item['反馈问题']}",
                f"- 必填字段：{', '.join(item['必填字段'])}",
                f"- 允许处理：{item['允许处理']}",
                f"- 禁止处理：{item['禁止处理']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_classify_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['级别']} | {item['含义']} | {item['处理']} |" for item in report["反馈分级规则"]]
    return "\n".join(["# 反馈分级与处理边界", "", "| 级别 | 含义 | 处理 |", "| --- | --- | --- |", *rows, ""])


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险用户反馈样本模板包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 反馈模板：{len(report['反馈模板'])}",
            f"- 反馈分级规则：{len(report['反馈分级规则'])}",
            "",
            f"- 用户反馈样本模板：{TEMPLATE_MD}",
            f"- 反馈分级与处理边界：{CLASSIFY_MD}",
            "",
            "## 核心口径",
            "",
            "- 只收集低风险反馈样本，不接外部系统。",
            "- F3/F4/F5 必须停止并汇报或等待确认。",
        ]
    )


def main() -> int:
    report = {
        "名称": "低风险用户反馈样本模板包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "low_risk_user_feedback_template_ready",
        "反馈模板": FEEDBACK_TEMPLATES,
        "反馈分级规则": CLASSIFICATION_RULES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "用户反馈样本模板": str(TEMPLATE_MD),
            "反馈分级与处理边界": str(CLASSIFY_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(TEMPLATE_MD, build_template_md(report))
    write_text(CLASSIFY_MD, build_classify_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "反馈模板": len(FEEDBACK_TEMPLATES), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
