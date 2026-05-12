# -*- coding: utf-8 -*-
"""执行稳定交付版首日只读复验并回收问题。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "82稳定交付版首日复验执行与问题回收包"

PLAN_JSON = DATA_DIR / "稳定版首日只读复验执行计划_最新.json"
RESULT_JSON = DATA_DIR / "稳定版首日只读复验执行结果_最新.json"
RESULT_MD = DATA_DIR / "稳定版首日只读复验执行结果_最新.md"
LEDGER_JSON = DATA_DIR / "稳定版首日问题回收台账_最新.json"
LEDGER_MD = DATA_DIR / "稳定版首日问题回收台账_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_script(path_text: str) -> dict[str, Any]:
    if not path_text:
        return {"执行": False, "通过": True, "returncode": 0, "stdout": "", "stderr": "", "脚本": ""}
    path = Path(path_text)
    if not path.exists():
        return {"执行": False, "通过": False, "returncode": None, "stdout": "", "stderr": "script missing", "脚本": path_text}
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(path.parent.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
        check=False,
    )
    return {
        "执行": True,
        "通过": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip()[-2000:],
        "stderr": result.stderr.strip()[-2000:],
        "脚本": path_text,
    }


def issue_from_result(task: dict[str, Any], stage: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "来源任务": f"{task['id']} {task['名称']} {stage}",
        "问题级别": task.get("失败级别", "P2"),
        "现象": f"{stage} 未通过",
        "复现脚本": result.get("脚本", ""),
        "标准输出摘要": result.get("stdout", ""),
        "错误输出摘要": result.get("stderr", ""),
        "是否触碰红线": False,
        "是否需总管确认": task.get("失败级别") == "P0",
        "建议动作": "先只读复现并定位失败项；如涉及服务重载、红线或正式规则，登记需总管确认。",
    }


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['名称']} | {'pass' if item['通过'] else 'blocked'} | {item['失败阶段']} |"
        for item in report["任务结果"]
    ]
    issues = report["问题项"]
    issue_rows = [
        f"| {idx} | {item['来源任务']} | {item['问题级别']} | {item['是否需总管确认']} |"
        for idx, item in enumerate(issues, start=1)
    ]
    return "\n".join(
        [
            "# 稳定版首日只读复验执行结果",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            f"- 问题数：{len(issues)}",
            "",
            "| ID | 任务 | 结果 | 失败阶段 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 问题项",
            "",
            "| 序号 | 来源 | 级别 | 需总管确认 |",
            "| --- | --- | --- | --- |",
            *(issue_rows if issue_rows else ["| - | 无 | - | - |"]),
            "",
        ]
    )


def build_ledger_md(ledger: dict[str, Any]) -> str:
    rows = [
        f"| {idx} | {item['来源任务']} | {item['问题级别']} | {item['是否需总管确认']} | {item['建议动作']} |"
        for idx, item in enumerate(ledger["问题项"], start=1)
    ]
    return "\n".join(
        [
            "# 稳定版首日问题回收台账",
            "",
            f"- 生成时间：{ledger['生成时间']}",
            f"- 问题数：{len(ledger['问题项'])}",
            "",
            "| 序号 | 来源 | 级别 | 需总管确认 | 建议动作 |",
            "| --- | --- | --- | --- | --- |",
            *(rows if rows else ["| - | 无 | - | - | - |"]),
            "",
        ]
    )


def main() -> int:
    plan = read_json(PLAN_JSON)
    task_results = []
    issues = []

    for task in plan.get("任务", []):
        first = run_script(task.get("脚本", ""))
        second = run_script(task.get("验证脚本", ""))
        passed = first["通过"] and second["通过"]
        failed_stage = ""
        if not first["通过"]:
            failed_stage = "执行脚本"
            issues.append(issue_from_result(task, failed_stage, first))
        if not second["通过"]:
            failed_stage = "验证脚本" if not failed_stage else f"{failed_stage}+验证脚本"
            issues.append(issue_from_result(task, "验证脚本", second))
        task_results.append(
            {
                "id": task["id"],
                "名称": task["名称"],
                "类别": task["类别"],
                "通过": passed,
                "失败阶段": failed_stage,
                "执行结果": first,
                "验证结果": second,
            }
        )

    passed_count = sum(1 for item in task_results if item["通过"])
    report = {
        "名称": "稳定版首日只读复验执行结果",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed_count == len(task_results) else "blocked",
        "汇总": {"总数": len(task_results), "通过": passed_count, "失败": len(task_results) - passed_count},
        "任务结果": task_results,
        "问题项": issues,
        "安全边界": plan.get("安全边界", {}),
    }
    ledger = {
        "名称": "稳定版首日问题回收台账",
        "生成时间": report["生成时间"],
        "问题项": issues,
        "安全边界": plan.get("安全边界", {}),
    }
    write_json(RESULT_JSON, report)
    write_text(RESULT_MD, build_md(report))
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed_count, "失败": len(task_results) - passed_count, "问题数": len(issues), "输出": str(RESULT_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
