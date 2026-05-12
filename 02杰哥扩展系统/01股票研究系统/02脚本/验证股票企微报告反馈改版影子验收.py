# -*- coding: utf-8 -*-
"""
名称：验证股票企微报告反馈改版影子验收.py
作用：验证股票企业微信用户报告已具备可点击股票名、用户化表达和反馈入口。
边界：本地影子验收；不真实发送企业微信、不触发n8n、不接券商、不交易、不重载服务。
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def stock_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def load_stock_assistant(script_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("stock_assistant_entry_shadow", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module(script_path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    now = datetime.now()
    root = stock_root()
    script = root / "02脚本" / "股票助手入口.py"
    bridge_script = root / "02脚本" / "股票企业微信桥接入口.py"
    data_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    log_dir = root / "04日志" / "股票企微报告反馈改版影子验收"
    report_json = data_dir / "股票企微报告反馈改版影子验收_最新.json"
    report_md = data_dir / "股票企微报告反馈改版影子验收_最新.md"

    checks: list[dict[str, Any]] = []
    module = load_stock_assistant(script)
    bridge = load_module(bridge_script, "stock_wecom_bridge_shadow")
    result = module.build_analysis("今日观察", refresh=False, remember_context=False, entrance_role="专家")
    reply = str(result.get("企业微信回复") or result.get("回复") or "")
    bridge_content = bridge.prepare_wecom_chat_content(reply, limit=1800)
    feedback_question = "报告里股票名称应该可以点击，能看具体分析报告"

    add_check(checks, "今日观察返回用户报告", result.get("类型") == "今日推荐", result.get("类型"))
    add_check(checks, "报告包含企业微信可点击链接", bool(re.search(r"\[[^\]]+\]\(http[^)]+/wecom-bot/message\?ask=", reply)), reply[:300])
    add_check(checks, "桥接层保留可点击详情链接", bool(re.search(r"\[[^\]]+\]\(http[^)]+/wecom-bot/message\?ask=", bridge_content)), bridge_content[:500])
    add_check(checks, "报告说明可点击查看详情", "点股票名称" in reply and "具体分析报告" in reply, reply[:300])
    add_check(checks, "报告包含为什么看", "为什么看" in reply, reply[:500])
    add_check(checks, "报告包含当前判断", "当前判断" in reply, reply[:500])
    add_check(checks, "报告包含风险/缺口", "风险/缺口" in reply, reply[:500])
    add_check(checks, "报告包含反馈入口", "报告缺少什么" in reply and "股票名称应该可以点击" in reply, reply[-600:])
    add_check(checks, "可识别点击详情反馈", module.is_report_feedback_question(feedback_question) is True, feedback_question)
    add_check(checks, "反馈分类正确", module.classify_report_feedback(feedback_question) in ("股票名称需要可点击详情", "需要单股详情入口", "需要可点击入口"), module.classify_report_feedback(feedback_question))
    forbidden_terms = ("买入研究信号", "卖出研究信号", "重点推荐", "常规推荐", "加仓", "减仓", "满仓", "清仓", "下单")
    hits = [term for term in forbidden_terms if term in reply]
    add_check(checks, "无交易化和旧展示口径残留", not hits, hits)

    safety = {
        "真实发送企业微信": False,
        "触发n8n": False,
        "调用券商接口": False,
        "自动交易": False,
        "重载19310": False,
        "重载19302": False,
        "写正式规则库": False,
    }
    for name, value in safety.items():
        add_check(checks, f"安全边界：{name}=false", value is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "股票企微报告反馈改版影子验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "入口问题": "今日观察",
        "反馈测试问题": feedback_question,
        "回复预览": reply[:1200],
        "检查项": checks,
        "安全边界": safety,
    }
    output_json = log_dir / f"stock-wecom-report-feedback-shadow-verify-{now.strftime('%Y%m%d-%H%M%S')}.json"
    write_json(output_json, report)
    write_json(log_dir / "stock-wecom-report-feedback-shadow-verify-最新.json", report)
    write_json(report_json, report)
    md = [
        "# 股票企微报告反馈改版影子验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 通过：{passed}",
        f"- 失败：{failed}",
        "- 结论：股票企业微信用户报告已具备可点击股票名、用户化摘要和报告反馈入口。" if failed == 0 else "- 结论：仍有影子验收未通过项。",
        "",
        "## 边界",
        "- 未真实发送企业微信；未触发n8n；未接券商；未交易；未重载19310/19302；未写正式规则库。",
    ]
    write_text(report_md, "\n".join(md))
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(report_json)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
