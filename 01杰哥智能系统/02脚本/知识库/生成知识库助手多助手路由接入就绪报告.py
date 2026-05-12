# -*- coding: utf-8 -*-
"""
名称：生成知识库助手多助手路由接入就绪报告.py
作用：汇总知识库可追溯问答入口、企业微信统一指令路由预演和机器人终端分工，形成知识库助手接入多助手路由的就绪报告。
触发方式：python 生成知识库助手多助手路由接入就绪报告.py
依赖：Python标准库；知识库可追溯问答入口验收日志；企业微信统一指令路由/本地调用预演；企业微信机器人终端分工总表。
所属系统：01杰哥智能系统/知识库
安全边界：只读取01智能系统与06企业微信助手系统的既有验收报告；只写入01智能系统03数据/知识库/09多助手路由接入就绪；不修改企业微信配置、不发送企业微信、不触发n8n、不写正式库、不改股票脚本。
创建/修改记录：2026-05-05 创建知识库助手多助手路由接入就绪报告。
标识：knowledge-assistant-route-readiness-report-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
WECOM_ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "06企业微信助手系统"
OUTPUT_DIR = SMART_ROOT / "03数据" / "知识库" / "09多助手路由接入就绪"


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


def find_route_sample(report: dict[str, Any], route_name: str) -> dict[str, Any]:
    for item in report.get("样例结果", []):
        if item.get("命中路由") == route_name:
            return item
    return {}


def find_call_sample(report: dict[str, Any], route_name: str) -> dict[str, Any]:
    for item in report.get("调用结果", []):
        if item.get("路由") == route_name:
            return item
    return {}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库助手多助手路由接入就绪报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 就绪状态：{report['汇总']['就绪状态']}",
        f"- 通过项：{report['汇总']['通过数量']}",
        f"- 阻塞项：{report['汇总']['阻塞数量']}",
        "",
        "## 接入结论",
        "",
        report["接入结论"],
        "",
        "## 路由建议",
        "",
    ]
    for item in report["路由建议"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 检查项", ""])
    for item in report["检查项"]:
        mark = "通过" if item["通过"] else "阻塞"
        lines.append(f"- {mark}：{item['名称']} - {item['说明']}")
    lines.extend(["", "## 阻塞项", ""])
    for item in report["阻塞项"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    entry_verify_path = SMART_ROOT / "04日志" / "知识库" / "knowledge-traceable-qa-entry-verify-最新.json"
    entry_output_path = SMART_ROOT / "03数据" / "知识库" / "08可追溯问答入口" / "知识库可追溯问答入口输出_最新.json"
    route_path = WECOM_ROOT / "03数据" / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"
    local_call_path = WECOM_ROOT / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"
    terminal_path = WECOM_ROOT / "01配置" / "企业微信机器人终端分工总表.json"

    entry_verify = load_json(entry_verify_path, {})
    entry_output = load_json(entry_output_path, {})
    route = load_json(route_path, {})
    local_call = load_json(local_call_path, {})
    terminal = load_json(terminal_path, {})
    route_sample = find_route_sample(route, "知识库问答")
    call_sample = find_call_sample(local_call, "知识库问答")
    terminals = terminal.get("终端列表", [])
    pending_terminals = [item.get("名称", "") for item in terminals if "待桥接" in str(item.get("启用状态", ""))]

    checks = [
        {
            "名称": "知识库可追溯问答入口验收通过",
            "通过": entry_verify.get("汇总", {}).get("失败") == 0,
            "说明": str(entry_verify_path),
        },
        {
            "名称": "知识库入口输出可被路由层读取",
            "通过": entry_output.get("汇总", {}).get("状态") == "pass",
            "说明": str(entry_output_path),
        },
        {
            "名称": "统一指令路由包含知识库问答",
            "通过": bool(route_sample) and route_sample.get("是否命中期望") is True and route_sample.get("真实动作") is False,
            "说明": route_sample,
        },
        {
            "名称": "统一指令本地调用包含知识库问答",
            "通过": bool(call_sample) and call_sample.get("调用状态") in {"healthy", "完成"} and call_sample.get("真实发送企业微信") is False,
            "说明": call_sample,
        },
        {
            "名称": "企业微信终端分工明确",
            "通过": len(terminals) >= 5 and "杰哥系统管家" in pending_terminals,
            "说明": {"终端数量": len(terminals), "待桥接终端": pending_terminals},
        },
    ]
    blockers = [
        "知识库助手尚未独立登记为正式企业微信机器人；当前以统一指令路由中的知识库问答能力存在。",
        "正式知识库内容覆盖不足，当前索引主要是测试文档，适合验收机制，不适合正式业务问答。",
        "正式向量生成和正式向量库写入仍关闭；若要升级语义检索，需要先走入库复核和写库门禁。",
        "系统管家、工作秘书、视频助理仍待桥接服务接入；不应误报为已正式上线。",
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    ready_state = "route_ready_local_only" if failed == 0 else "attention_required"
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-assistant-route-readiness",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "就绪状态": ready_state,
            "通过数量": passed,
            "阻塞数量": failed,
            "是否修改企业微信配置": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写正式库": False,
        },
        "接入结论": "知识库助手已具备本地路由调用条件，可作为统一指令路由的 local_preview_only 能力继续接入；正式企业微信独立助手、真实发送和向量写库仍需后续受控推进。",
        "路由建议": [
            "资料依据、来源追溯、查知识库、这份文件依据是什么 -> 知识库问答。",
            "系统状态、施工进度、接续包 -> 杰哥系统管家，不由知识库助手代答。",
            "股票名称、代码、个股怎么看 -> 股票助手或股票专家，不由知识库助手接管。",
            "知识库问答输出必须保留来源文件、分块序号和证据摘录；没有来源时返回拒答。",
        ],
        "检查项": checks,
        "阻塞项": blockers,
        "输入报告": {
            "入口验收": str(entry_verify_path),
            "入口输出": str(entry_output_path),
            "统一指令路由预演": str(route_path),
            "统一指令本地调用预演": str(local_call_path),
            "企业微信终端分工": str(terminal_path),
        },
        "安全边界": {
            "修改股票研究系统脚本": False,
            "修改企业微信正式配置": False,
            "修改总管进度标准文件": False,
            "覆盖正式知识库": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
        },
    }
    output_json = OUTPUT_DIR / f"知识库助手多助手路由接入就绪报告_{timestamp}.json"
    latest_json = OUTPUT_DIR / "知识库助手多助手路由接入就绪报告_最新.json"
    output_md = OUTPUT_DIR / f"知识库助手多助手路由接入就绪报告_{timestamp}.md"
    latest_md = OUTPUT_DIR / "知识库助手多助手路由接入就绪报告_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": ready_state, "通过": passed, "阻塞": failed, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
