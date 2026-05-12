# -*- coding: utf-8 -*-
"""
名称：生成进化系统复盘材料状态基线.py
作用：汇总进化系统状态摘要、复盘报告和巡检经验卡片候选模板，形成总管侧复盘材料状态基线。
触发方式：python 生成进化系统复盘材料状态基线.py
所属系统：00杰哥系统总管 / 03杰哥进化系统
安全边界：只运行进化系统本地状态与候选材料脚本；只写00总管运行状态报告；
不生成正式经验卡片；不自动固化规则；不写总纲规则；不删除样本；不触发n8n；不发送企业微信；不写旧系统；不交易。
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
EVOLUTION = ROOT / "03杰哥进化系统"
SCRIPT_DIR = EVOLUTION / "02脚本"
DATA_DIR = EVOLUTION / "03数据"
OUT_DIR = MANAGER / "03数据" / "运行状态"

SCRIPTS = [
    ("进化系统状态摘要验收", SCRIPT_DIR / "验证进化系统状态摘要.py"),
    ("进化复盘报告生成", SCRIPT_DIR / "生成进化复盘报告.py"),
    ("巡检经验候选模板验收", SCRIPT_DIR / "验证巡检结果经验卡片候选模板.py"),
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
    parsed: dict[str, Any] = {}
    first_line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
    if first_line:
        try:
            parsed = json.loads(first_line)
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
        "# 进化系统复盘材料状态基线",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 脚本通过：{summary['脚本通过数量']}/{summary['脚本总数']}",
        f"- 进化系统状态：{summary['进化系统状态']}",
        f"- 经验卡片数量：{summary['经验卡片数量']}",
        f"- 方法资产候选数量：{summary['方法资产候选数量']}",
        f"- 巡检候选数量：{summary['巡检候选数量']}",
        f"- 正式经验卡片数量：{summary['正式经验卡片数量']}",
        f"- 自动固化规则数量：{summary['自动固化规则数量']}",
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
        "- 本轮不生成正式经验卡片、不自动固化规则、不写总纲规则。",
        "- 本轮不删除样本、不清理文件、不触发n8n、不发送企业微信。",
        "- 本轮不写旧系统、不调用券商接口、不自动交易。",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    runs = [run_script(name, script) for name, script in SCRIPTS]
    status_report = load_json(DATA_DIR / "07状态摘要" / "evolution-system-status-summary-最新.json", {})
    review_report = load_json(DATA_DIR / "04通用方法" / "进化复盘报告_最新.json", {})
    suggestion_report = load_json(DATA_DIR / "05进化建议" / "进化建议_最新.json", {})
    candidate_report = load_json(DATA_DIR / "06巡检经验候选" / "巡检结果经验卡片候选模板_最新.json", {})

    status_summary = status_report.get("汇总", {})
    candidate_summary = candidate_report.get("汇总", {})
    status_safety = status_report.get("安全边界", {})
    passed_runs = [item for item in runs if item["退出码"] == 0]
    failed_runs = [item for item in runs if item["退出码"] != 0]
    formal_cards = int(candidate_summary.get("正式经验卡片数量", 99) or 0)
    auto_rules = int(candidate_summary.get("自动固化规则数量", 99) or 0)
    safety_ok = (
        status_safety.get("删除样本") is False
        and status_safety.get("清理文件") is False
        and status_safety.get("触发n8n") is False
        and status_safety.get("发送企业微信") is False
        and status_safety.get("写旧系统") is False
        and formal_cards == 0
        and auto_rules == 0
    )
    all_ok = (
        not failed_runs
        and status_summary.get("状态") == "healthy"
        and int(review_report.get("经验卡片数量", 0) or 0) >= 1
        and int(review_report.get("方法资产候选数量", 0) or 0) >= 1
        and int(candidate_summary.get("候选数量", 0) or 0) >= 5
        and safety_ok
    )

    risks: list[str] = []
    if failed_runs:
        risks.append("存在进化材料脚本失败：" + "、".join(item["名称"] for item in failed_runs))
    if status_summary.get("状态") != "healthy":
        risks.append("进化系统状态摘要不是 healthy。")
    if formal_cards != 0 or auto_rules != 0:
        risks.append("巡检经验候选模板出现正式经验卡片或自动固化规则数量非零。")
    if not risks:
        risks.append("未发现阻断；本轮只形成复盘材料和候选模板，不写总纲规则。")

    report = {
        "名称": "进化系统复盘材料状态基线",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if all_ok else "失败",
        "汇总": {
            "脚本总数": len(runs),
            "脚本通过数量": len(passed_runs),
            "脚本失败数量": len(failed_runs),
            "进化系统状态": status_summary.get("状态", "unknown"),
            "经验卡片数量": review_report.get("经验卡片数量", 0),
            "方法资产候选数量": review_report.get("方法资产候选数量", 0),
            "建议数量": suggestion_report.get("建议数量", 0),
            "巡检候选数量": candidate_summary.get("候选数量", 0),
            "正式经验卡片数量": candidate_summary.get("正式经验卡片数量", 0),
            "自动提炼通用方法数量": candidate_summary.get("自动提炼通用方法数量", 0),
            "自动固化规则数量": candidate_summary.get("自动固化规则数量", 0),
            "删除样本数量": candidate_summary.get("删除样本数量", 0),
            "写旧系统数量": candidate_summary.get("写旧系统数量", 0),
        },
        "脚本执行": runs,
        "引用产物": {
            "进化系统状态摘要": str(DATA_DIR / "07状态摘要" / "evolution-system-status-summary-最新.json"),
            "进化复盘报告": str(DATA_DIR / "04通用方法" / "进化复盘报告_最新.json"),
            "进化建议": str(DATA_DIR / "05进化建议" / "进化建议_最新.json"),
            "巡检经验候选模板": str(DATA_DIR / "06巡检经验候选" / "巡检结果经验卡片候选模板_最新.json"),
        },
        "风险与缺口": risks,
        "安全边界": {
            "生成正式经验卡片": False,
            "自动固化规则": False,
            "写总纲规则": False,
            "删除样本": False,
            "清理文件": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "进化系统复盘材料状态基线_最新.json"
    latest_md = OUT_DIR / "进化系统复盘材料状态基线_最新.md"
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
