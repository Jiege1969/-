# -*- coding: utf-8 -*-
"""
名称：执行当前低风险自动推进队列.py
作用：按阶段汇报不中断策略连续复测公网回调、可信IP、非交易总闸门和股票交付使用版验收。
触发方式：python 执行当前低风险自动推进队列.py
依赖：查看股票公网回调状态.ps1；执行企业微信可信IP阻断自动复测队列.py；验证股票系统只分析不交易总闸门.py；验证股票系统交付使用版总验收.py。
所属系统：00杰哥系统总管
输出：00杰哥系统总管/03数据/运行状态/当前低风险自动推进队列_最新.md/json
安全边界：不启动旧n8n；不启动旧容器；不调用券商接口；不自动交易；不下单；企业微信只走既有可信IP受控复测队列。
标识：current-low-risk-auto-advance-queue
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
OUT_DIR = MANAGER / "03数据" / "运行状态"

PUBLIC_STATUS = STOCK / "02脚本" / "查看股票公网回调状态.ps1"
IP_QUEUE = MANAGER / "02脚本" / "执行企业微信可信IP阻断自动复测队列.py"
NON_TRADE_GATE = MANAGER / "02脚本" / "验证股票系统只分析不交易总闸门.py"
DELIVERY_ACCEPTANCE = STOCK / "02脚本" / "验证股票系统交付使用版总验收.py"

IP_QUEUE_JSON = OUT_DIR / "企业微信可信IP阻断自动复测队列_最新.json"
NON_TRADE_JSON = OUT_DIR / "股票系统只分析不交易总闸门验收_最新.json"
ACCEPTANCE_DIR = STOCK / "04日志" / "股票系统交付使用版总验收"


def run_step(name: str, cmd: list[str]) -> dict[str, Any]:
    start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "名称": name,
        "命令": cmd,
        "开始时间": start,
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "返回码": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))


def latest_acceptance() -> dict[str, Any]:
    latest = ACCEPTANCE_DIR / "stock-delivery-total-acceptance-最新.json"
    if latest.exists():
        data = read_json(latest)
        data["_path"] = str(latest)
        return data
    return {}


def parse_public(stdout: str) -> dict[str, Any]:
    try:
        return json.loads(stdout)
    except Exception:
        return {"raw": stdout}


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "当前低风险自动推进队列_最新.json"
    md_path = OUT_DIR / "当前低风险自动推进队列_最新.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    ip = report.get("企业微信可信IP复测", {})
    public = report.get("公网回调状态", {})
    non_trade = report.get("非交易总闸门", {})
    acceptance = report.get("交付使用版总验收", {})
    lines = [
        "# 当前低风险自动推进队列",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 公网回调状态：{public.get('status')}",
        f"- 公网入口：`{public.get('public_bot_url', '')}`",
        f"- 企业微信真实发送成功：{(ip.get('最近真实复测') or {}).get('真实发送成功')}",
        f"- 当前需放行 IP：`{ip.get('当前需放行IP', '')}`",
        f"- 目标应用：`{(ip.get('目标应用档案') or {}).get('名称', '')}`",
        f"- 非交易总闸门：{non_trade.get('通过数量')}/{non_trade.get('通过数量', 0) + non_trade.get('失败数量', 0)}",
        f"- 交付使用版总验收：{acceptance.get('通过')}/{acceptance.get('通过', 0) + acceptance.get('失败', 0)}",
        "",
        "## 本轮步骤",
        "",
    ]
    for step in report.get("步骤", []):
        lines.append(f"- {step['名称']}：返回码 {step['返回码']}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 未启动旧n8n。",
        "- 未启动旧智能体容器。",
        "- 未调用券商接口。",
        "- 未自动交易。",
        "- 未下单。",
        "- 企业微信只走既有可信IP受控复测队列。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["输出"] = {"json": str(json_path), "markdown": str(md_path)}
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    steps = [
        run_step("公网回调健康复测", ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(PUBLIC_STATUS)]),
        run_step("企业微信可信IP阻断自动复测队列", [sys.executable, str(IP_QUEUE)]),
        run_step("股票系统只分析不交易总闸门", [sys.executable, str(NON_TRADE_GATE)]),
        run_step("股票系统交付使用版总验收", [sys.executable, str(DELIVERY_ACCEPTANCE)]),
    ]
    public = parse_public(steps[0].get("stdout", ""))
    ip = read_json(IP_QUEUE_JSON)
    non_trade = read_json(NON_TRADE_JSON)
    acceptance = latest_acceptance()

    public_ok = public.get("status") == "ready" and public.get("public_callback_ok") is True
    non_trade_ok = non_trade.get("当前结论") == "通过" and non_trade.get("失败数量") == 0
    acceptance_ok = acceptance.get("失败") == 0 and acceptance.get("通过", 0) >= 22
    ip_blocked = (ip.get("最近真实复测") or {}).get("企业微信errcode") == 60020
    ip_success = (ip.get("最近真实复测") or {}).get("真实发送成功") is True

    if public_ok and non_trade_ok and acceptance_ok and (ip_success or ip_blocked):
        conclusion = "继续推进可用：公网机器人、非交易闸门和交付验收通过；企业微信主动发送若仍60020则进入下一轮自动复测"
    else:
        conclusion = "存在需处理项：查看步骤返回码和各验收摘要"

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": conclusion,
        "公网回调状态": public,
        "企业微信可信IP复测": ip,
        "非交易总闸门": non_trade,
        "交付使用版总验收": acceptance,
        "步骤": steps,
        "安全边界": {
            "启动旧n8n": False,
            "启动旧容器": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
        },
    }
    write_outputs(report)
    print(json.dumps({
        "状态": "完成",
        "当前结论": conclusion,
        "公网回调状态": public.get("status"),
        "真实发送成功": (ip.get("最近真实复测") or {}).get("真实发送成功"),
        "当前需放行IP": ip.get("当前需放行IP"),
        "目标应用": (ip.get("目标应用档案") or {}).get("名称"),
        "非交易总闸门": {"通过": non_trade.get("通过数量"), "失败": non_trade.get("失败数量")},
        "交付使用版总验收": {"通过": acceptance.get("通过"), "失败": acceptance.get("失败")},
        "输出": report["输出"],
    }, ensure_ascii=False))
    return 0 if public_ok and non_trade_ok and acceptance_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
