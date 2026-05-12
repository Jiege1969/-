"""
名称：生成日常任务放行预案.py
作用：根据人工确认单生成任务放行预案，明确只读计划、草稿生成或真实接入前评审边界。
触发方式：python 生成日常任务放行预案.py；验证阶段可使用 --demo。
依赖：Python 标准库；日常任务放行规则.json；日常任务人工确认单_最新.json。
所属系统：01杰哥智能系统
安全边界：只生成放行预案；不执行任务、不触发n8n、不发送企业微信、不写旧系统、不恢复税收业务。
创建/修改记录：2026-04-27 创建日常任务放行预案生成脚本。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def strategy_for(task_type: str, rules: dict[str, Any]) -> dict[str, Any]:
    for item in rules.get("任务放行策略", []):
        if item.get("任务类型") == task_type:
            return item
    return {
        "任务类型": task_type,
        "允许模式": rules.get("默认放行模式", "只读计划"),
        "预案动作": ["生成只读计划", "生成人工确认清单"],
        "禁止动作": [],
    }


def build_release_plan(confirmation: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    task_type = confirmation.get("任务类型", "普通对话")
    strategy = strategy_for(task_type, rules)
    paused = task_type in set(rules.get("暂停任务类型", []))
    high_risk = confirmation.get("风险等级") == "高"
    if paused:
        decision = "禁止放行，仅暂停登记"
    elif high_risk:
        decision = "仅允许真实接入前评审，不进入真实执行"
    else:
        decision = f"允许生成{strategy.get('允许模式')}预案"
    forbidden = list(dict.fromkeys(strategy.get("禁止动作", []) + rules.get("统一禁止动作", [])))
    return {
        "放行预案ID": f"REL-{confirmation.get('任务ID')}",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "确认单ID": confirmation.get("确认单ID"),
        "任务ID": confirmation.get("任务ID"),
        "任务类型": task_type,
        "目标系统": confirmation.get("目标系统"),
        "风险等级": confirmation.get("风险等级"),
        "允许模式": strategy.get("允许模式"),
        "放行结论": decision,
        "预案动作": strategy.get("预案动作", []),
        "禁止动作": forbidden,
        "回滚要求": [
            "真实接入前必须有回滚脚本或回滚说明",
            "真实发送、真实写入、真实抓取必须单独评审",
            "异常时先关闭入口，再保留日志，再分析原因"
        ],
        "执行开关": {
            "是否执行任务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否执行税收业务": False,
            "是否执行真实交易": False
        },
    }


def write_markdown(plans: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# 日常任务放行预案",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 预案数量：{len(plans)}",
        "",
    ]
    for plan in plans:
        lines.extend([
            f"## {plan['放行预案ID']}",
            "",
            f"- 任务ID：{plan['任务ID']}",
            f"- 任务类型：{plan['任务类型']}",
            f"- 目标系统：{plan['目标系统']}",
            f"- 风险等级：{plan['风险等级']}",
            f"- 允许模式：{plan['允许模式']}",
            f"- 放行结论：{plan['放行结论']}",
            "",
            "预案动作：",
        ])
        lines.extend(f"- {value}" for value in plan["预案动作"])
        lines.append("")
        lines.append("禁止动作：")
        lines.extend(f"- {value}" for value in plan["禁止动作"])
        lines.append("")
        lines.append("回滚要求：")
        lines.extend(f"- {value}" for value in plan["回滚要求"])
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="read temporary rehearsal confirmation sheet")
    args = parser.parse_args()
    root = system_root()
    rules = load_json(root / "01杰哥智能系统" / "01配置" / "日常任务放行规则.json")
    if args.demo:
        input_path = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "人工确认单" / "日常任务人工确认单_最新.json"
        output_dir = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "放行预案"
    else:
        input_path = root / "01杰哥智能系统" / "03数据" / "任务队列" / "02人工确认单" / "日常任务人工确认单_最新.json"
        output_dir = root / "01杰哥智能系统" / "03数据" / "任务队列" / "03放行预案"
    output_dir.mkdir(parents=True, exist_ok=True)
    confirmations = load_json(input_path) if input_path.exists() else []
    plans = [build_release_plan(item, rules) for item in confirmations]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_output = output_dir / f"日常任务放行预案_{timestamp}.json"
    latest_json = output_dir / "日常任务放行预案_最新.json"
    latest_md = output_dir / "日常任务放行预案_最新.md"
    text = json.dumps(plans, ensure_ascii=False, indent=2)
    json_output.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    write_markdown(plans, latest_md)
    print(json.dumps({"预案数量": len(plans), "输出": str(json_output)}, ensure_ascii=False))
    return 0 if plans else 1


if __name__ == "__main__":
    raise SystemExit(main())
