# -*- coding: utf-8 -*-
"""
名称：生成企业微信统一指令灰度放行门禁.py
作用：读取企业微信接入设置状态摘要、统一指令路由预演和统一指令本地调用预演，生成是否只允许本地/影子预演或具备真实灰度前置条件的门禁报告。
触发方式：python 生成企业微信统一指令灰度放行门禁.py
依赖：Python标准库；企业微信统一指令灰度放行规则.json；企业微信接入设置状态摘要；统一指令路由预演；统一指令本地调用预演。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只读取本系统配置和03数据状态摘要；只写入03数据/10统一指令灰度放行门禁；不真实发送企业微信；不触发Webhook；不触发n8n；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令灰度放行门禁生成脚本。
标识：wecom-unified-command-gray-gate-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


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


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    lines = [
        "# 企业微信统一指令灰度放行门禁",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 门禁状态：{summary['门禁状态']}",
        f"- 放行结论：{summary['放行结论']}",
        f"- 最大首轮真实消息数：{summary['最大首轮真实消息数']}",
        f"- 通过项：{summary['通过数量']}",
        f"- 失败项：{summary['失败数量']}",
        "",
        "## 检查项",
        "",
    ]
    for item in report["检查项"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {mark}：{item['名称']}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本报告只判断门禁条件，不发送企业微信。",
            "- 当前真实灰度不自动放行；扩大白名单、真实发送、交易接口、税收真实业务、写旧系统、写正式业务库仍保持禁止，除非另有当日人工确认令。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据"
    rule = load_json(root / "01配置" / "企业微信统一指令灰度放行规则.json", {})
    status_report = load_json(data_root / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json", {})
    route_report = load_json(data_root / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json", {})
    local_report = load_json(data_root / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json", {})

    status_summary = status_report.get("汇总", {})
    route_summary = route_report.get("汇总", {})
    local_summary = local_report.get("汇总", {})
    gray_scope = rule.get("灰度范围", {})
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "企业微信接入设置状态摘要安全边界可读",
        bool(status_summary)
        and status_summary.get("真实发送状态") == "禁用态"
        and status_summary.get("是否触发Webhook") is False
        and status_summary.get("是否触发n8n") is False,
        status_summary,
    )
    add_check(checks, "统一指令路由预演健康", route_summary.get("状态") == "healthy", route_summary)
    add_check(checks, "统一指令本地调用预演健康", local_summary.get("状态") == "healthy", local_summary)
    add_check(checks, "路由样例全部命中期望", route_summary.get("样例数量") == route_summary.get("命中期望数量") and int(route_summary.get("样例数量", 0) or 0) >= 6, route_summary)
    add_check(checks, "本地调用样例全部成功", local_summary.get("样例数量") == local_summary.get("调用成功数量") and int(local_summary.get("样例数量", 0) or 0) >= 6, local_summary)
    add_check(checks, "路由无真实动作", int(route_summary.get("真实动作数量", 1) or 0) == 0, route_summary)
    add_check(checks, "本地调用无真实动作", int(local_summary.get("真实动作数量", 1) or 0) == 0, local_summary)
    add_check(checks, "真实发送执行器仍为禁用态", status_summary.get("真实发送状态") == "禁用态", status_summary)
    add_check(checks, "Webhook关闭", status_summary.get("是否触发Webhook") is False, status_summary)
    add_check(checks, "n8n触发关闭", status_summary.get("是否触发n8n") is False, status_summary)
    add_check(checks, "当前首轮真实消息数为0", int_value(gray_scope.get("最大首轮真实消息数"), 99) == 0, gray_scope)
    add_check(checks, "当前不自动放行真实灰度", int_value(gray_scope.get("最大首轮真实消息数"), 99) == 0 and gray_scope.get("允许真实灰度") is False, gray_scope)
    add_check(checks, "不允许扩大白名单", gray_scope.get("允许扩大白名单") is False, gray_scope)
    add_check(checks, "不允许交易接口", gray_scope.get("允许交易接口") is False, gray_scope)
    add_check(checks, "不允许税收真实业务", gray_scope.get("允许税收真实业务") is False, gray_scope)
    add_check(checks, "不允许写旧系统", gray_scope.get("允许写旧系统") is False, gray_scope)
    add_check(checks, "不允许写正式业务库", gray_scope.get("允许写正式业务库") is False, gray_scope)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    gate_status = "pass" if failed == 0 else "blocked"
    max_real_messages = int_value(gray_scope.get("最大首轮真实消息数"), 0)
    conclusion = (
        "本地/影子预演通过；当前真实灰度仍未放行，必须另行人工确认"
        if gate_status == "pass" and max_real_messages == 0
        else ("满足真实灰度前置检查，但真实发送仍需另行人工确认" if gate_status == "pass" else "保持本地预演，不进入真实灰度")
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-gray-gate",
        "所属系统": "02杰哥扩展系统/00公共组件/企业微信接入设置",
        "汇总": {
            "门禁状态": gate_status,
            "放行结论": conclusion,
            "最大首轮真实消息数": gray_scope.get("最大首轮真实消息数", 5),
            "通过数量": passed,
            "失败数量": failed,
        },
        "检查项": checks,
        "规则": rule,
        "状态摘要报告": str(data_root / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json"),
        "路由预演报告": str(data_root / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"),
        "本地调用预演报告": str(data_root / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"),
    }

    output_dir = data_root / "10统一指令灰度放行门禁"
    latest_json = output_dir / "wecom-unified-command-gray-gate-最新.json"
    latest_md = output_dir / "企业微信统一指令灰度放行门禁_最新.md"
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    print(json.dumps({"门禁状态": gate_status, "通过": passed, "失败": failed, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if gate_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
