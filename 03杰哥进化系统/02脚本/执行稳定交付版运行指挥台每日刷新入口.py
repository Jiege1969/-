# -*- coding: utf-8 -*-
"""执行稳定交付版运行指挥台每日刷新入口。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "88稳定交付版运行指挥台每日刷新入口包"

PLAN_JSON = DATA_DIR / "稳定版运行指挥台每日刷新入口计划_最新.json"
RESULT_JSON = DATA_DIR / "稳定版运行指挥台每日刷新入口执行结果_最新.json"
RESULT_MD = DATA_DIR / "稳定版运行指挥台每日刷新入口执行结果_最新.md"
DASHBOARD_JSON = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定版运行指挥台_最新.json"
FEEDBACK_RESULT_JSON = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账结果_最新.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    script = Path(task["脚本"])
    if not script.exists():
        return {**task, "通过": False, "returncode": None, "stdout": "", "stderr": "script missing"}
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(EVOLUTION_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        check=False,
    )
    return {
        **task,
        "通过": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip()[-2500:],
        "stderr": result.stderr.strip()[-2500:],
    }


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['名称']} | {'pass' if item['通过'] else 'blocked'} | {item['returncode']} |"
        for item in report["任务结果"]
    ]
    return "\n".join(
        [
            "# 稳定版运行指挥台每日刷新入口执行结果",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            f"- 运行灯号：{report['指挥台摘要']['运行灯号']}",
            f"- 今日结论：{report['指挥台摘要']['今日结论']}",
            "",
            "| ID | 任务 | 结果 | 返回码 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    plan = read_json(PLAN_JSON)
    results = [run_task(task) for task in plan.get("任务", [])]
    passed = sum(1 for item in results if item["通过"])
    dashboard = read_json(DASHBOARD_JSON)
    feedback = read_json(FEEDBACK_RESULT_JSON)
    report = {
        "名称": "稳定版运行指挥台每日刷新入口执行结果",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed == len(results) else "blocked",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "任务结果": results,
        "指挥台摘要": {
            "运行灯号": dashboard.get("运行灯号"),
            "今日结论": dashboard.get("今日结论"),
            "三日达标": dashboard.get("三日稳定", {}).get("达标"),
            "仍缺样本数": dashboard.get("三日稳定", {}).get("仍缺样本数"),
            "每日刷新失败": dashboard.get("每日刷新", {}).get("失败"),
            "总巡检失败": dashboard.get("总巡检", {}).get("失败"),
            "总回归失败": dashboard.get("总回归", {}).get("失败"),
            "反馈扫描文件数": feedback.get("指标", {}).get("扫描文件数"),
            "反馈接收数": feedback.get("指标", {}).get("接收数"),
            "反馈拒收数": feedback.get("指标", {}).get("拒收数"),
            "反馈需总管确认数": feedback.get("指标", {}).get("需总管确认数"),
        },
        "安全边界": plan.get("安全边界", {}),
    }
    write_json(RESULT_JSON, report)
    write_text(RESULT_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "运行灯号": dashboard.get("运行灯号"), "输出": str(RESULT_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
