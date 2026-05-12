# -*- coding: utf-8 -*-
"""
名称：验证企业微信股票L3接入对齐.py
作用：验证公共企业微信接入层的股票路由、预演、速查卡和门禁已对齐股票系统L3结论型短答，不退回旧technical接口或旧买入研究信号模板。
触发方式：python 验证企业微信股票L3接入对齐.py
依赖：Python标准库；企业微信统一指令配置、最新预演、速查卡、灰度门禁和状态摘要。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只读配置和最新预演结果，只写验收报告；不真实发送企业微信；不触发Webhook；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


OLD_STOCK_WORDS = ["买入研究信号", "研究星级", "19300/technical", "technical?stock", "新易盛（sz300502）"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def route_rule(route_config: dict[str, Any], route_name: str) -> dict[str, Any]:
    for item in route_config.get("路由规则", []):
        if item.get("路由") == route_name:
            return item if isinstance(item, dict) else {}
    return {}


def call_rule(call_config: dict[str, Any], route_name: str) -> dict[str, Any]:
    item = call_config.get("允许本地调用", {}).get(route_name, {})
    return item if isinstance(item, dict) else {}


def first_local_item(local_preview: dict[str, Any], route_name: str) -> dict[str, Any]:
    for item in local_preview.get("调用结果", []):
        if item.get("路由") == route_name:
            return item if isinstance(item, dict) else {}
    return {}


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['名称']} | {'通过' if item['通过'] else '失败'} |"
        for item in report["检查项"]
    ]
    lines = [
        "# 企业微信股票L3接入对齐验收",
        "",
        f"生成时间：{report['生成时间']}",
        f"总体状态：{report['汇总']['状态']}",
        f"通过：{report['汇总']['通过']} / {report['汇总']['总数']}",
        "",
        "| 检查项 | 结果 |",
        "|---|---:|",
        *rows,
        "",
        "## 边界",
        "",
        "- 不真实发送企业微信",
        "- 不触发 Webhook",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "- 真实灰度必须另行人工确认",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    route_config = load_json(root / "01配置" / "企业微信统一指令路由预演规则.json", {}) or {}
    call_config = load_json(root / "01配置" / "企业微信统一指令本地调用预演规则.json", {}) or {}
    gray_rule = load_json(root / "01配置" / "企业微信统一指令灰度放行规则.json", {}) or {}
    local_preview = load_json(root / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json", {}) or {}
    quick_card = load_json(root / "03数据" / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json", {}) or {}
    gray_gate = load_json(root / "03数据" / "10统一指令灰度放行门禁" / "wecom-unified-command-gray-gate-最新.json", {}) or {}
    status = load_json(root / "03数据" / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json", {}) or {}

    stock_route = route_rule(route_config, "股票研究")
    stock_call = call_rule(call_config, "股票研究")
    stock_local = first_local_item(local_preview, "股票研究")
    quick_text = json.dumps(quick_card, ensure_ascii=False)
    local_text = json.dumps(local_preview, ensure_ascii=False)
    current_text = "\n".join([
        json.dumps(route_config, ensure_ascii=False),
        json.dumps(call_config, ensure_ascii=False),
        local_text,
        quick_text,
        json.dumps(gray_gate, ensure_ascii=False),
        json.dumps(status, ensure_ascii=False),
    ])

    gray_scope = gray_rule.get("灰度范围", {}) if isinstance(gray_rule.get("灰度范围"), dict) else {}
    gray_summary = gray_gate.get("汇总", {}) if isinstance(gray_gate.get("汇总"), dict) else {}
    status_summary = status.get("汇总", {}) if isinstance(status.get("汇总"), dict) else {}
    safety = status.get("安全边界", {}) if isinstance(status.get("安全边界"), dict) else {}

    checks: list[dict[str, Any]] = []
    add_check(checks, "股票路由存在", bool(stock_route), stock_route)
    add_check(checks, "股票样例为L3短答入口", any(str(item.get("输入", "")).startswith("分析云南锗业") for item in route_config.get("预演样例", [])), route_config.get("预演样例", []))
    add_check(checks, "股票调用方式为L3桥接dry-run", stock_call.get("方式") == "stock_l3_wecom_dry_run", stock_call)
    add_check(checks, "股票调用URL为19302桥接入口", "19302/wecom-bot/message" in str(stock_call.get("URL", "")), stock_call)
    add_check(checks, "本地预演股票调用成功", stock_local.get("调用状态") == "完成", stock_local)
    add_check(checks, "本地预演股票来源为19302", "19302/wecom-bot/message" in str(stock_local.get("来源", "")), stock_local.get("来源"))
    add_check(checks, "股票短答为L3结论型格式", all(word in str(stock_local.get("回复预演", "")) for word in ["分析对象：", "结论：", "缺口：", "仅供研究参考"]), str(stock_local.get("回复预演", ""))[:500])
    add_check(checks, "当前产物不含旧股票模板", not any(word in current_text for word in OLD_STOCK_WORDS), "")
    add_check(checks, "本地调用真实动作数为0", local_preview.get("汇总", {}).get("真实动作数量") == 0, local_preview.get("汇总", {}))
    add_check(checks, "速查卡健康", quick_card.get("总体状态") == "healthy", quick_card.get("总体状态"))
    add_check(checks, "灰度门禁本地影子通过", gray_summary.get("门禁状态") == "pass", gray_summary)
    add_check(checks, "真实灰度最大消息数为0", int_value(gray_summary.get("最大首轮真实消息数"), 99) == 0 and int_value(gray_scope.get("最大首轮真实消息数"), 99) == 0, {"summary": gray_summary, "rule": gray_scope})
    add_check(checks, "真实灰度需人工确认", "必须另行人工确认" in str(gray_summary.get("放行结论", "")) and gray_scope.get("允许真实灰度") is False, {"summary": gray_summary, "rule": gray_scope})
    add_check(
        checks,
        "状态摘要安全边界可读",
        bool(status_summary)
        and status_summary.get("是否企业微信真实发送") is False
        and status_summary.get("是否触发Webhook") is False
        and status_summary.get("是否触发n8n") is False,
        status_summary,
    )
    add_check(checks, "未真实发送企业微信", safety.get("企业微信真实发送") is False and status_summary.get("是否企业微信真实发送") is False, {"summary": status_summary, "safety": safety})
    add_check(checks, "未触发Webhook", safety.get("触发Webhook") is False and status_summary.get("是否触发Webhook") is False, {"summary": status_summary, "safety": safety})
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False and status_summary.get("是否触发n8n") is False, {"summary": status_summary, "safety": safety})
    add_check(checks, "未接入交易接口", safety.get("交易接口") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-stock-l3-alignment-verify",
        "汇总": {
            "状态": "passed" if passed == len(checks) else "failed",
            "通过": passed,
            "总数": len(checks),
            "失败": len(checks) - passed,
        },
        "检查项": checks,
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    out_dir = root / "04日志"
    latest_json = out_dir / "wecom-stock-l3-alignment-verify-最新.json"
    latest_md = out_dir / "企业微信股票L3接入对齐验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({"状态": report["汇总"]["状态"], "通过": passed, "失败": len(checks) - passed, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if report["汇总"]["状态"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
