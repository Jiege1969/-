# -*- coding: utf-8 -*-
"""
名称：生成企业微信助手统一路由状态基线.py
作用：在总管侧汇总企业微信助手统一指令路由、本地调用、本地服务、速查卡和状态摘要验收，形成低风险状态基线。
触发方式：python 生成企业微信助手统一路由状态基线.py
所属系统：00杰哥系统总管 / 02杰哥扩展系统/06企业微信助手系统
安全边界：只运行企业微信助手现有本地预演与验收脚本；只写00总管运行状态报告；
不发送企业微信；不触发Webhook；不触发n8n；不写正式库；不写旧系统；不重启19300/19302；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
WECOM = ROOT / "02杰哥扩展系统" / "06企业微信助手系统"
OUT_DIR = MANAGER / "03数据" / "运行状态"
WECOM_SCRIPT_DIR = WECOM / "02脚本"
WECOM_DATA_DIR = WECOM / "03数据"

SCRIPTS = [
    ("统一指令路由预演验收", WECOM_SCRIPT_DIR / "验证企业微信统一指令路由预演.py"),
    ("统一指令本地调用预演验收", WECOM_SCRIPT_DIR / "验证企业微信统一指令本地调用预演.py"),
    ("统一指令本地服务入口验收", WECOM_SCRIPT_DIR / "验证企业微信统一指令本地服务入口.py"),
    ("统一指令使用速查卡验收", WECOM_SCRIPT_DIR / "验证企业微信统一指令使用速查卡.py"),
    ("企业微信助手系统状态摘要验收", WECOM_SCRIPT_DIR / "验证企业微信助手系统状态摘要.py"),
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(name: str, script: Path, timeout: int = 120) -> dict[str, Any]:
    if not script.exists():
        return {
            "名称": name,
            "脚本": str(script),
            "存在": False,
            "退出码": 127,
            "标准输出": "",
            "标准错误": "脚本不存在",
            "输出解析": {},
        }
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=timeout,
    )
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(result.stdout.strip()) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        parsed = {}
    return {
        "名称": name,
        "脚本": str(script),
        "存在": True,
        "退出码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
        "输出解析": parsed,
    }


def bool_false_map(keys: list[str]) -> dict[str, bool]:
    return {key: False for key in keys}


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    lines = [
        "# 企业微信助手统一路由状态基线",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 脚本通过：{summary['脚本通过数量']}/{summary['脚本总数']}",
        f"- 系统状态：{summary['系统状态']}",
        f"- 路由命中：{summary['路由命中期望数量']}/{summary['路由样例数量']}",
        f"- 本地调用成功：{summary['本地调用成功数量']}/{summary['本地调用样例数量']}",
        f"- 本地服务验收：{summary['本地服务验收通过数量']}/{summary['本地服务验收总数']}",
        f"- 速查卡指令数量：{summary['速查卡指令数量']}",
        f"- 真实动作数量：{summary['真实动作数量']}",
        "",
        "## 脚本执行",
        "",
    ]
    for item in report["脚本执行"]:
        status = "通过" if item["退出码"] == 0 else "失败"
        lines.append(f"- {item['名称']}：{status}，退出码 {item['退出码']}")
    lines.extend(["", "## 风险与缺口", ""])
    for item in report["风险与缺口"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.extend([
        "- 本轮不发送企业微信、不触发Webhook、不触发n8n。",
        "- 本轮不写正式库、不写旧系统、不重启19300/19302。",
        "- 本轮不调用券商接口、不自动交易、不替换正式入口。",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    script_runs = [run_script(name, script) for name, script in SCRIPTS]
    status_report = load_json(WECOM_DATA_DIR / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json", {})
    route_report = load_json(WECOM_DATA_DIR / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json", {})
    local_call_report = load_json(WECOM_DATA_DIR / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json", {})
    quick_card_report = load_json(WECOM_DATA_DIR / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json", {})

    status_summary = status_report.get("汇总", {})
    route_summary = route_report.get("汇总", {})
    local_call_summary = local_call_report.get("汇总", {})
    safety = status_report.get("安全边界", {})
    passed_scripts = [item for item in script_runs if item["退出码"] == 0]
    failed_scripts = [item for item in script_runs if item["退出码"] != 0]
    real_action_count = int(route_summary.get("真实动作数量", 0) or 0) + int(local_call_summary.get("真实动作数量", 0) or 0)

    safety_ok = (
        safety.get("企业微信真实发送") is False
        and safety.get("触发Webhook") is False
        and safety.get("触发n8n") is False
        and safety.get("写旧系统") is False
        and safety.get("接入税收") is False
        and safety.get("交易接口") is False
    )
    route_ok = (
        route_summary.get("状态") == "healthy"
        and route_summary.get("样例数量") == route_summary.get("命中期望数量")
        and int(route_summary.get("真实动作数量", 1) or 0) == 0
    )
    local_call_ok = (
        local_call_summary.get("状态") == "healthy"
        and local_call_summary.get("样例数量") == local_call_summary.get("调用成功数量")
        and int(local_call_summary.get("真实动作数量", 1) or 0) == 0
    )
    status_ok = status_summary.get("状态") == "healthy"
    quick_card_ok = quick_card_report.get("总体状态") == "healthy" and int(quick_card_report.get("指令数量", 0) or 0) >= 7
    all_ok = not failed_scripts and status_ok and route_ok and local_call_ok and quick_card_ok and safety_ok and real_action_count == 0

    gaps: list[str] = []
    if failed_scripts:
        gaps.append("存在脚本验收失败：" + "、".join(item["名称"] for item in failed_scripts))
    if not status_ok:
        gaps.append("企业微信助手系统状态摘要未达到 healthy。")
    if not route_ok:
        gaps.append("统一指令路由预演未全部命中或存在真实动作。")
    if not local_call_ok:
        gaps.append("统一指令本地调用预演未全部成功或存在真实动作。")
    if not quick_card_ok:
        gaps.append("统一指令速查卡未达到 healthy 或常用入口不足。")
    if not safety_ok:
        gaps.append("企业微信助手安全边界存在非关闭项。")
    if not gaps:
        gaps.append("未发现阻断；本轮只形成状态基线，不替换正式入口。")

    report = {
        "名称": "企业微信助手统一路由状态基线",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if all_ok else "失败",
        "所属系统": "02杰哥扩展系统/06企业微信助手系统",
        "汇总": {
            "脚本总数": len(script_runs),
            "脚本通过数量": len(passed_scripts),
            "脚本失败数量": len(failed_scripts),
            "系统状态": status_summary.get("状态", "unknown"),
            "路由状态": route_summary.get("状态", "unknown"),
            "路由样例数量": route_summary.get("样例数量", 0),
            "路由命中期望数量": route_summary.get("命中期望数量", 0),
            "本地调用状态": local_call_summary.get("状态", "unknown"),
            "本地调用样例数量": local_call_summary.get("样例数量", 0),
            "本地调用成功数量": local_call_summary.get("调用成功数量", 0),
            "本地服务状态": status_summary.get("统一指令本地服务状态", "unknown"),
            "本地服务验收通过数量": status_summary.get("本地服务验收通过数量", 0),
            "本地服务验收失败数量": status_summary.get("本地服务验收失败数量", 0),
            "本地服务验收总数": status_summary.get("本地服务验收总数", 0),
            "速查卡状态": quick_card_report.get("总体状态", "unknown"),
            "速查卡指令数量": quick_card_report.get("指令数量", 0),
            "真实动作数量": real_action_count,
            "企业微信真实发送": safety.get("企业微信真实发送"),
            "触发Webhook": safety.get("触发Webhook"),
            "触发n8n": safety.get("触发n8n"),
        },
        "脚本执行": script_runs,
        "引用产物": {
            "企业微信助手状态摘要": str(WECOM_DATA_DIR / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json"),
            "统一指令路由预演": str(WECOM_DATA_DIR / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"),
            "统一指令本地调用预演": str(WECOM_DATA_DIR / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"),
            "统一指令速查卡": str(WECOM_DATA_DIR / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json"),
        },
        "风险与缺口": gaps,
        "安全边界": bool_false_map([
            "发送企业微信",
            "触发Webhook",
            "触发n8n",
            "写正式库",
            "写旧系统",
            "重启19300",
            "重启19302",
            "调用券商接口",
            "自动交易",
            "替换正式入口",
        ]),
    }

    latest_json = OUT_DIR / "企业微信助手统一路由状态基线_最新.json"
    latest_md = OUT_DIR / "企业微信助手统一路由状态基线_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "脚本通过数量": report["汇总"]["脚本通过数量"],
        "脚本失败数量": report["汇总"]["脚本失败数量"],
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
