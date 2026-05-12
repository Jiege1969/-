# -*- coding: utf-8 -*-
"""
名称：执行持续施工总控队列.py
作用：持续推进当前计划队列，统一执行低风险复测、计划完成度验收、旧容器引用检查、一键接续包刷新和验收。
触发方式：python 执行持续施工总控队列.py
依赖：执行当前低风险自动推进队列.py；验证智能体三服务计划完成度.py；生成旧容器引用关系检查报告.py；生成一键接续施工包.py；验证一键接续施工包.py。
所属系统：00杰哥系统总管
输出：00杰哥系统总管/03数据/运行状态/持续施工总控队列_最新.md/json
安全边界：不启动旧n8n；不启动旧容器；不开放旧端口公网；不调用券商接口；不自动交易；不下单；企业微信只走既有受控复测队列。
标识：continuous-construction-control-queue
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
SCRIPTS = MANAGER / "02脚本"
OUT_DIR = MANAGER / "03数据" / "运行状态"
RESUME_LOG_DIR = MANAGER / "04日志" / "开工上下文"

LOW_RISK_SCRIPT = SCRIPTS / "执行当前低风险自动推进队列.py"
PLAN_ACCEPT_SCRIPT = SCRIPTS / "验证智能体三服务计划完成度.py"
OLD_CONTAINER_SCRIPT = SCRIPTS / "生成旧容器引用关系检查报告.py"
RESUME_BUILD_SCRIPT = SCRIPTS / "生成一键接续施工包.py"
RESUME_VERIFY_SCRIPT = SCRIPTS / "验证一键接续施工包.py"

LOW_RISK_JSON = OUT_DIR / "当前低风险自动推进队列_最新.json"
PLAN_ACCEPT_JSON = OUT_DIR / "智能体三服务计划完成度总验收_最新.json"
OLD_CONTAINER_JSON = OUT_DIR / "旧容器引用关系检查报告_最新.json"
RESUME_VERIFY_JSON = RESUME_LOG_DIR / "one-click-resume-package-verify-最新.json"


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
        "开始时间": start,
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "命令": cmd,
        "返回码": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))


def parse_stdout_json(step: dict[str, Any]) -> dict[str, Any]:
    text = step.get("stdout", "")
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {}


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "持续施工总控队列_最新.json"
    md_path = OUT_DIR / "持续施工总控队列_最新.md"

    low = report.get("低风险自动推进摘要", {})
    plan = report.get("计划完成度摘要", {})
    old = report.get("旧容器引用摘要", {})
    resume = report.get("一键接续包摘要", {})

    lines = [
        "# 持续施工总控队列",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 公网机器人：{low.get('公网状态')}",
        f"- 企业微信真实发送成功：{low.get('真实发送成功')}",
        f"- 企业微信错误码：{low.get('errcode')}",
        f"- 当前需放行 IP：`{low.get('当前需放行IP', '')}`",
        f"- 目标应用：`{low.get('目标应用', '')}`",
        f"- 非交易总闸门：{low.get('非交易通过')}/{low.get('非交易通过', 0) + low.get('非交易失败', 0)}",
        f"- 交付使用版总验收：{low.get('交付通过')}/{low.get('交付通过', 0) + low.get('交付失败', 0)}",
        f"- 计划完成度：{plan.get('通过数量')}/{plan.get('通过数量', 0) + plan.get('失败数量', 0)}",
        f"- 旧容器引用：旧容器 {old.get('旧容器数量')}，存在引用 {old.get('存在引用')}，退役候选 {old.get('无引用退役候选')}",
        f"- 一键接续包验收：{resume.get('通过')}/{resume.get('通过', 0) + resume.get('失败', 0)}",
        "",
        "## 本轮步骤",
        "",
    ]
    for step in report.get("步骤", []):
        lines.append(f"- {step['名称']}：返回码 {step['返回码']}")
    lines.extend([
        "",
        "## 继续策略",
        "",
        "- 企业微信 `60020` 只登记并等待下一轮自动复测，不作为本地停工点。",
        "- 不启动旧 n8n，不启动旧容器，不开放旧端口公网。",
        "- 不调用券商接口，不自动交易，不下单，不配置资金账户。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["输出"] = {"json": str(json_path), "markdown": str(md_path)}
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    steps = [
        run_step("统一低风险自动推进队列", [sys.executable, str(LOW_RISK_SCRIPT)]),
        run_step("智能体三服务计划完成度总验收", [sys.executable, str(PLAN_ACCEPT_SCRIPT)]),
        run_step("旧容器引用关系检查", [sys.executable, str(OLD_CONTAINER_SCRIPT)]),
        run_step("生成一键接续施工包", [sys.executable, str(RESUME_BUILD_SCRIPT)]),
        run_step("验证一键接续施工包", [sys.executable, str(RESUME_VERIFY_SCRIPT)]),
    ]

    low_json = read_json(LOW_RISK_JSON)
    plan_json = read_json(PLAN_ACCEPT_JSON)
    old_json = read_json(OLD_CONTAINER_JSON)
    resume_log = read_json(RESUME_VERIFY_JSON)
    resume_stdout = resume_log or parse_stdout_json(steps[-1])

    ip_probe = (low_json.get("企业微信可信IP复测") or {}).get("最近真实复测") or {}
    low_summary = {
        "公网状态": (low_json.get("公网回调状态") or {}).get("status"),
        "真实发送成功": ip_probe.get("真实发送成功"),
        "errcode": ip_probe.get("企业微信errcode"),
        "当前需放行IP": (low_json.get("企业微信可信IP复测") or {}).get("当前需放行IP"),
        "目标应用": ((low_json.get("企业微信可信IP复测") or {}).get("目标应用档案") or {}).get("名称"),
        "非交易通过": (low_json.get("非交易总闸门") or {}).get("通过数量", 0),
        "非交易失败": (low_json.get("非交易总闸门") or {}).get("失败数量", 0),
        "交付通过": (low_json.get("交付使用版总验收") or {}).get("通过", 0),
        "交付失败": (low_json.get("交付使用版总验收") or {}).get("失败", 0),
    }
    plan_summary = {
        "本地计划通过": plan_json.get("本地计划通过"),
        "通过数量": plan_json.get("通过数量", 0),
        "失败数量": plan_json.get("失败数量", 0),
        "外部待生效数量": plan_json.get("外部待生效数量", 0),
    }
    old_summary = old_json.get("汇总") or {}
    resume_summary = {
        "通过": resume_stdout.get("通过", 0),
        "失败": resume_stdout.get("失败", 0),
        "输出": resume_stdout.get("输出") or resume_stdout.get("输出文件", ""),
    }

    local_ok = (
        low_summary["公网状态"] == "ready"
        and low_summary["非交易失败"] == 0
        and low_summary["交付失败"] == 0
        and plan_summary["失败数量"] == 0
        and resume_summary["失败"] == 0
        and all(step["返回码"] == 0 or step["名称"] == "统一低风险自动推进队列" for step in steps)
    )
    if local_ok and low_summary.get("errcode") == 60020:
        conclusion = "持续推进正常：本地队列通过，企业微信主动发送仍为可信IP外部待生效"
    elif local_ok:
        conclusion = "持续推进正常：本地队列通过"
    else:
        conclusion = "持续推进存在本地失败项，需查看步骤返回码"

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": conclusion,
        "低风险自动推进摘要": low_summary,
        "计划完成度摘要": plan_summary,
        "旧容器引用摘要": old_summary,
        "一键接续包摘要": resume_summary,
        "步骤": steps,
        "安全边界": {
            "启动旧n8n": False,
            "启动旧容器": False,
            "开放旧端口公网": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
        },
    }
    write_outputs(report)
    print(json.dumps({
        "状态": "完成",
        "当前结论": conclusion,
        "公网机器人": low_summary.get("公网状态"),
        "真实发送成功": low_summary.get("真实发送成功"),
        "errcode": low_summary.get("errcode"),
        "当前需放行IP": low_summary.get("当前需放行IP"),
        "目标应用": low_summary.get("目标应用"),
        "非交易总闸门": {"通过": low_summary.get("非交易通过"), "失败": low_summary.get("非交易失败")},
        "交付使用版总验收": {"通过": low_summary.get("交付通过"), "失败": low_summary.get("交付失败")},
        "计划完成度": {"通过": plan_summary.get("通过数量"), "失败": plan_summary.get("失败数量")},
        "一键接续包": {"通过": resume_summary.get("通过"), "失败": resume_summary.get("失败")},
        "输出": report["输出"],
    }, ensure_ascii=False))
    return 0 if local_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
