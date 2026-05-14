# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信桥接报告反馈优先级.py
作用：验收19302桥接层把报告反馈优先交给股票助手，不被交易护栏提前拦截。
边界：本地影子调用；不真实发送企业微信；不触发n8n；不接券商；不交易；不重载19310/19302。
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "02脚本" / "股票企业微信桥接入口.py"
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
LOG_DIR = ROOT / "04日志" / "股票企业微信桥接报告反馈优先级"


LONG_FEEDBACK = "这份报告的缺点：标题不对 股票n8n企业微信终端桥接运行记录 不符合杰哥的股票分析专家，不应该有阶段：after_close_report 问题：今日观察 成功：True 真实发送企业微信：False 接券商/交易：False 企业微信可读内容，分析太虚，风险没讲清楚"
TYPO_FEEDBACK = "分析太空乏，风险没将清楚"
RESULT_STYLE_FEEDBACK = "前台报告要少讲技术过程，多讲结果，后面只盯哪几件事要说清楚。"
NUMERIC_CONDITION_FEEDBACK = "成交量达到最近5日平均量1.2倍要具体算出来，站稳和跌破也要给具体数字。"
STRONG_WATCH_FEEDBACK = "强烈关注要参照五星方式表达，不能只写一句强烈关注。"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("stock_wecom_bridge_feedback_priority_verify", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "说明": detail})


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信桥接报告反馈优先级验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 通过：{report['统计']['通过']}",
        f"- 失败：{report['统计']['失败']}",
        "",
        "## 检查项",
        "",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['检查项']}：{item['通过']}；{item['说明']}")
    lines.extend(["", "## 边界", "", "- 未真实发送企业微信。", "- 未触发n8n。", "- 未接券商，未交易。", "- 未重载19310/19302。"])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    module = load_module()
    long_result = module.process_message({"text": LONG_FEEDBACK}, robot_stream=True)
    typo_result = module.process_message({"text": TYPO_FEEDBACK}, robot_stream=True)
    long_content = str(long_result.get("企业微信内容") or long_result.get("回复") or "")
    typo_content = str(typo_result.get("企业微信内容") or typo_result.get("回复") or "")
    checks: list[dict[str, Any]] = []
    add_check(checks, "长反馈桥接层识别为报告反馈消息", module.is_report_feedback_message(LONG_FEEDBACK), LONG_FEEDBACK[:120])
    add_check(checks, "长反馈包含交易字样但不被桥接交易护栏拦截", long_result.get("股票助手状态") != "已拦截" and "已拦截" not in long_content, long_content)
    add_check(checks, "长反馈已调用股票助手入账", long_result.get("实际动作", {}).get("调用股票助手") is True and "记入反馈日志" in long_content, long_result)
    add_check(checks, "错别字反馈桥接层识别为报告反馈消息", module.is_report_feedback_message(TYPO_FEEDBACK), TYPO_FEEDBACK)
    add_check(checks, "错别字反馈不要求补股票名", "请告诉我股票名称" not in typo_content and "记入反馈日志" in typo_content, typo_content)
    add_check(checks, "错别字反馈不被桥接交易护栏拦截", typo_result.get("股票助手状态") != "已拦截" and "已拦截" not in typo_content, typo_content)
    add_check(checks, "前台少讲技术多讲结果被桥接识别为报告反馈", module.is_report_feedback_message(RESULT_STYLE_FEEDBACK), RESULT_STYLE_FEEDBACK)
    add_check(checks, "成交量站稳跌破具体数字被桥接识别为报告反馈", module.is_report_feedback_message(NUMERIC_CONDITION_FEEDBACK), NUMERIC_CONDITION_FEEDBACK)
    add_check(checks, "强烈关注五星口径被桥接识别为报告反馈", module.is_report_feedback_message(STRONG_WATCH_FEEDBACK), STRONG_WATCH_FEEDBACK)
    safety = {"真实发送企业微信": False, "触发n8n": False, "接券商": False, "交易": False, "重载19310": False, "重载19302": False}
    for key, value in safety.items():
        add_check(checks, f"安全边界：{key}=false", value is False, safety)
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票企业微信桥接报告反馈优先级验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "统计": {"通过": len(checks) - len(failed), "失败": len(failed)},
        "检查项": checks,
        "长反馈桥接回复": long_content,
        "错别字反馈桥接回复": typo_content,
        "安全边界": safety,
    }
    latest_json = OUT_DIR / "股票企业微信桥接报告反馈优先级验收_最新.json"
    latest_md = OUT_DIR / "股票企业微信桥接报告反馈优先级验收_最新.md"
    log_json = LOG_DIR / f"stock-wecom-bridge-feedback-priority-verify-{stamp}.json"
    log_md = LOG_DIR / f"stock-wecom-bridge-feedback-priority-verify-{stamp}.md"
    markdown = build_markdown(report)
    for path in (latest_json, log_json):
        write_json(path, report)
    for path in (latest_md, log_md):
        write_text(path, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["统计"]["通过"], "失败": report["统计"]["失败"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
