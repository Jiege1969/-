# -*- coding: utf-8 -*-
"""
名称：生成企业微信助手系统状态摘要.py
作用：汇总企业微信助手沙箱回环、凭据隔离、真实发送禁用态、统一指令路由预演、统一指令本地调用预演、灰度放行门禁和统一出口边界，生成日常状态摘要。
触发方式：python 生成企业微信助手系统状态摘要.py
依赖：Python标准库；企业微信沙箱回环门禁报告；企业微信凭据隔离检查；企业微信真实发送禁用态检查；企业微信统一指令路由预演；企业微信统一指令本地调用预演；企业微信统一指令本地服务；企业微信统一指令灰度放行门禁；企业微信统一指令使用速查卡。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只读取企业微信助手系统本地日志和配置；只写入03数据/07状态摘要；不写真实凭据；不触发Webhook；不触发n8n；不发送企业微信；不写旧系统；不接入税收业务。
创建/修改记录：2026-04-29 创建企业微信助手系统状态摘要生成脚本；2026-04-29 纳入统一指令路由预演状态；2026-04-29 纳入统一指令本地调用预演状态；2026-04-29 纳入统一指令灰度放行门禁状态；2026-04-29 纳入统一指令使用速查卡状态；2026-04-29 纳入统一指令本地服务状态；2026-05-05 将本地系统健康与灰度放行状态解耦。
标识：wecom-assistant-system-status-summary-generate
"""

from __future__ import annotations

import json
import subprocess
import sys
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


