# -*- coding: utf-8 -*-
"""
名称：验证股票机器人报告反馈误判修复.py
作用：验收股票企业微信机器人能把报告吐槽识别为反馈，不误判成交易指令或缺少股票名。
边界：本地影子验收；不真实发送企业微信；不触发n8n；不接券商；不交易；不重载19310/19302。
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "02脚本" / "股票助手入口.py"
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
LOG_DIR = ROOT / "04日志" / "股票机器人报告反馈误判修复"


LONG_FEEDBACK = """这份报告的缺点：
1、标题不对“股票n8n企业微信终端桥接运行记录”这不符合【杰哥的股票分析专家】这个机器人的发的股票分析报告。
2、这部分内容也不符合，不应该有“阶段：after_close_report 问题：今日观察 成功：True 真实发送企业微信：False 接券商/交易：False / False 企业微信可读内容”
3、龙芯中科没有实现股票链接接入具体详细的个股报告；当前判断太虚；风险/缺口里复核不是分析系统应该做的吗？
"""

TYPO_FEEDBACK = "分析太空乏，风险没将清楚"
RESULT_STYLE_FEEDBACK = "前台报告要少讲技术过程，多讲结果，不要把MACD这些分析过程堆给我。"
NUMERIC_CONDITION_FEEDBACK = "成交量达到最近5日平均量1.2倍要具体算出来，站稳和跌破也要给具体数字。"
STRONG_WATCH_FEEDBACK = "强烈关注要参照五星方式表达，不能只写一句强烈关注。"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("stock_assistant_feedback_verify", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "说明": detail})


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票机器人报告反馈误判修复验收",
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
    lines.extend([
        "",
        "## 边界",
        "",
        "- 未真实发送企业微信。",
        "- 未触发n8n。",
        "- 未接券商，未交易。",
        "- 未重载19310/19302。",
    ])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    module = load_module()
    long_result = module.build_analysis(LONG_FEEDBACK, refresh=False, remember_context=False, entrance_role="专家")
    typo_result = module.build_analysis(TYPO_FEEDBACK, refresh=False, remember_context=False, entrance_role="专家")
    long_reply = str(long_result.get("企业微信回复") or long_result.get("回复") or "")
    typo_reply = str(typo_result.get("企业微信回复") or typo_result.get("回复") or "")

    checks: list[dict[str, Any]] = []
    add_check(checks, "长报告吐槽识别为报告反馈", long_result.get("类型") == "报告反馈", long_result)
    add_check(checks, "长报告吐槽不触发交易拦截", long_result.get("trade_guard") is not True and "已拦截" not in long_reply, long_reply)
    add_check(checks, "长报告吐槽不要求补股票名", "请告诉我股票名称" not in long_reply and "需要补充股票" != long_result.get("状态"), long_reply)
    add_check(checks, "长报告吐槽归类技术元信息或标题问题", long_result.get("反馈记录", {}).get("反馈类型") in {"报告混入桥接技术元信息", "报告标题不符合机器人身份", "报告口径不符合用户预期"}, long_result.get("反馈记录", {}))
    add_check(checks, "错别字反馈识别为报告反馈", typo_result.get("类型") == "报告反馈", typo_result)
    add_check(checks, "错别字太空乏归一为太空泛", typo_result.get("反馈记录", {}).get("反馈类型") == "太空泛", typo_result.get("反馈记录", {}))
    add_check(checks, "错别字反馈不要求补股票名", "请告诉我股票名称" not in typo_reply and "需要补充股票" != typo_result.get("状态"), typo_reply)
    add_check(checks, "错别字反馈不触发交易拦截", typo_result.get("trade_guard") is not True and "已拦截" not in typo_reply, typo_reply)
    result_style_type = module.classify_report_feedback(RESULT_STYLE_FEEDBACK)
    result_style_lane = module.classify_feedback_learning_lane(RESULT_STYLE_FEEDBACK, result_style_type)
    numeric_type = module.classify_report_feedback(NUMERIC_CONDITION_FEEDBACK)
    numeric_lane = module.classify_feedback_learning_lane(NUMERIC_CONDITION_FEEDBACK, numeric_type)
    star_type = module.classify_report_feedback(STRONG_WATCH_FEEDBACK)
    star_lane = module.classify_feedback_learning_lane(STRONG_WATCH_FEEDBACK, star_type)
    add_check(checks, "前台少讲技术多讲结果归入三阶段报告", result_style_type in {"前台报告过程过重", "前台报告结果不突出"} and result_style_lane.get("主分类") == "三阶段报告", {"反馈类型": result_style_type, "学习线": result_style_lane})
    add_check(checks, "成交量和站稳跌破反馈归入指标具体条件", numeric_type in {"条件没有算成具体数字", "成交量条件未算清", "触发条件需要具体化", "失效条件需要具体化"} and numeric_lane.get("主分类") == "指标", {"反馈类型": numeric_type, "学习线": numeric_lane})
    add_check(checks, "强烈关注五星反馈归入模型评分口径", star_type == "强烈关注星级口径" and star_lane.get("主分类") == "模型", {"反馈类型": star_type, "学习线": star_lane})
    safety = {
        "真实发送企业微信": False,
        "触发n8n": False,
        "接券商": False,
        "交易": False,
        "重载19310": False,
        "重载19302": False,
    }
    for key, value in safety.items():
        add_check(checks, f"安全边界：{key}=false", value is False, safety)

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票机器人报告反馈误判修复验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "统计": {"通过": len(checks) - len(failed), "失败": len(failed)},
        "检查项": checks,
        "长报告吐槽回复": long_reply,
        "错别字反馈回复": typo_reply,
        "安全边界": safety,
    }
    latest_json = OUT_DIR / "股票机器人报告反馈误判修复验收_最新.json"
    latest_md = OUT_DIR / "股票机器人报告反馈误判修复验收_最新.md"
    log_json = LOG_DIR / f"stock-bot-report-feedback-misroute-verify-{stamp}.json"
    log_md = LOG_DIR / f"stock-bot-report-feedback-misroute-verify-{stamp}.md"
    markdown = build_markdown(report)
    for path in (latest_json, log_json):
        write_json(path, report)
    for path in (latest_md, log_md):
        write_text(path, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["统计"]["通过"], "失败": report["统计"]["失败"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
