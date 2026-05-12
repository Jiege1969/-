# -*- coding: utf-8 -*-
"""
名称：生成个人智能母系统任务准入报告.py
作用：根据当前日常调度状态、交易保护、权限等级、任务类型和硬阻断条件，判断任务是否允许、降级、延后、需许可或禁止。
触发方式：python 生成个人智能母系统任务准入报告.py --task "任务名" --level L0只读巡检 --type 静态验收 --action "只读检查"
依赖：Python标准库；个人智能母系统任务准入规则.json；生成个人智能母系统日常调度状态.py；旧口径冲突审计报告。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统任务准入/task-admission-*.json|md；03数据/运行状态/个人智能母系统任务准入_最新.json|md。
安全边界：只读判断并写总管日志/状态；不执行任务、不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易、不修改业务文件。
标识：personal-ai-task-admission；任务准入；调度闸口；只读判断。
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


def run_py(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def contains_any(text: str, words: list[str]) -> bool:
    return any(word and word in text for word in words)


def normalize_level(level: str) -> str:
    if level.upper() in {"L0", "0"}:
        return "L0只读巡检"
    if level.upper() in {"L1", "1"}:
        return "L1低风险修复"
    if level.upper() in {"L2", "2"}:
        return "L2服务级操作"
    if level.upper() in {"L3", "3"}:
        return "L3破坏性操作"
    return level


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# 个人智能母系统任务准入报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 任务：{report['任务']}",
        f"- 当前调度状态：{report['当前调度状态']}",
        f"- 权限等级：{report['权限等级']}",
        f"- 准入结论：{report['准入结论']}",
        "",
        "## 理由",
    ]
    lines.extend([f"- {item}" for item in report.get("理由", [])])
    lines.extend(["", "## 降级或后续动作"])
    lines.extend([f"- {item}" for item in report.get("建议动作", [])])
    lines.extend(["", "## 安全边界"])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, help="任务名称。")
    parser.add_argument("--level", default="L0只读巡检", help="权限等级：L0/L1/L2/L3或完整名称。")
    parser.add_argument("--type", default="静态验收", help="任务类型，如静态验收、股票收市分析、新业务系统复制搭建。")
    parser.add_argument("--action", default="只读检查", help="拟执行动作描述。")
    parser.add_argument("--system", default="00总管", help="所属系统或业务域。")
    parser.add_argument("--now", default="", help="用于验收的指定时间，格式 YYYY-MM-DD HH:MM:SS。")
    parser.add_argument("--ignore-resource-pressure", action="store_true", help="仅用于验收，忽略当前资源压力。")
    args = parser.parse_args()

    manager = manager_root()
    rules_path = manager / "01配置" / "个人智能母系统任务准入规则.json"
    rules = load_json(rules_path, {})
    scheduler_script = manager / "02脚本" / "生成个人智能母系统日常调度状态.py"
    scheduler_args = []
    if args.now:
        scheduler_args.extend(["--now", args.now])
    if args.ignore_resource_pressure:
        scheduler_args.append("--ignore-resource-pressure")
    scheduler_run = run_py(scheduler_script, *scheduler_args)
    scheduler_state = load_json(manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.json", {})
    current_state = scheduler_state.get("当前状态") or "未知"
    level = normalize_level(args.level)
    task_text = f"{args.task} {args.type} {args.system}"
    action_text = str(args.action or "")
    reasons: list[str] = []
    suggestions: list[str] = []
    conclusion = "允许执行"

    old_state = scheduler_state.get("旧口径审计状态", {})
    if old_state.get("阻断"):
        conclusion = "禁止执行"
        reasons.append("旧口径审计高危或中危未归零。")

    hard_blocks = {
        "动作包含自动交易": ["自动交易", "自动下单", "买入", "卖出"],
        "动作包含旧系统写入": ["旧系统写入", "写旧系统"],
        "动作包含删除正式文件": ["删除正式", "删除文件"],
        "动作包含覆盖正式配置": ["覆盖正式配置", "覆盖配置"],
        "真实接入总闸门未放行却请求真实发送或真实Webhook": ["真实发送", "真实Webhook", "正式Webhook"],
    }
    for reason, words in hard_blocks.items():
        if contains_any(action_text, words):
            conclusion = "禁止执行"
            reasons.append(reason)

    if conclusion != "禁止执行" and level == "L3破坏性操作" and contains_any(task_text + " " + action_text, ["税收", "删除", "覆盖", "迁移", "旧系统"]):
        conclusion = "禁止执行"
        reasons.append("L3破坏性或暂停业务任务不得进入执行。")

    strategy = rules.get("状态准入策略", {}).get(current_state, {})
    allowed = set(strategy.get("允许", []))
    downgrade = set(strategy.get("降级", []))
    delayed = set(strategy.get("延后", []))
    need_license = set(strategy.get("需要许可", []))
    forbidden = set(strategy.get("禁止", []))

    if conclusion != "禁止执行":
        if level in forbidden or args.type in forbidden:
            conclusion = "禁止执行"
            reasons.append(f"{current_state} 状态下禁止 {level} 或 {args.type}。")
        elif level in need_license or args.type in need_license:
            conclusion = "需要许可令"
            reasons.append(f"{current_state} 状态下 {level} 或 {args.type} 需要许可令。")
        elif level in delayed or args.type in delayed:
            conclusion = "延后执行"
            reasons.append(f"{current_state} 状态下 {level} 或 {args.type} 应延后。")
        elif level in downgrade or args.type in downgrade:
            conclusion = "降级只读"
            reasons.append(f"{current_state} 状态下 {level} 或 {args.type} 只能降级处理。")
        elif level in allowed or args.type in allowed:
            conclusion = "允许执行"
            reasons.append(f"{current_state} 状态下允许 {level} 或 {args.type}。")
        else:
            conclusion = "延后执行"
            reasons.append(f"{current_state} 状态下未明确放行该任务，默认延后。")

    downgrade_paths = rules.get("默认降级路径", {})
    if conclusion == "降级只读":
        suggestions.append(downgrade_paths.get(level, "改为只读报告或影子预案。"))
    elif conclusion == "延后执行":
        suggestions.append("放入任务队列，等待日常调度状态变为允许窗口后再评估。")
    elif conclusion == "需要许可令":
        suggestions.append("生成许可令、回滚点、验收清单和执行窗口，不直接执行。")
    elif conclusion == "禁止执行":
        suggestions.append(downgrade_paths.get(level, "禁止执行，只生成风险说明和替代方案。"))
    else:
        suggestions.append("可进入对应执行器或下一层验收；本脚本不执行任务。")

    report = {
        "名称": "个人智能母系统任务准入报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务": args.task,
        "系统": args.system,
        "任务类型": args.type,
        "拟执行动作": args.action,
        "权限等级": level,
        "当前调度状态": current_state,
        "准入结论": conclusion,
        "理由": reasons,
        "建议动作": suggestions,
        "调度状态摘要": {
            "当前允许": scheduler_state.get("当前允许", []),
            "当前禁止": scheduler_state.get("当前禁止", []),
            "原因": scheduler_state.get("原因", []),
        },
        "日常调度执行": {"返回码": scheduler_run.returncode, "stdout": scheduler_run.stdout.strip(), "stderr": scheduler_run.stderr.strip()},
        "安全边界": {
            "是否执行任务": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改业务文件": False,
        },
        "规则文件": str(rules_path),
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = manager / "04日志" / "个人智能母系统任务准入"
    state_dir = manager / "03数据" / "运行状态"
    json_path = log_dir / "task-admission-最新.json"
    md_path = log_dir / "task-admission-最新.md"
    latest_json = state_dir / "个人智能母系统任务准入_最新.json"
    latest_md = state_dir / "个人智能母系统任务准入_最新.md"
    write_json(json_path, report)
    write_text(md_path, render_md(report))
    write_json(latest_json, report)
    write_text(latest_md, render_md(report))
    print(json.dumps({"准入结论": conclusion, "当前调度状态": current_state, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