def run_local_script(script: Path, timeout: int = 90) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "脚本": str(script),
        "退出码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    return "\n".join(
        [
            "# 企业微信助手系统状态摘要",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{summary['状态']}",
            f"- 沙箱脚本失败数：{summary['沙箱脚本失败数']}",
            f"- 凭据高风险发现数：{summary['凭据高风险发现数']}",
            f"- 真实发送状态：{summary['真实发送状态']}",
            f"- 统一指令路由：{summary['统一指令路由状态']}，样例命中 {summary['路由命中期望数量']}/{summary['路由样例数量']}",
            f"- 统一指令本地调用：{summary['统一指令本地调用状态']}，调用成功 {summary['本地调用成功数量']}/{summary['本地调用样例数量']}",
            f"- 统一指令本地服务：{summary['统一指令本地服务状态']}，验收 {summary['本地服务验收通过数量']}/{summary['本地服务验收总数']}",
            f"- 统一指令速查卡：{summary['统一指令速查卡状态']}，指令数量 {summary['速查卡指令数量']}",
            f"- 灰度放行门禁：{summary['灰度放行门禁状态']}，失败项 {summary['灰度放行失败数量']}",
            f"- Webhook触发：{summary['是否触发Webhook']}",
            f"- n8n触发：{summary['是否触发n8n']}",
            "",
            "## 安全边界",
            "",
            "- 当前只允许凭据隔离检查、路径模板检查、只读回环预演和沙箱回滚演练。",
            "- 真实凭据写入、真实企业微信发送、Webhook触发、n8n触发均保持关闭。",
            "- OpenClaw只作为边缘消息代理，不写业务判断。",
        ]
    ) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据"
    output_dir = data_root / "07状态摘要"
    quick_card_refresh = run_local_script(root / "02脚本" / "生成企业微信统一指令使用速查卡.py")
    local_service_verify = run_local_script(root / "02脚本" / "验证企业微信统一指令本地服务入口.py")
    gate_report = load_json(data_root / "06沙箱回环门禁" / "企业微信沙箱回环门禁报告_最新.json", {})
    credential_report = load_json(data_root / "01接入检查" / "企业微信凭据隔离检查_最新.json", {})
    disabled_report = load_json(data_root / "06沙箱回环门禁" / "企业微信真实发送禁用态检查_最新.json", {})
    route_report = load_json(data_root / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json", {})
    local_call_report = load_json(data_root / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json", {})
    gray_gate_report = load_json(data_root / "10统一指令灰度放行门禁" / "wecom-unified-command-gray-gate-最新.json", {})
    quick_card_report = load_json(data_root / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json", {})
    local_service_verify_data = {}
    service_logs = sorted(root.glob("04日志/wecom-unified-command-local-service-verify-*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if service_logs:
        local_service_verify_data = load_json(service_logs[0], {})

    scripts = gate_report.get("脚本执行", [])
    failed_scripts = [item for item in scripts if item.get("退出码") != 0]
    high_risk = int(credential_report.get("高风险发现数量", 0) or 0)
    disabled_ok = disabled_report.get("执行器状态") == "禁用态" and disabled_report.get("是否企业微信真实发送") is False
    webhook_off = disabled_report.get("是否触发Webhook") is False
    n8n_off = disabled_report.get("是否触发n8n") is False
    route_summary = route_report.get("汇总", {})
    route_real_action_count = int(route_summary.get("真实动作数量", 1))
    route_ok = route_summary.get("状态") == "healthy" and route_real_action_count == 0
    local_call_summary = local_call_report.get("汇总", {})
    local_call_real_action_count = int(local_call_summary.get("真实动作数量", 1))
    local_call_ok = (
        local_call_summary.get("状态") == "healthy"
        and local_call_summary.get("样例数量") == local_call_summary.get("调用成功数量")
        and int(local_call_summary.get("样例数量", 0) or 0) >= 6
        and local_call_real_action_count == 0
    )
    gray_gate_summary = gray_gate_report.get("汇总", {})
    gray_gate_ok = gray_gate_summary.get("门禁状态") == "pass" and int(gray_gate_summary.get("失败数量", 1) or 0) == 0
    quick_card_ok = quick_card_refresh.get("退出码") == 0 and quick_card_report.get("总体状态") == "healthy" and int(quick_card_report.get("指令数量", 0) or 0) >= 7
    service_summary = local_service_verify_data.get("汇总", {})
    local_service_ok = local_service_verify.get("退出码") == 0 and service_summary.get("失败") == 0 and int(service_summary.get("通过", 0) or 0) >= 10
    local_system_ok = not failed_scripts and high_risk == 0 and disabled_ok and webhook_off and n8n_off and route_ok and local_call_ok and quick_card_ok and local_service_ok
    status = "healthy" if local_system_ok else "degraded"

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-assistant-system-status-summary",
        "所属系统": "02杰哥扩展系统/06企业微信助手系统",
        "汇总": {
            "状态": status,
            "沙箱脚本数量": len(scripts),
            "沙箱脚本失败数": len(failed_scripts),
            "凭据扫描文件数": credential_report.get("扫描文件数", 0),
            "凭据提示发现数": credential_report.get("发现数量", 0),
            "凭据高风险发现数": high_risk,
            "真实发送状态": disabled_report.get("执行器状态", "未知"),
            "统一指令路由状态": route_summary.get("状态", "unknown"),
            "路由样例数量": route_summary.get("样例数量", 0),
            "路由命中期望数量": route_summary.get("命中期望数量", 0),
            "路由真实动作数量": route_summary.get("真实动作数量", 0),
            "统一指令本地调用状态": local_call_summary.get("状态", "unknown"),
            "本地调用样例数量": local_call_summary.get("样例数量", 0),
            "本地调用成功数量": local_call_summary.get("调用成功数量", 0),
            "本地调用真实动作数量": local_call_summary.get("真实动作数量", 0),
            "统一指令本地服务状态": "healthy" if local_service_ok else "degraded",
            "本地服务验收通过数量": service_summary.get("通过", 0),
            "本地服务验收失败数量": service_summary.get("失败", 0),
            "本地服务验收总数": int(service_summary.get("通过", 0) or 0) + int(service_summary.get("失败", 0) or 0),
            "统一指令速查卡状态": quick_card_report.get("总体状态", "unknown"),
            "速查卡指令数量": quick_card_report.get("指令数量", 0),
            "速查卡刷新退出码": quick_card_refresh.get("退出码"),
            "灰度放行门禁状态": gray_gate_summary.get("门禁状态", "unknown"),
            "灰度放行结论": gray_gate_summary.get("放行结论", ""),
            "灰度放行失败数量": gray_gate_summary.get("失败数量", 0),
            "灰度放行是否影响本地健康": False,
            "最大首轮真实消息数": gray_gate_summary.get("最大首轮真实消息数", 5),
            "是否企业微信真实发送": disabled_report.get("是否企业微信真实发送"),
            "是否触发Webhook": disabled_report.get("是否触发Webhook"),
            "是否触发n8n": disabled_report.get("是否触发n8n"),
        },
        "沙箱门禁报告": str(data_root / "06沙箱回环门禁" / "企业微信沙箱回环门禁报告_最新.json"),
        "凭据隔离报告": str(data_root / "01接入检查" / "企业微信凭据隔离检查_最新.json"),
        "真实发送禁用态报告": str(data_root / "06沙箱回环门禁" / "企业微信真实发送禁用态检查_最新.json"),
        "统一指令路由预演报告": str(data_root / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"),
        "统一指令本地调用预演报告": str(data_root / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"),
        "统一指令本地服务验收": local_service_verify,
        "统一指令灰度放行门禁报告": str(data_root / "10统一指令灰度放行门禁" / "wecom-unified-command-gray-gate-最新.json"),
        "统一指令使用速查卡报告": str(data_root / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json"),
        "统一指令使用速查卡刷新": quick_card_refresh,
        "安全边界": {
            "写入真实凭据": False,
            "企业微信真实发送": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写旧系统": False,
            "接入税收": False,
            "交易接口": False,
        },
    }

    latest_json = output_dir / "wecom-assistant-system-status-summary-最新.json"
    output_json = latest_json
    latest_md = output_dir / "企业微信助手系统状态摘要_最新.md"
    output_md = latest_md
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
