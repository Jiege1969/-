# -*- coding: utf-8 -*-
"""
名称：生成个人智能母系统任务队列调度面板.py
作用：读取无人值守任务队列种子，为每个任务调用任务准入闸口，生成当前队列调度状态面板。
触发方式：python 生成个人智能母系统任务队列调度面板.py [--now "YYYY-MM-DD HH:MM:SS"] [--ignore-resource-pressure]
依赖：Python标准库；无人值守任务队列种子；个人智能母系统任务队列调度规则；生成个人智能母系统任务准入报告.py。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统任务队列/task-queue-scheduler-*.json|md；03数据/运行状态/个人智能母系统任务队列调度_最新.json|md。
安全边界：只读队列并写总管状态/日志；不执行任务、不触发执行器、不触发n8n、不发送企业微信、不调用券商接口、不自动交易、不修改业务文件。
标识：personal-ai-task-queue-scheduler；任务队列；准入调度；只读面板。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def run_py(script: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def infer_type(task: dict[str, Any], rules: dict[str, Any]) -> str:
    text = f"{task.get('任务名称') or ''} {task.get('所属模块') or ''} {task.get('执行器标识') or ''}"
    for item in rules.get("任务类型推断", []):
        if item.get("关键词") and item["关键词"] in text:
            return item.get("任务类型") or "L0只读巡检"
    return "L0只读巡检"


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# 个人智能母系统任务队列调度面板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前调度状态：{report.get('当前调度状态')}",
        f"- 队列任务数：{report['汇总']['任务数量']}",
        f"- 允许：{report['汇总']['允许执行']}",
        f"- 降级：{report['汇总']['降级只读']}",
        f"- 延后：{report['汇总']['延后执行']}",
        f"- 需许可：{report['汇总']['需要许可令']}",
        f"- 禁止：{report['汇总']['禁止执行']}",
        "",
        "## 队列",
    ]
    for item in report.get("任务队列", []):
        lines.append(f"- {item['任务编号']} {item['任务名称']}：{item['准入结论']}；{item['队列动作']}")
    lines.extend(["", "## 安全边界"])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", default="", help="用于验收的指定时间，格式 YYYY-MM-DD HH:MM:SS。")
    parser.add_argument("--ignore-resource-pressure", action="store_true", help="仅用于验收，忽略当前资源压力。")
    args = parser.parse_args()

    manager = manager_root()
    rules_path = manager / "01配置" / "个人智能母系统任务队列调度规则.json"
    rules = load_json(rules_path, {})
    seed_script = manager / "02脚本" / "生成无人值守任务队列种子.py"
    admission_script = manager / "02脚本" / "生成个人智能母系统任务准入报告.py"

    seed_run = run_py(seed_script)
    seed_path = manager / "03数据" / "无人值守守护" / "无人值守任务队列种子_最新.json"
    seed = load_json(seed_path, {})
    queue = seed.get("任务队列", [])
    level_map = rules.get("风险等级映射", {})
    action_map = rules.get("队列动作", {})
    scheduled: list[dict[str, Any]] = []
    latest_admission = manager / "03数据" / "运行状态" / "个人智能母系统任务准入_最新.json"

    for task in queue:
        level = level_map.get(str(task.get("风险等级") or ""), str(task.get("风险等级") or "L0只读巡检"))
        task_type = infer_type(task, rules)
        admission_args = [
            "--task", str(task.get("任务名称") or ""),
            "--level", level,
            "--type", task_type,
            "--action", "队列准入判断",
            "--system", str(task.get("所属模块") or "00总管"),
        ]
        if args.now:
            admission_args.extend(["--now", args.now])
        if args.ignore_resource_pressure:
            admission_args.append("--ignore-resource-pressure")
        admission_run = run_py(admission_script, *admission_args)
        admission = load_json(latest_admission, {})
        conclusion = admission.get("准入结论") or "延后执行"
        scheduled.append({
            "任务编号": task.get("任务编号"),
            "任务名称": task.get("任务名称"),
            "所属模块": task.get("所属模块"),
            "权限等级": level,
            "任务类型": task_type,
            "原状态": task.get("当前状态"),
            "准入结论": conclusion,
            "队列动作": action_map.get(conclusion, "保留观察。"),
            "执行器标识": task.get("执行器标识"),
            "是否触发执行器": False,
            "是否触发n8n": False,
            "准入返回码": admission_run.returncode,
            "准入理由": admission.get("理由", []),
        })

    counts = {key: sum(1 for item in scheduled if item["准入结论"] == key) for key in action_map}
    scheduler_state = load_json(manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.json", {})
    report = {
        "名称": "个人智能母系统任务队列调度面板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前调度状态": scheduler_state.get("当前状态"),
        "规则文件": str(rules_path),
        "队列种子文件": str(seed_path),
        "队列种子生成": {"返回码": seed_run.returncode, "stdout": seed_run.stdout.strip(), "stderr": seed_run.stderr.strip()},
        "任务队列": scheduled,
        "汇总": {
            "任务数量": len(scheduled),
            "允许执行": counts.get("允许执行", 0),
            "降级只读": counts.get("降级只读", 0),
            "延后执行": counts.get("延后执行", 0),
            "需要许可令": counts.get("需要许可令", 0),
            "禁止执行": counts.get("禁止执行", 0),
            "触发执行器数量": 0,
            "触发n8n数量": 0,
        },
        "安全边界": {
            "是否执行任务": False,
            "是否触发执行器": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改业务文件": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = manager / "04日志" / "个人智能母系统任务队列"
    state_dir = manager / "03数据" / "运行状态"
    json_path = log_dir / f"task-queue-scheduler-{stamp}.json"
    md_path = log_dir / f"task-queue-scheduler-{stamp}.md"
    latest_json = state_dir / "个人智能母系统任务队列调度_最新.json"
    latest_md = state_dir / "个人智能母系统任务队列调度_最新.md"
    write_json(json_path, report)
    write_text(md_path, render_md(report))
    write_json(latest_json, report)
    write_text(latest_md, render_md(report))
    print(json.dumps({"任务数量": len(scheduled), "汇总": report["汇总"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
