# -*- coding: utf-8 -*-
"""
名称：验证股票报告数据口径.py
作用：检查股票报告中的数据单位、前台措辞和证据状态，防止异常口径进入企微前台。
触发方式：python 验证股票报告数据口径.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读报告和数据文件；只写03数据验收目录；不触发n8n；不真实发送企业微信；不调用券商接口；不自动交易。
标识：stock-report-data-caliber-check
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_issue(issues: list[dict[str, Any]], level: str, item: str, message: str, suggestion: str) -> None:
    issues.append({
        "级别": level,
        "对象": item,
        "问题": message,
        "建议": suggestion,
    })


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y-%m-%d")

    ai_json_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.json"
    ai_md_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.md"
    single_report_dir = root / "03数据" / "135分层日报"
    front_regression_path = root / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.json"

    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    ai_data = load_json(ai_json_path, {})
    results = ai_data.get("分析结果", []) if isinstance(ai_data, dict) else []

    for item in results:
        name = item.get("名称") or item.get("代码") or "未知股票"
        text = str(item.get("analysis_text") or "")
        if "万亿元" in text:
            add_issue(
                issues,
                "严重",
                str(name),
                "AI分析文本出现“万亿元”成交额口径，疑似单位换算错误。",
                "重新生成报告前应使用亿元格式化字段；前台不得直接展示该原文。",
            )
        if "<font" in text or "</font>" in text:
            add_issue(
                issues,
                "严重",
                str(name),
                "AI分析文本出现HTML标签。",
                "前台仅允许纯文本星级和结论，不展示HTML标签。",
            )
        if "买入机会" in text or "卖出" in text:
            add_issue(
                issues,
                "严重",
                str(name),
                "AI分析文本出现交易倾向词。",
                "改为研究信号、观察、风险复核等表述。",
            )
        if "成交额为估算值" in text:
            add_issue(
                warnings,
                "提示",
                str(name),
                "成交额为估算值。",
                "报告应保留证据完整度提示，不直接作为确定事实。",
            )

    md_text = read_text(ai_md_path)
    if "<font" in md_text:
        add_issue(issues, "严重", "AI分析报告Markdown", "Markdown报告含HTML font标签。", "改为纯文本星级。")
    if "买入机会" in md_text:
        add_issue(issues, "严重", "AI分析报告Markdown", "Markdown报告含买入机会措辞。", "改为机会研究信号。")
    if re.search(r"\d+(?:\.\d+)?\s*万亿元", md_text):
        add_issue(issues, "严重", "AI分析报告Markdown", "Markdown报告含异常万亿元口径。", "重新生成或前台屏蔽原文。")

    single_report_files = sorted(
        [
            path for path in single_report_dir.glob("单股标准报告v2_*_最新.md")
            if path.name != "单股标准报告v2_最新.md"
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in single_report_files[:80]:
        text = read_text(path)
        item = path.stem.replace("单股标准报告v2_", "")
        if any(keyword in text for keyword in ["【杰哥推荐】方法材料包", "相近强势样本", "失败对照校验", "校准分层", "原始分数"]):
            add_issue(
                warnings,
                "提示",
                item,
                "单股标准报告疑似展示后台材料包或样本距离。",
                "前台报告只保留普通投资者可理解的结论、依据摘要、条件和风险；后台材料留在证据链。",
            )
        if any(keyword in text for keyword in ["财报：关键指标待接入", "待核验：公告", "证据缺口", "行业价格待核验"]):
            add_issue(
                warnings,
                "提示",
                item,
                "单股标准报告仍有财报、公告、行业价格等证据缺口。",
                "继续走既有单股证据核验链路补齐，不另建人工核验支线。",
            )
        if "买入" in text or "卖出" in text:
            add_issue(
                warnings,
                "提示",
                item,
                "单股标准报告存在交易化措辞。",
                "改为研究条件、观察条件、风险底线和状态变化，不输出交易指令。",
            )
        missing_terms = [term for term in ["【结论】", "当前价", "承接区", "转强线", "风险线"] if term not in text]
        if missing_terms:
            add_issue(
                warnings,
                "提示",
                item,
                f"单股标准报告缺少标准前台字段：{'、'.join(missing_terms)}。",
                "按标准样式保留核心结论、关键价位、观察条件、风险提醒。",
            )

    regression = load_json(front_regression_path, {})
    regression_failed = int(regression.get("失败数") or 0) if isinstance(regression, dict) else -1
    if regression_failed != 0:
        add_issue(
            issues,
            "严重",
            "企微前台交互回归",
            f"前台交互回归失败数={regression_failed}。",
            "先修复182企微前台交互回归验收，再继续报告上线。",
        )

    conclusion = "通过" if not issues else "存在严重问题"
    report = {
        "名称": "股票报告数据口径检查",
        "日期": today,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": conclusion,
        "严重问题数": len(issues),
        "提示数": len(warnings),
        "检查范围": {
            "AI分析报告JSON": str(ai_json_path),
            "AI分析报告Markdown": str(ai_md_path),
            "单股标准报告v2目录": str(single_report_dir),
            "企微前台交互回归": str(front_regression_path),
        },
        "严重问题": issues,
        "提示": warnings,
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写正式库": False,
        },
    }

    output_dir = root / "03数据" / "183报告数据口径检查"
    json_path = output_dir / f"股票报告数据口径检查_{stamp}.json"
    latest_json = output_dir / "股票报告数据口径检查_最新.json"
    md_path = output_dir / f"股票报告数据口径检查_{stamp}.md"
    latest_md = output_dir / "股票报告数据口径检查_最新.md"

    write_json(json_path, report)
    write_json(latest_json, report)

    lines = [
        f"# 股票报告数据口径检查 - {today}",
        "",
        f"- 状态：{conclusion}",
        f"- 严重问题数：{len(issues)}",
        f"- 提示数：{len(warnings)}",
        "- 安全边界：未真实发送企业微信，未触发n8n，未调用券商接口，未自动交易。",
        "",
        "## 严重问题",
        "",
    ]
    if issues:
        for issue in issues:
            lines.append(f"- {issue['对象']}：{issue['问题']} 建议：{issue['建议']}")
    else:
        lines.append("- 无。")
    lines.extend(["", "## 提示", ""])
    if warnings:
        for warning in warnings[:20]:
            lines.append(f"- {warning['对象']}：{warning['问题']} 建议：{warning['建议']}")
    else:
        lines.append("- 无。")

    write_text(md_path, "\n".join(lines) + "\n")
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": conclusion,
        "严重问题数": len(issues),
        "提示数": len(warnings),
        "报告": str(latest_md),
        "数据": str(latest_json),
    }, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
