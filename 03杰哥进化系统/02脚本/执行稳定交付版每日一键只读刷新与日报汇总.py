# -*- coding: utf-8 -*-
"""执行稳定交付版每日一键只读刷新与日报汇总。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "86稳定交付版每日一键只读刷新与日报汇总包"

PLAN_JSON = DATA_DIR / "稳定版每日一键只读刷新计划_最新.json"
RESULT_JSON = DATA_DIR / "稳定版每日一键只读刷新结果_最新.json"
RESULT_MD = DATA_DIR / "稳定版每日一键只读刷新结果_最新.md"

SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
DAILY_REPORT_JSON = EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定版每日运行日报_最新.json"
THREE_DAY_JSON = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json"


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
        timeout=360,
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
        f"| {item['id']} | {item['名称']} | {item['类别']} | {'pass' if item['通过'] else 'blocked'} | {item['returncode']} |"
        for item in report["任务结果"]
    ]
    return "\n".join(
        [
            "# 稳定版每日一键只读刷新结果",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            f"- 稳定运行状态：{report['汇总摘要']['稳定运行状态']}",
            f"- 三日达标：{report['汇总摘要']['三日达标']}",
            "",
            "| ID | 任务 | 类别 | 结果 | 返回码 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    plan = read_json(PLAN_JSON)
    results = [run_task(task) for task in plan.get("任务", [])]
    passed = sum(1 for item in results if item["通过"])
    snapshot = read_json(SNAPSHOT_JSON)
    daily = read_json(DAILY_REPORT_JSON)
    three_day = read_json(THREE_DAY_JSON)
    report = {
        "名称": "稳定版每日一键只读刷新结果",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed == len(results) else "blocked",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "任务结果": results,
        "汇总摘要": {
            "总巡检状态": snapshot.get("总体状态"),
            "总巡检通过": snapshot.get("汇总", {}).get("通过"),
            "总巡检总数": snapshot.get("汇总", {}).get("总数"),
            "稳定运行状态": daily.get("稳定版运行状态"),
            "今日结论": daily.get("今日结论"),
            "三日达标": three_day.get("三日达标"),
            "仍缺自然日样本": three_day.get("仍缺自然日样本数"),
            "下一自然日最早采集日期": three_day.get("下一自然日最早采集日期"),
        },
        "安全边界": plan.get("安全边界", {}),
    }
    write_json(RESULT_JSON, report)
    write_text(RESULT_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "稳定运行状态": daily.get("稳定版运行状态"), "输出": str(RESULT_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
