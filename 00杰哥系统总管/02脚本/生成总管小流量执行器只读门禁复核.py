# -*- coding: utf-8 -*-
"""
名称：生成总管小流量执行器只读门禁复核.py
作用：汇总首批执行器就绪总表、小流量只读执行方案、执行前快照和执行后观测模板验收，形成总管只读门禁复核报告。
触发方式：python 生成总管小流量执行器只读门禁复核.py
所属系统：00杰哥系统总管
安全边界：只运行既有只读门禁验收脚本；只写00总管运行状态报告；
不触发执行器；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不重启19300/19302；不调用券商接口；不自动交易。
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
SCRIPT_DIR = MANAGER / "02脚本"
DATA_DIR = MANAGER / "03数据" / "小流量只读执行"
OUT_DIR = MANAGER / "03数据" / "运行状态"

SCRIPTS = [
    ("首批执行器就绪总表验收", SCRIPT_DIR / "验证首批执行器就绪总表.py"),
    ("小流量只读执行方案验收", SCRIPT_DIR / "验证小流量只读执行方案.py"),
    ("小流量只读执行前快照验收", SCRIPT_DIR / "验证小流量只读执行前快照.py"),
    ("小流量只读执行后观测模板验收", SCRIPT_DIR / "验证小流量只读执行后观测模板.py"),
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


def run_script(name: str, script: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=120,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    parsed: dict[str, Any] = {}
    if lines:
        try:
            parsed = json.loads(lines[0])
        except json.JSONDecodeError:
            parsed = {}
    return {
        "名称": name,
        "脚本": str(script),
        "存在": script.exists(),
        "退出码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
        "输出解析": parsed,
    }


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    lines = [
        "# 总管小流量执行器只读门禁复核",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 脚本通过：{summary['脚本通过数量']}/{summary['脚本总数']}",
        f"- 执行器数量：{summary['执行器数量']}",
        f"- 就绪但冻结数量：{summary['就绪但冻结数量']}",
        f"- 真实动作数量：{summary['真实动作数量']}",
        f"- 前快照失败数：{summary['执行前快照失败数']}",
        f"- 后观测模板项目数：{summary['后观测项目数量']}",
        "",
        "## 脚本执行",
        "",
    ]
    for item in report["脚本执行"]:
        status = "通过" if item["退出码"] == 0 else "失败"
        lines.append(f"- {item['名称']}：{status}，退出码 {item['退出码']}")
    lines.extend(["", "## 安全边界", ""])
    lines.extend([
        "- 本轮不触发执行器、不触发n8n、不发送企业微信。",
        "- 本轮不写正式库、不写旧系统、不重启19300/19302。",
        "- 本轮不调用券商接口、不自动交易。",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    runs = [run_script(name, script) for name, script in SCRIPTS]
    readiness = load_json(DATA_DIR / "首批执行器就绪总表_最新.json", {})
    plan = load_json(DATA_DIR / "小流量只读执行方案_最新.json", {})
    snapshot = load_json(DATA_DIR / "小流量只读执行前快照_最新.json", {})
    observation = load_json(DATA_DIR / "小流量只读执行后观测模板_最新.json", {})

    readiness_summary = readiness.get("汇总", {})
    plan_switches = plan.get("默认开关", {})
    snapshot_switches = snapshot.get("真实动作关闭开关", {})
    observation_state = observation.get("默认状态", {})
    passed_runs = [item for item in runs if item["退出码"] == 0]
    failed_runs = [item for item in runs if item["退出码"] != 0]
    real_action_count = int(readiness_summary.get("真实动作数量", 99) or 0)
    switches_closed = all(value is False for value in plan_switches.values()) and all(value is False for value in snapshot_switches.values())
    observation_closed = all(value is False for value in observation_state.values())
    all_ok = (
        not failed_runs
        and readiness_summary.get("执行器数量") == 3
        and readiness_summary.get("就绪但冻结数量") == 3
        and real_action_count == 0
        and snapshot.get("汇总", {}).get("失败") == 0
        and len(observation.get("观测项目", [])) >= 6
        and switches_closed
        and observation_closed
    )

    risks = []
    if failed_runs:
        risks.append("存在只读门禁脚本失败：" + "、".join(item["名称"] for item in failed_runs))
    if real_action_count != 0:
        risks.append("执行器就绪总表出现真实动作数量非零。")
    if not switches_closed:
        risks.append("只读方案或执行前快照存在未关闭开关。")
    if not observation_closed:
        risks.append("执行后观测模板默认状态存在未关闭项。")
    if not risks:
        risks.append("未发现阻断；本轮只做门禁复核，不触发执行器。")

    report = {
        "名称": "总管小流量执行器只读门禁复核",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if all_ok else "失败",
        "汇总": {
            "脚本总数": len(runs),
            "脚本通过数量": len(passed_runs),
            "脚本失败数量": len(failed_runs),
            "执行器数量": readiness_summary.get("执行器数量", 0),
            "就绪但冻结数量": readiness_summary.get("就绪但冻结数量", 0),
            "真实动作数量": readiness_summary.get("真实动作数量", 0),
            "执行批次数量": len(plan.get("执行批次", [])),
            "执行前快照失败数": snapshot.get("汇总", {}).get("失败", 0),
            "后观测项目数量": len(observation.get("观测项目", [])),
            "计划开关全部关闭": switches_closed,
            "后观测默认状态全部关闭": observation_closed,
        },
        "脚本执行": runs,
        "引用产物": {
            "首批执行器就绪总表": str(DATA_DIR / "首批执行器就绪总表_最新.json"),
            "小流量只读执行方案": str(DATA_DIR / "小流量只读执行方案_最新.json"),
            "小流量只读执行前快照": str(DATA_DIR / "小流量只读执行前快照_最新.json"),
            "小流量只读执行后观测模板": str(DATA_DIR / "小流量只读执行后观测模板_最新.json"),
        },
        "风险与缺口": risks,
        "安全边界": {
            "触发执行器": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "写旧系统": False,
            "重启19300": False,
            "重启19302": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "总管小流量执行器只读门禁复核_最新.json"
    latest_md = OUT_DIR / "总管小流量执行器只读门禁复核_最新.md"
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
